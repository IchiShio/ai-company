#!/usr/bin/env python3
"""
readup_pipeline.py — ReadUp 記事自動生成パイプライン

VOA最新記事を Gemma4 で4段階リライト → factcheck → QC → stories.js 追記 → git push

フロー:
  1. [generate]   VOA取得 → Gemma4でvl2000/3000/5000/7000の4レベル書き直し
                  staging.json に保存（stories.jsはまだ更新しない）
  2. [factcheck]  Claude Code で事実・翻訳・問題の正確性チェック → staging.json 修正
  3. [qc]         Claude Code でフォーマット・整合性チェック → stories.js追記 + git push

使い方:
  python3 readup_pipeline.py              # 最新1本
  python3 readup_pipeline.py --count 3   # 最新3本
  python3 readup_pipeline.py --dry-run   # デプロイしない
  python3 readup_pipeline.py --step generate   # ステップ個別実行
  python3 readup_pipeline.py --step factcheck
  python3 readup_pipeline.py --step qc
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
AICOMP_DIR  = BASE_DIR.parent / "ai-company"
GEN_SCRIPT  = AICOMP_DIR / "generate_series_ollama.py"
STAGING_JSON = AICOMP_DIR / "reading" / "series" / "staging.json"
TODAY       = date.today().isoformat()

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def log(msg: str, color: str = CYAN):
    print(f"{color}{msg}{RESET}")


def check_ollama():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return True
    except Exception:
        return False


def run_claude(prompt: str, label: str, timeout: int = 360) -> bool:
    """claude -p でプロンプトを実行。成功なら True を返す"""
    cmd = [
        "claude", "-p", prompt,
        "--allowedTools", "Read,Edit,Write",
        "--dangerously-skip-permissions",
        "--system-prompt", "You are a ReadUp content QC assistant. Check and fix English learning article content.",
    ]
    log(f"  claude -p 実行中: {label} ... （1〜2分）")
    try:
        result = subprocess.run(
            cmd, cwd=AICOMP_DIR, capture_output=False, text=True, timeout=timeout
        )
        if result.returncode != 0:
            log(f"  ❌ claude -p 失敗 (exit {result.returncode})", RED)
            return False
        return True
    except subprocess.TimeoutExpired:
        log(f"  ❌ claude -p タイムアウト ({timeout}s)", RED)
        return False


def step_generate(count: int, model: str):
    """Step 1: VOA取得 → Gemma4でリライト → staging.json に保存"""
    log(f"\n{'─'*60}")
    log(f"  Step 1 / VOA取得 → Gemma4 リライト ({count}本 × 4レベル)", BOLD + CYAN)
    log(f"{'─'*60}")

    # --dry-run: stories.js は更新しない（staging.json のみ保存）
    cmd = [
        "python3", str(GEN_SCRIPT),
        "--count", str(count),
        "--model", model,
        "--dry-run",   # staging.jsonに保存、stories.jsは更新しない
    ]
    log(f"  generate_series_ollama.py 実行中 ... （数分かかります）")
    result = subprocess.run(cmd, cwd=AICOMP_DIR)
    if result.returncode != 0:
        log(f"  ❌ 生成スクリプト失敗 (exit {result.returncode})", RED)
        sys.exit(1)

    if not STAGING_JSON.exists():
        log(f"  ❌ staging.json が生成されませんでした", RED)
        sys.exit(1)

    staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    log(f"  ✅ 生成完了: {len(staging)} ストーリーを staging.json に保存", GREEN)


def step_factcheck():
    """Step 2: staging.json の事実・翻訳・問題精度をチェックして修正"""
    log(f"\n{'─'*60}")
    log(f"  Step 2 / Factcheck（事実・翻訳・問題精度）", BOLD + CYAN)
    log(f"{'─'*60}")

    if not STAGING_JSON.exists():
        log(f"  ❌ staging.json がありません。先に generate を実行してください", RED)
        sys.exit(1)

    staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    if not staging:
        log(f"  ⚠️  staging.json が空です", YELLOW)
        return

    staging_path = str(STAGING_JSON)

    prompt = f"""
ReadUp の英語学習記事のファクトチェックを行ってください。

staging.json のパス: {staging_path}

チェック項目（各ストーリーについて）:
1. **事実確認**: body（英文）と body_ja（和訳）の内容が一致しているか
2. **VLレベルの一貫性**:
   - vl2000: 中学レベルの語彙・短文（80-100語）
   - vl3000: 高校基礎レベル（100-120語）
   - vl5000: 高校上級レベル（120-140語）
   - vl7000: 大学受験・TOEIC600レベル（130-150語）
3. **クイズの正確性**:
   - answerのインデックスが本文の内容と一致しているか
   - expl（解説）が answer に対応した説明になっているか
   - choices に明らかな誤りや重複がないか
4. **和訳の自然さ**: body_ja が不自然でないか（機械翻訳的すぎないか）

問題が見つかった場合は {staging_path} を直接編集して修正してください。
修正不要な場合もファイルは変更せずそのままでOKです。

