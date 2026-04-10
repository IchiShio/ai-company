#!/usr/bin/env python3
"""
check_questions.py - 統一品質チェッカー（WordsUp / GrammarUp / ListenUp 対応）

Claude API で意味的品質チェックを実行:
  1. 正解複数チェック: 不正解の選択肢が実は正解として成立しないか
  2. 消去法チェック: 問題文なしでも正解を絞れないか（選択肢だけで解ける問題を排除）
  3. 説明の正確性: expl の語義・用法説明が辞書的に正確か
  4. axis 整合性: axis 分類が問題内容と一致しているか

使用法:
  python3 check_questions.py --type words   [--file staging.json]
  python3 check_questions.py --type grammar [--file grammar/staging.json]
  python3 check_questions.py --type listen  [--file listening/staging.json]
  python3 check_questions.py --type words --file words/questions.js  # 既存問題の全チェック

結果: PASS/FAIL + 修正提案。FAIL の問題は staging_checked.json に修正版を出力。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: anthropic パッケージが必要です: pip install anthropic")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).parent
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────
# Quiz type definitions
# ─────────────────────────────────────────
QUIZ_TYPES = {
    "words": {
        "axes": ["meaning", "phrase", "idiom", "nuance", "context"],
        "num_choices": 4,
        "question_key": "text",
        "answer_key": "answer",
        "staging_default": "words/staging.json",
    },
    "grammar": {
        "axes": ["form", "vocab", "logic", "tense", "trap"],
        "num_choices": 5,
        "question_key": "stem",
        "answer_key": "answer",
        "staging_default": "grammar/staging.json",
    },
    "listen": {
        "axes": ["speed", "reduction", "vocab", "context", "distractor"],
        "num_choices": 5,
        "question_key": "text",
        "answer_key": "answer",
        "staging_default": "listening/staging.json",
    },
}


def load_questions(filepath, quiz_type):
    """JSONまたはquestions.jsから問題を読み込む"""
    content = Path(filepath).read_text(encoding="utf-8").strip()

    if filepath.endswith(".js"):
        # questions.js 形式: const DATA = [...];
        # コメント行を除去
        lines = [line for line in content.split('\n') if not line.strip().startswith('//')]
        content_no_comments = '\n'.join(lines)
        match = re.search(r'\[.*\]', content_no_comments, re.DOTALL)
        if not match:
            print(f"ERROR: {filepath} からデータを抽出できません")
            sys.exit(1)
        js_data = match.group(0)
        # JS object key: value -> "key": value (キーにクォートがない場合)
        js_data = re.sub(r'(?<=[{,\s])(\w+)\s*:', r'"\1":', js_data)
        # trailing commas
        js_data = re.sub(r',\s*([\]}])', r'\1', js_data)
        try:
            questions = json.loads(js_data)
        except json.JSONDecodeError as e:
            # デバッグ: エラー位置の前後を表示
            pos = e.pos if hasattr(e, 'pos') else 0
            snippet = js_data[max(0, pos-80):pos+80]
            print(f"ERROR: {filepath} の JSON パースに失敗 (pos={pos})")
            print(f"  付近: ...{snippet}...")
            sys.exit(1)
    else:
        try:
            questions = json.loads(content)
        except json.JSONDecodeError:
            print(f"ERROR: {filepath} の JSON パースに失敗")
            sys.exit(1)

    print(f"{len(questions)} 問を読み込みました ({filepath})")
    return questions


def build_check_prompt(questions, quiz_type):
    """品質チェック用のプロンプトを構築"""
    cfg = QUIZ_TYPES[quiz_type]
    q_key = cfg["question_key"]

    q_json = json.dumps(questions, ensure_ascii=False, indent=2)

    prompt = f"""あなたは英語教育コンテンツの品質検査官です。以下の {quiz_type} クイズ問題を4つの観点で厳密にチェックしてください。

## チェック項目

### 1. 正解複数チェック (multi_answer)
不正解の選択肢の中に、実は正解としても成立するものがないか確認。
- 語彙問題: 同義語・類義語が不正解に含まれていないか
- 文法問題: 別の文法解釈で正解になる選択肢がないか
- 厳格基準: 「意味が近い」「場合によっては正解」もFAIL

### 2. 消去法チェック (elimination)
問題文（{q_key}）を見ずに選択肢だけで正解を絞れないか。
- 不正解が明らかに場違い（カテゴリ違い、トーン違い）
- 正解だけが「まとも」で他が冗談のような選択肢
- 4択中3択が同じ方向を向いていて1つだけ違う（その1つが正解）

### 3. 説明の正確性 (accuracy)
expl フィールドの語義・用法・語源説明が辞書的に正確か。
- 誤った語源や語義
- 不正確なニュアンス説明
- 誤った文法規則の引用

