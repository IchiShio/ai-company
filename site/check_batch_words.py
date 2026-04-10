#!/usr/bin/env python3
"""
check_batch_words.py - WordsUp Batch API 結果を取得 → 品質チェック → 音声生成 → push

使用法:
  python3 check_batch_words.py             # 結果取得 + チェック + 追加
  python3 check_batch_words.py --status    # 状態確認のみ
  python3 check_batch_words.py --no-check  # チェックスキップ（テスト用）

処理フロー:
  1. Batch API 結果取得 → words/staging.json に保存
  2. Haiku でサンプリング品質チェック（20%抽出、severity=FAILのみ除外）
  3. add_words.py で MP3生成 → questions.js追記 → git push
"""

import argparse
import json
import os
import random
import re
import subprocess
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

from lib import parse_words_response

REPO_ROOT = Path(__file__).parent
STAGING_JSON = REPO_ROOT / "words" / "staging.json"
BATCH_STATE = REPO_ROOT / "words" / "batch_state.json"

CHECK_MODEL = "claude-haiku-4-5-20251001"
SAMPLE_RATE = 0.20  # 20%サンプリング
CHECK_BATCH_SIZE = 20


def deduplicate(questions):
    """word フィールドで重複を除去"""
    seen = set()
    unique = []
    for q in questions:
        w = q.get("word", "").strip().lower()
        if w not in seen:
            seen.add(w)
            unique.append(q)
    return unique


def check_sample(questions, client):
    """Haikuでサンプリング品質チェック。severity=FAILの問題インデックスを返す"""
    sample_size = max(10, int(len(questions) * SAMPLE_RATE))
    sample_indices = sorted(random.sample(range(len(questions)), min(sample_size, len(questions))))
    sample = [questions[i] for i in sample_indices]

    print(f"\n品質チェック: {len(sample)}問をサンプリング（全{len(questions)}問の{len(sample)*100//len(questions)}%）")
    print(f"  モデル: {CHECK_MODEL}")

    fail_words = set()  # FAILしたwordを収集
    all_fail_indices = set()

    for batch_start in range(0, len(sample), CHECK_BATCH_SIZE):
        batch = sample[batch_start:batch_start + CHECK_BATCH_SIZE]
        batch_indices = sample_indices[batch_start:batch_start + CHECK_BATCH_SIZE]

        q_json = json.dumps(batch, ensure_ascii=False, indent=2)
        prompt = f"""あなたは英語教育コンテンツの品質検査官です。以下の語彙クイズ問題を厳密にチェックしてください。

## チェック項目
1. **multi_answer**: 不正解選択肢に実は正解として成立するものがないか（同義語・類義語チェック）
2. **elimination**: 問題文なしで選択肢だけから正解を特定できないか
3. **accuracy**: expl の語義・用法説明が辞書的に正確か
4. **axis_match**: axis 分類が問題内容と一致しているか

## 出力形式（JSONのみ）
[
  {{
    "index": 0,
    "word": "(問題のword)",
    "status": "PASS" or "FAIL",
    "issues": [
      {{
        "check": "multi_answer|elimination|accuracy|axis_match",
        "severity": "FAIL|WARN",
        "detail": "具体的な問題点"
      }}
    ]
  }}
]

severity "FAIL" = 必ず修正が必要、"WARN" = 改善推奨だが問題として機能する
FAIL が1つでもあれば status = "FAIL"。JSONのみ出力。

## チェック対象
{q_json}"""

        try:
            resp = client.messages.create(
                model=CHECK_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw.strip())

            results = json.loads(raw)

            for r in results:
                has_critical = any(
                    issue.get("severity") == "FAIL"
                    for issue in r.get("issues", [])
                )
                if has_critical:
                    idx_in_batch = r.get("index", 0)
                    if idx_in_batch < len(batch_indices):
                        global_idx = batch_indices[idx_in_batch]
                        all_fail_indices.add(global_idx)
                        fail_words.add(batch[idx_in_batch].get("word", "?"))

            batch_fails = sum(1 for r in results if r.get("status") == "FAIL")
            print(f"  チェック {batch_start+1}〜{batch_start+len(batch)}: "
                  f"PASS={len(batch)-batch_fails} FAIL={batch_fails}")

        except (json.JSONDecodeError, Exception) as e:
            print(f"  WARNING: チェックバッチ {batch_start//CHECK_BATCH_SIZE+1} でエラー: {e}")
            continue

    # サンプルのFAIL率から全体のFAIL数を推定し、サンプル外も確率的に除外
    sample_fail_rate = len(all_fail_indices) / len(sample) if sample else 0
    print(f"\nサンプルFAIL率: {sample_fail_rate*100:.1f}% ({len(all_fail_indices)}/{len(sample)})")

    if fail_words:
        print(f"  FAILした単語: {', '.join(sorted(fail_words)[:20])}")

    # サンプルでFAILした問題のみ除外（サンプル外はそのまま通す）
    return all_fail_indices


