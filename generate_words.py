#!/usr/bin/env python3
"""
generate_words.py - Claude API で語彙問題を生成 → words/staging.json に保存

使用法:
  python3 generate_words.py --count 100
  python3 generate_words.py --count 50 --axis-only idiom,phrase
  python3 generate_words.py --count 10 --dry-run  # プロンプト確認のみ

生成後のフロー:
  1. python3 check_questions.py --type words  # 品質チェック（必須）
  2. python3 add_words.py                     # MP3生成 → questions.js追記 → git push
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic がインストールされていません: pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from lib import WORDS_VALID_FIELDS, VALID_AXES_WORDS, VALID_DIFFS, parse_words_response

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "words" / "questions.js"
STAGING_JSON = REPO_ROOT / "words" / "staging.json"

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
BATCH_SIZE = 25
EXCLUDE_LIMIT = 5500

AXIS_DESCRIPTIONS = {
    "meaning":  "meaning : 基本的な英単語の語義を問う（grateful=感謝している、reluctant=気が進まない 等）",
    "phrase":   "phrase  : 句動詞・フレーズの意味を問う（figure out=解明する、put off=延期する 等）",
    "idiom":    "idiom   : イディオム・慣用表現の意味を問う（break the ice=場を和ませる、cut corners=手を抜く 等）",
    "nuance":   "nuance  : 似た単語の使い分け・ニュアンスの違いを問う（affect/effect、borrow/lend 等）",
    "context":  "context : 文脈によって意味が変わる多義語の正しい意味を問う（address=対処する、sound=堅実な 等）",
}


def load_existing_words():
    """既存問題のword+textリストを取得（重複防止用）"""
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    words = re.findall(r'\bword:\s*"((?:[^"\\]|\\.)*)"', content)
    if len(words) > EXCLUDE_LIMIT:
        words = words[-EXCLUDE_LIMIT:]
    return words


def build_prompt(count, lv_counts, existing_words, axis_only=None):
    existing_list = json.dumps(existing_words, ensure_ascii=False)

    if axis_only:
        per = count // len(axis_only)
        axis_lines = "\n".join(f"- {AXIS_DESCRIPTIONS[a]}" for a in axis_only)
        axis_instruction = (
            f"各問題に以下の axis のいずれかを割り当て、均等に分散させること（各約{per}問）：\n{axis_lines}"
        )
    else:
        per = count // 5
        axis_lines = "\n".join(f"- {d}" for d in AXIS_DESCRIPTIONS.values())
        axis_instruction = (
            f"各問題に以下のいずれかを1つ割り当て、均等に分散させること（各約{per}問）：\n{axis_lines}"
        )

    return f"""以下のJSON形式で英単語・語彙クイズの問題を{count}問生成してください。

## 難易度の内訳
- lv1（基礎語彙・高校レベル）: {lv_counts[0]}問
- lv2（中級語彙・TOEIC600レベル）: {lv_counts[1]}問
- lv3（中上級語彙・TOEIC800レベル）: {lv_counts[2]}問
- lv4（上級語彙・英検準1級レベル）: {lv_counts[3]}問
- lv5（最上級語彙・英検1級レベル）: {lv_counts[4]}問

## 語彙カテゴリ（axis）
{axis_instruction}

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5のいずれか",
    "axis": "meaning | phrase | idiom | nuance | context のいずれか",
    "word": "出題対象の単語・フレーズ",
    "text": "その単語を含む自然な英文（1〜2文）",
    "ja": "英文の日本語訳",
    "answer": "choices[0] と完全に同じ文字列",
    "choices": ["正解の日本語訳（10〜20字）", "紛らわしい誤答1", "紛らわしい誤答2", "紛らわしい誤答3"],
    "expl": "なぜそのような意味になるのかの解説（1〜2文、語法・用例含む）"
  }}
]

## 重要な制約

### 正解の一意性（最重要）
- **正解は必ず1つだけ**。不正解の選択肢が正解としても成立してはならない
- 同義語・類義語を不正解に入れてはならない（例: answer="感謝している" なら "ありがたく思う" は不正解に使えない）
- 各選択肢は意味的に明確に異なること

### 消去法の防止
- 問題文（text）を読まなくても選択肢だけで正解がわかってはならない
- 不正解は全て「その単語の意味としてありえそう」な選択肢にすること
- 正解だけ日本語のトーンが違う、長さが違う等の手がかりを与えない

### 品質基準
- text はネイティブが実際に使う自然な英文
- word は text 中に必ず含まれること
- answer は必ず choices[0] と完全一致（システムが文字列一致で判定）
- expl は辞書的に正確な説明のみ記載（推測・ハルシネーション厳禁）
- axis の特性を問題内容に正しく反映すること

### 重複禁止
以下の単語・フレーズは既出のため使わないこと：
{existing_list}
"""


def run_generation(count, model, axis_only=None):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    existing = load_existing_words()
    print(f"既存問題: {len(existing)} 語")

    # 難易度配分: 25% / 30% / 25% / 15% / 5%
    lv_total = [
        round(count * 0.25),
        round(count * 0.30),
        round(count * 0.25),
        round(count * 0.15),
        max(1, round(count * 0.05)),
    ]
    diff = count - sum(lv_total)
    lv_total[2] += diff  # 端数はlv3に

    all_questions = []
    remaining = count

    while remaining > 0:
        batch = min(BATCH_SIZE, remaining)
        # バッチ内の難易度配分
        ratio = batch / count
        lv_batch = [max(0, round(l * ratio)) for l in lv_total]
        diff = batch - sum(lv_batch)
        lv_batch[2] = max(0, lv_batch[2] + diff)

        prompt = build_prompt(batch, lv_batch, existing + [q.get("word", "") for q in all_questions], axis_only)

        print(f"\n生成中: {batch} 問 (モデル: {model})...")
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text
        questions = parse_words_response(raw, raise_on_error=False)

        if not questions:
            print(f"  WARNING: パースに失敗。リトライします。")
            continue

        print(f"  {len(questions)} 問取得")
        all_questions.extend(questions)
        remaining -= len(questions)

    return all_questions


def main():
    parser = argparse.ArgumentParser(description="WordsUp 問題生成")
    parser.add_argument("--count", type=int, default=100, help="生成する問題数（デフォルト: 100）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"モデル名（デフォルト: {DEFAULT_MODEL}）")
    parser.add_argument("--axis-only", help="特定axisのみ生成（カンマ区切り。例: idiom,phrase）")
    parser.add_argument("--dry-run", action="store_true", help="プロンプトを表示するだけ")
    args = parser.parse_args()

    axis_only = None
    if args.axis_only:
        axis_only = [a.strip() for a in args.axis_only.split(",")]
        invalid = [a for a in axis_only if a not in VALID_AXES_WORDS]
        if invalid:
            print(f"ERROR: 無効な axis: {invalid}")
            print(f"  有効な値: {sorted(VALID_AXES_WORDS)}")
            sys.exit(1)

    if args.dry_run:
        existing = load_existing_words()
        lv = [round(args.count * r) for r in [0.25, 0.30, 0.25, 0.15, 0.05]]
        prompt = build_prompt(args.count, lv, existing, axis_only)
        print(prompt)
        return

    questions = run_generation(args.count, args.model, axis_only)

    # staging.json に保存
    STAGING_JSON.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(questions)} 問を {STAGING_JSON} に保存しました")
    print(f"\n次のステップ:")
    print(f"  1. python3 check_questions.py --type words          # 品質チェック（必須）")
    print(f"  2. python3 add_words.py                             # MP3生成 → 追加 → push")


if __name__ == "__main__":
    main()