### 4. axis 整合性 (axis_match)
問題の axis 分類が内容と一致しているか。
有効な axis: {cfg["axes"]}

## 出力形式

各問題について以下のJSON形式で結果を返してください。全問題分をリストで返すこと。

```json
[
  {{
    "index": 0,
    "word": "(問題の識別子)",
    "status": "PASS" or "FAIL",
    "issues": [
      {{
        "check": "multi_answer|elimination|accuracy|axis_match",
        "severity": "FAIL|WARN",
        "detail": "具体的な問題点",
        "fix": "修正提案（あれば）"
      }}
    ]
  }}
]
```

- status が "PASS" なら issues は空配列
- severity "FAIL" = 必ず修正が必要、"WARN" = 改善推奨
- FAIL が1つでもあれば status は "FAIL"

重要: JSONのみ出力してください。マークダウンのコードブロック記号（```）や説明文は不要です。配列 [ ... ] だけを出力してください。

## チェック対象の問題

{q_json}
"""
    return prompt


def run_check(questions, quiz_type, batch_size=15):
    """Claude API でチェック実行"""
    all_results = []

    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        print(f"\nチェック中: {i + 1}〜{i + len(batch)} 問目...")

        prompt = build_check_prompt(batch, quiz_type)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # JSON 部分を抽出
        raw = re.sub(r'^```[a-z]*\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw.strip())

        try:
            results = json.loads(raw)
        except json.JSONDecodeError:
            # JSON抽出を試行
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                try:
                    results = json.loads(match.group(0))
                except json.JSONDecodeError:
                    print(f"  WARNING: バッチ {i // batch_size + 1} のパースに失敗。スキップ。")
                    continue
            else:
                print(f"  WARNING: バッチ {i // batch_size + 1} のパースに失敗。スキップ。")
                continue

        # インデックスをグローバルに補正
        for r in results:
            r["index"] = r.get("index", 0) + i

        all_results.extend(results)

    return all_results


def print_report(results, questions, quiz_type):
    """チェック結果のレポートを表示"""
    cfg = QUIZ_TYPES[quiz_type]
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"  品質チェック結果: {quiz_type.upper()}")
    print("=" * 60)
    print(f"  総問題数: {total}")
    print(f"  PASS: {passed}")
    print(f"  FAIL: {failed}")
    print("=" * 60)

    if failed == 0:
        print("\n  全問題 PASS! デプロイ可能です。")
        return True

    print(f"\n  FAIL: {failed} 問に問題あり\n")
    for r in results:
        if r.get("status") != "FAIL":
            continue
        idx = r.get("index", "?")
        word = r.get("word", "?")
        print(f"  [{idx}] {word}")
        for issue in r.get("issues", []):
            sev = issue.get("severity", "?")
            chk = issue.get("check", "?")
            detail = issue.get("detail", "")
            fix = issue.get("fix", "")
            marker = "FAIL" if sev == "FAIL" else "WARN"
            print(f"    [{marker}] {chk}: {detail}")
            if fix:
                print(f"          -> 修正案: {fix}")
        print()

    return False


def main():
    parser = argparse.ArgumentParser(description="統一品質チェッカー")
    parser.add_argument("--type", required=True, choices=["words", "grammar", "listen"],
                        help="クイズの種類")
    parser.add_argument("--file", help="チェック対象のファイルパス（デフォルト: staging.json）")
    parser.add_argument("--batch-size", type=int, default=15,
                        help="1回のAPI呼び出しで処理する問題数（デフォルト: 15）")
    parser.add_argument("--dry-run", action="store_true",
                        help="最初の5問だけチェック")
    args = parser.parse_args()

    cfg = QUIZ_TYPES[args.type]
    filepath = args.file or str(REPO_ROOT / cfg["staging_default"])

    if not Path(filepath).exists():
        print(f"ERROR: ファイルが見つかりません: {filepath}")
        sys.exit(1)

    questions = load_questions(filepath, args.type)

    if args.dry_run:
        questions = questions[:5]
        print(f"dry-run モード: 最初の {len(questions)} 問のみチェック")

    if not questions:
        print("チェック対象の問題がありません。")
        sys.exit(0)

    results = run_check(questions, args.type, args.batch_size)
    ok = print_report(results, questions, args.type)

    # FAILした問題のインデックスを出力
    if not ok:
        fail_indices = [r["index"] for r in results if r.get("status") == "FAIL"]
        print(f"  FAIL インデックス: {fail_indices}")

        # 結果をJSONに保存
        output_path = REPO_ROOT / f"check_result_{args.type}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  詳細結果: {output_path}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
