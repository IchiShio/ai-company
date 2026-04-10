#!/usr/bin/env python3
"""
毎日のSEOパイプライン — API不要版

使い方:
  python3 daily_pipeline.py              # 全ステップ実行
  python3 daily_pipeline.py --step seo   # SEOメンテナンスのみ
  python3 daily_pipeline.py --step links # 内部リンクのみ
  python3 daily_pipeline.py --step build # staging JSONから記事ビルドのみ
  python3 daily_pipeline.py --step topics # 次の記事トピック表示のみ

パイプライン全体の流れ:
  1. [seo]    check_stats.py — 統計チェック
  2. [seo]    add_citations.py — 引用リンク付与
  3. [seo]    fix_seo_baseline.py — SEOメタデータ修正
  4. [links]  add_internal_links.py — 内部リンク追加
  5. [build]  build_article.py --all — staging/JSONから記事ビルド
  6. [topics] 次に書くべきトピックの表示

API版スクリプト（ANTHROPIC_API_KEY設定時のみ）:
  7. generate_questions.py --count 100 — リスニング問題生成
  8. add_questions.py — 問題追加・MP3生成
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TODAY = date.today().isoformat()

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def header(text: str):
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")


def run(cmd: list[str], label: str) -> bool:
    print(f"  {BOLD}▶ {label}{RESET}")
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")
    if result.returncode != 0 and result.stderr:
        for line in result.stderr.strip().split("\n"):
            print(f"    {RED}{line}{RESET}")
    ok = result.returncode == 0
    status = f"{GREEN}✅ OK{RESET}" if ok else f"{RED}❌ FAIL{RESET}"
    print(f"  {status}\n")
    return ok


def step_factcheck():
    header("Step 0: ファクトチェック（必須ゲート）")
    ok = run(["python3", "factcheck.py", "--changed"], "新規・変更記事のファクトチェック")
    if not ok:
        print(f"  {RED}{BOLD}⛔ ファクトチェック不合格 — 問題を修正してから再実行してください{RESET}")
        print(f"  修正後: python3 factcheck.py --changed で再検証\n")
    return ok


def step_seo():
    header("Step 1: SEOメンテナンス")
    run(["python3", "check_stats.py"], "統計チェック (check_stats.py)")
    run(["python3", "add_citations.py"], "引用リンク付与 (add_citations.py)")
    run(["python3", "fix_seo_baseline.py"], "SEOメタデータ修正 (fix_seo_baseline.py)")


def step_links():
    header("Step 2: 内部リンク追加")
    run(["python3", "add_internal_links.py"], "内部リンク (add_internal_links.py)")


def step_build():
    header("Step 3: 記事ビルド (staging → HTML)")
    staging = BASE_DIR / "articles" / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    jsons = list(staging.glob("*.json"))
    if jsons:
        run(["python3", "build_article.py", "--all"], f"記事ビルド ({len(jsons)}件)")
    else:
        print(f"  {YELLOW}staging/ にJSONファイルなし — スキップ{RESET}")
        print(f"  記事を追加するには articles/staging/ にコンテンツJSONを配置してください\n")


def step_topics():
    header("Step 4: 次に書くべきトピック")
    queue_path = BASE_DIR / "data" / "seo-topics-queue.json"
    if not queue_path.exists():
        print(f"  {RED}seo-topics-queue.json が見つかりません{RESET}")
        return

    data = json.loads(queue_path.read_text())
    queue = data.get("queue", [])
    articles_dir = BASE_DIR / "articles"

    pending = []
    for t in queue:
        if not (articles_dir / t["slug"]).exists():
            pending.append(t)

    if not pending:
        print(f"  {GREEN}全トピック生成済み！ seo-topics-queue.json に新トピック追加が必要です{RESET}")
        return

    print(f"  未生成トピック: {BOLD}{len(pending)}件{RESET}\n")
    for i, t in enumerate(pending[:5], 1):
        print(f"  {BOLD}{i}. {t['title']}{RESET}")
        print(f"     slug: {t['slug']}")
        print(f"     KW: {t.get('target_kw', '—')}")
        print()

    print(f"  {YELLOW}ヒント: Claude Code に以下を依頼してください:{RESET}")
    top = pending[0]
    print(f'  「{top["slug"]} の記事を書いて articles/staging/ にJSON出力して」\n')


def step_api():
    header("Step 5: API依存タスク（オプション）")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        dotenv = BASE_DIR / ".env"
        if dotenv.exists():
            for line in dotenv.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY=") and "your_" not in line:
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        print(f"  {YELLOW}ANTHROPIC_API_KEY 未設定 — スキップ{RESET}")
        print(f"  設定方法: .env に ANTHROPIC_API_KEY=sk-... を追加\n")
        return

    print(f"  {GREEN}API Key 検出{RESET}")
    run(["python3", "generate_questions.py", "--count", "100"],
        "リスニング問題生成 (100問)")

    staging = BASE_DIR / "listening" / "staging.json"
    if staging.exists():
        run(["python3", "add_questions.py"], "問題追加・MP3生成")


def summary():
    header(f"パイプライン完了 — {TODAY}")

    # Count git changes
    result = subprocess.run(
        ["git", "diff", "--stat"], cwd=BASE_DIR, capture_output=True, text=True
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--stat"], cwd=BASE_DIR, capture_output=True, text=True
    )

    changes = result.stdout.strip()
    if changes:
        print(f"  {BOLD}変更ファイル:{RESET}")
        for line in changes.split("\n"):
            print(f"    {line}")
    else:
        print(f"  変更なし")

    print(f"\n  {YELLOW}コミット・プッシュするには:{RESET}")
    print(f"  git add -A && git commit -m 'daily SEO pipeline {TODAY}' && git push origin main\n")


def main():
    parser = argparse.ArgumentParser(description="毎日のSEOパイプライン")
    parser.add_argument("--step", choices=["factcheck", "seo", "links", "build", "topics", "api"],
                        help="特定のステップのみ実行")
    parser.add_argument("--skip-factcheck", action="store_true",
                        help="ファクトチェックをスキップ（非推奨）")
    args = parser.parse_args()

    header(f"Daily SEO Pipeline — {TODAY}")

    if args.step:
        {"factcheck": step_factcheck, "seo": step_seo, "links": step_links,
         "build": step_build, "topics": step_topics, "api": step_api}[args.step]()
    else:
        # ファクトチェックは最初に実行（必須ゲート）
        if not args.skip_factcheck:
            fc_ok = step_factcheck()
            if not fc_ok:
                print(f"  {RED}パイプラインを中断しました。ファクトチェックの問題を修正してください。{RESET}")
                summary()
                sys.exit(1)

        step_seo()
        step_links()
        step_build()
        step_topics()
        step_api()

    summary()


if __name__ == "__main__":
    main()