最後に各ストーリーのチェック結果を簡潔に報告してください（OK / 修正済み）。
"""
    ok = run_claude(prompt, "ReadUp factcheck")
    if ok:
        log(f"  ✅ Factcheck 完了", GREEN)
    else:
        log(f"  ⚠️  Factcheck に問題がありました（手動確認推奨）", YELLOW)


def step_qc(dry_run: bool, model: str):
    """Step 3: フォーマット・整合性チェック → stories.js 追記 + git push"""
    log(f"\n{'─'*60}")
    log(f"  Step 3 / QC + Deploy", BOLD + CYAN)
    log(f"{'─'*60}")

    if not STAGING_JSON.exists():
        log(f"  ❌ staging.json がありません", RED)
        sys.exit(1)

    staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    if not staging:
        log(f"  ⚠️  staging.json が空です", YELLOW)
        return

    staging_path = str(STAGING_JSON)
    stories_js = str(AICOMP_DIR / "reading" / "series" / "stories.js")

    prompt = f"""
ReadUp の staging.json に保存された記事データのフォーマット QC を行ってください。

staging.json のパス: {staging_path}

チェック項目:
1. **必須フィールド確認**: 各ストーリーに id, vl, week, pub_date, source_url, source_title, title, title_ja, body, body_ja, questions が存在するか
2. **4レベルセット**: 同じ week/記事番号に vl2000/vl3000/vl5000/vl7000 の4つが揃っているか
3. **questions 形式**:
   - 各ストーリーに2問あるか
   - axis が "detail" または "main_idea" であるか
   - choices が4つあるか
   - answer が 0〜3 の整数で choices の範囲内か
   - expl が空でないか
4. **空フィールド**: title, title_ja, body, body_ja が空でないか

問題があれば {staging_path} を修正してください。
すべてOKなら修正不要です。

修正完了後、チェック結果を報告してください。
"""
    ok = run_claude(prompt, "ReadUp QC")
    if not ok:
        log(f"  ⚠️  QC に問題がありました。staging.json を確認してください", YELLOW)
        sys.exit(1)

    log(f"  ✅ QC 完了", GREEN)

    if dry_run:
        log(f"\n  [dry-run] デプロイをスキップしました", YELLOW)
        log(f"  staging.json を確認してください: {staging_path}", YELLOW)
        return

    # --resume で stories.js に追記 + git push
    log(f"\n  stories.js 追記 + git push ...", CYAN)
    cmd = [
        "python3", str(GEN_SCRIPT),
        "--resume",
        "--model", model,
    ]
    result = subprocess.run(cmd, cwd=AICOMP_DIR)
    if result.returncode != 0:
        log(f"  ❌ deploy 失敗 (exit {result.returncode})", RED)
        sys.exit(1)

    log(f"  ✅ デプロイ完了 → native-real.com/reading/", GREEN)


def main():
    parser = argparse.ArgumentParser(description="ReadUp 記事自動生成 (VOA → Gemma4 → factcheck → QC → deploy)")
    parser.add_argument("--count",   type=int, default=1, help="生成記事数 (default: 1)")
    parser.add_argument("--model",   default="gemma4:latest", help="Ollamaモデル (default: gemma4:latest)")
    parser.add_argument("--dry-run", action="store_true", help="デプロイしない")
    parser.add_argument("--step",    choices=["generate", "factcheck", "qc"],
                        help="特定ステップのみ実行")
    args = parser.parse_args()

    log(f"\n{'═'*60}", BOLD)
    log(f"  ReadUp Pipeline  —  {TODAY}", BOLD)
    log(f"  VOA → Gemma4 ({args.model}) → factcheck → QC → native-real.com", BOLD)
    log(f"{'═'*60}")

    # Ollama チェック（generate ステップが必要な場合）
    if not args.step or args.step == "generate":
        log(f"\n  Ollama 起動確認 ...", CYAN)
        if not check_ollama():
            log(f"  ❌ Ollama が起動していません", RED)
            log(f"     → ollama serve を先に実行してください", YELLOW)
            sys.exit(1)
        log(f"  ✅ Ollama: OK", GREEN)

    # generate_series_ollama.py の存在確認
    if not GEN_SCRIPT.exists():
        log(f"  ❌ {GEN_SCRIPT} が見つかりません", RED)
        sys.exit(1)

    # git pull（最新に合わせる）
    log(f"\n  git pull ...", CYAN)
    subprocess.run(["git", "pull", "origin", "main", "--quiet"],
                   cwd=AICOMP_DIR, check=False)

    if args.step == "generate":
        step_generate(args.count, args.model)
    elif args.step == "factcheck":
        step_factcheck()
    elif args.step == "qc":
        step_qc(args.dry_run, args.model)
    else:
        # フル実行
        step_generate(args.count, args.model)
        step_factcheck()
        step_qc(args.dry_run, args.model)

    log(f"\n{'═'*60}", GREEN)
    log(f"  ReadUp Pipeline 完了！", GREEN)
    log(f"{'═'*60}\n", GREEN)


if __name__ == "__main__":
    main()
