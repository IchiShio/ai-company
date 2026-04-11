#!/usr/bin/env python3
"""
readup_pipeline.py — ReadUp 記事自動生成パイプライン

VOA最新記事を Gemma4 で4段階リライト → stories.js 追記 → git push

フロー（generate_series_ollama.py に委譲）:
  1. VOA 最新記事を取得
  2. Gemma4:latest で vl2000/vl3000/vl5000/vl7000 の4レベルに書き直し
  3. 和訳・問題生成
  4. reading/series/stories.js に追記
  5. git push → native-real.com

使い方:
  python3 readup_pipeline.py              # 最新1本
  python3 readup_pipeline.py --count 3   # 最新3本
  python3 readup_pipeline.py --dry-run   # デプロイしない
"""

import argparse
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
AICOMP_DIR  = BASE_DIR.parent / "ai-company"  # 同リポジトリの別clone
GEN_SCRIPT  = AICOMP_DIR / "generate_series_ollama.py"
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


def main():
    parser = argparse.ArgumentParser(description="ReadUp 記事自動生成 (VOA → Gemma4 → deploy)")
    parser.add_argument("--count",   type=int, default=1, help="生成記事数 (default: 1)")
    parser.add_argument("--model",   default="gemma4:latest", help="Ollamaモデル (default: gemma4:latest)")
    parser.add_argument("--dry-run", action="store_true", help="デプロイしない")
    args = parser.parse_args()

    log(f"\n{'═'*60}", BOLD)
    log(f"  ReadUp Pipeline  —  {TODAY}", BOLD)
    log(f"  VOA → Gemma4 ({args.model}) → 4レベル → native-real.com", BOLD)
    log(f"{'═'*60}")

    # Ollama チェック
    log(f"\n  Ollama 起動確認 ...", CYAN)
    if not check_ollama():
        log(f"  ❌ Ollama が起動していません", RED)
        log(f"     → ollama serve を先に実行してください", YELLOW)
        sys.exit(1)
    log(f"  ✅ Ollama: OK", GREEN)

    # generate_series_ollama.py の存在確認
    if not GEN_SCRIPT.exists():
        log(f"  ❌ {GEN_SCRIPT} が見つかりません", RED)
        log(f"     → ~/projects/claude/ai-company/ が存在するか確認してください", YELLOW)
        sys.exit(1)

    # git pull（最新に合わせる）
    log(f"\n  git pull ...", CYAN)
    subprocess.run(["git", "pull", "origin", "main", "--quiet"],
                   cwd=AICOMP_DIR, check=False)

    # 生成実行
    log(f"\n{'─'*60}")
    log(f"  Step 1 / VOA取得 → Gemma4 リライト ({args.count}本 × 4レベル)", BOLD + CYAN)
    log(f"{'─'*60}")

    cmd = [
        "python3", str(GEN_SCRIPT),
        "--count", str(args.count),
        "--model", args.model,
    ]
    if args.dry_run:
        cmd.append("--no-push")
        log(f"  [dry-run] --no-push で実行", YELLOW)

    log(f"  generate_series_ollama.py 実行中 ... （数分かかります）")
    result = subprocess.run(cmd, cwd=AICOMP_DIR)

    if result.returncode != 0:
        log(f"\n  ❌ 生成スクリプト失敗 (exit {result.returncode})", RED)
        sys.exit(1)

    if args.dry_run:
        log(f"\n  [dry-run] デプロイをスキップしました", YELLOW)
        log(f"  reading/series/staging.json を確認してください", YELLOW)
    else:
        log(f"\n  ✅ デプロイ完了 → native-real.com/reading/", GREEN)

    log(f"\n{'═'*60}", GREEN)
    log(f"  ReadUp Pipeline 完了！", GREEN)
    log(f"{'═'*60}\n", GREEN)


if __name__ == "__main__":
    main()