def main():
    parser = argparse.ArgumentParser(description="WordsUp Batch API 結果取得・品質チェック・追加")
    parser.add_argument("--status", action="store_true", help="状態確認のみ")
    parser.add_argument("--no-check", action="store_true", help="品質チェックをスキップ")
    parser.add_argument("--no-add", action="store_true", help="staging.jsonに保存のみ（add_words.pyを実行しない）")
    args = parser.parse_args()

    if not BATCH_STATE.exists():
        print("未処理の Batch ジョブがありません")
        print("先に python3 generate_words.py --batch を実行してください")
        sys.exit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    state = json.loads(BATCH_STATE.read_text())
    batch_id = state["batch_id"]

    print(f"Batch ID: {batch_id}")
    print(f"投入日時: {state.get('submitted_at', '不明')}")
    print(f"予定問題数: {state['count']} 問")
    print(f"リクエスト数: {state.get('num_requests', '不明')} 件")

    client = anthropic.Anthropic(api_key=api_key)

    # ステータス確認
    batch = client.messages.batches.retrieve(batch_id)
    status = batch.processing_status

    counts = batch.request_counts
    total = counts.succeeded + counts.errored + counts.canceled + counts.expired
    print(f"\n処理状況: {status}")
    print(f"  成功: {counts.succeeded} / {total} 件")
    if counts.errored:
        print(f"  エラー: {counts.errored} 件")

    if status != "ended":
        print("\nまだ処理中です。しばらく待ってから再度実行してください。")
        sys.exit(0)

    if args.status:
        return

    # 結果取得
    print("\n結果を取得中...")
    all_questions = []
    error_count = 0

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            raw = result.result.message.content[0].text
            questions = parse_words_response(raw, raise_on_error=False)
            all_questions.extend(questions)
            print(f"  {result.custom_id}: {len(questions)} 問取得")
        else:
            error_count += 1
            print(f"  {result.custom_id}: ERROR ({result.result.type})")

    if error_count:
        print(f"\nWARNING: {error_count} 件のリクエストが失敗")

    if not all_questions:
        print("ERROR: 有効な問題を取得できませんでした")
        sys.exit(1)

    # 重複除去
    before = len(all_questions)
    all_questions = deduplicate(all_questions)
    removed = before - len(all_questions)
    if removed:
        print(f"\n重複除去: {removed} 問（{before} → {len(all_questions)} 問）")

    # 品質チェック（Haikuサンプリング）
    if not args.no_check:
        fail_indices = check_sample(all_questions, client)
        if fail_indices:
            before_check = len(all_questions)
            all_questions = [q for i, q in enumerate(all_questions) if i not in fail_indices]
            print(f"  除外: {before_check - len(all_questions)} 問 → 残り: {len(all_questions)} 問")

    # staging.json に保存
    STAGING_JSON.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{len(all_questions)} 問を words/staging.json に保存しました")

    # batch_state.json を削除
    BATCH_STATE.unlink()
    print("batch_state.json を削除しました")

    if args.no_add:
        print("\n--no-add が指定されたため、add_words.py はスキップします")
        print("次のステップ:")
        print("  python3 add_words.py")
        return

    # add_words.py を自動実行
    print("\nadd_words.py を実行します...")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "add_words.py")],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("ERROR: add_words.py が失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
