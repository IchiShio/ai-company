#!/usr/bin/env python3
"""
batch_words.py - WordsUp 問題を目標数まで自動バッチ生成・チェック・追加

使用法:
  python3 batch_words.py --target 5000
  python3 batch_words.py --target 5000 --batch-size 200
  python3 batch_words.py --target 5000 --skip-check  # チェックスキップ（非推奨）

処理フロー（1バッチごと）:
  1. generate_words.py で問題生成 → staging.json
  2. check_questions.py で品質チェック
  3. FAILした問題を除外
  4. add_words.py で MP3生成 → questions.js追記 → git push
  5. 目標数に到達するまで繰り返し
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "words" / "questions.js"
STAGING_JSON = REPO_ROOT / "words" / "staging.json"
CHECK_RESULT = REPO_ROOT / "check_result_words.json"
LOG_FILE = REPO_ROOT / "batch_words.log"


def get_current_count():
    """questions.js の現在の問題数を取得"""
    if not QUESTIONS_JS.exists():
        return 0
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    return len(re.findall(r'\bword:', content))


def log(msg):
    """コンソールとログファイルに出力"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_generate(count, model="claude-sonnet-4-6"):
    """問題生成"""
    log(f"生成開始: {count}問")
    result = subprocess.run(
        ["python3", "generate_words.py", "--count", str(count), "--model", model],
        cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        log(f"生成エラー: {result.stderr[:500]}")
        return False
    log(f"生成完了")
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return True


def run_check():
    """品質チェック"""
    log("品質チェック開始...")
    result = subprocess.run(
        ["python3", "check_questions.py", "--type", "words"],
        cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=600,
    )
    print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)

    if result.returncode == 0:
        log("全問 PASS")
        return True

    # FAILした問題を除外
    log("FAILした問題を除外中...")
    if not CHECK_RESULT.exists():
        log("WARNING: check_result_words.json が見つかりません。全問維持します。")
        return True

    check_results = json.loads(CHECK_RESULT.read_text(encoding="utf-8"))
    # severity=FAIL の issue がある問題のみ除外（WARNのみは保持）
    fail_indices = set()
    for r in check_results:
        has_critical = any(
            issue.get("severity") == "FAIL"
            for issue in r.get("issues", [])
        )
        if has_critical:
            fail_indices.add(r["index"])

    if not fail_indices:
        return True

    staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    original_count = len(staging)
    staging = [q for i, q in enumerate(staging) if i not in fail_indices]
    removed = original_count - len(staging)
    log(f"  {removed}問を除外（{len(staging)}問残り）")

    STAGING_JSON.write_text(json.dumps(staging, ensure_ascii=False, indent=2), encoding="utf-8")

    if not staging:
        log("WARNING: 全問FAILのため、このバッチはスキップ")
        return False

    return True


def run_add():
    """MP3生成 + questions.js追記 + git push"""
    log("add_words.py 実行中...")
    result = subprocess.run(
        ["python3", "add_words.py"],
        cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=1800,  # 音声生成に時間がかかる
    )
    if result.returncode != 0:
        log(f"add_words.py エラー: {result.stderr[:500]}")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return False
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    log("add_words.py 完了")
    return True


def main():
    parser = argparse.ArgumentParser(description="WordsUp バッチ生成パイプライン")
    parser.add_argument("--target", type=int, default=5000, help="目標問題数（デフォルト: 5000）")
    parser.add_argument("--batch-size", type=int, default=200, help="1バッチの生成数（デフォルト: 200）")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="生成モデル")
    parser.add_argument("--skip-check", action="store_true", help="品質チェックをスキップ（非推奨）")
    args = parser.parse_args()

    current = get_current_count()
    remaining = args.target - current
    log(f"現在: {current}問 → 目標: {args.target}問 → 残り: {remaining}問")

    if remaining <= 0:
        log("既に目標数に達しています。")
        return

    batch_num = 0
    while True:
        current = get_current_count()
        remaining = args.target - current
        if remaining <= 0:
            log(f"目標達成! 現在 {current} 問")
            break

        batch_num += 1
        batch_count = min(args.batch_size, remaining)
        log(f"\n{'='*60}")
        log(f"バッチ {batch_num}: {batch_count}問生成 (現在{current}問 / 目標{args.target}問)")
        log(f"{'='*60}")

        # 1. 生成
        if not run_generate(batch_count, args.model):
            log("生成に失敗。10秒待って再試行...")
            time.sleep(10)
            continue

        # 2. チェック
        if not args.skip_check:
            check_ok = run_check()
            if not check_ok:
                log("全問FAIL。次のバッチへ...")
                continue

        # 3. 追加（MP3 + questions.js + git push）
        if not run_add():
            log("追加に失敗。中断します。")
            break

        current_after = get_current_count()
        log(f"バッチ {batch_num} 完了: {current} → {current_after} 問")

        # API レートリミット対策
        time.sleep(5)

    final = get_current_count()
    log(f"\n完了! 最終問題数: {final}")


if __name__ == "__main__":
    main()
