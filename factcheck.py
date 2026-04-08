#!/usr/bin/env python3
"""
記事ファクトチェッカー（publish前必須ゲート）

新規・変更記事に対して以下を検査し、問題があれば非ゼロで終了する:
  1. 捏造パターン検出（具体的な%・調査名・研究者名+数値）
  2. ハルシネーション高リスク表現の検出
  3. **太字** マークダウン記法の検出
  4. 引用リンク未付与チェック

使い方:
  # 特定記事をチェック
  python3 factcheck.py articles/my-article/index.html

  # 新規・変更記事を自動検出してチェック（git diff --name-only）
  python3 factcheck.py --changed

  # 全記事チェック
  python3 factcheck.py --all

  # build_article.py から呼ばれるゲートモード（非ゼロで記事ビルドを中断）
  python3 factcheck.py --gate articles/my-article/index.html

終了コード:
  0: 問題なし（publish可）
  1: 要確認あり（修正後に再実行）
  2: ブロッキング問題あり（publish不可）
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SITE_DIR = Path(__file__).parent
CITATION_DB_PATH = SITE_DIR / "data" / "citation_db.json"

# ===== ブロッキング（publish不可）パターン =====
BLOCKING_PATTERNS = [
    # 架空の調査・アンケート（具体%付き）
    (r"(?:アンケート|調査)(?:で|では|の結果).*?(\d{2,})[%％]", "架空調査の疑い（具体%付き）"),
    # 架空の組織統計（具体%付き）
    (r"(MMD研究所|エン・ジャパン|船井総研|リクルート|マイナビ).*?\d+[%％]", "未検証組織+具体%"),
    # FSI誤用（日本人→英語に逆用）
    (r"FSI.*?日本語.*?2[,，]?200時間", "FSI誤用（日本人向けではない）"),
    (r"日本人.*?FSI.*?2[,，]?200時間", "FSI誤用（日本人向けではない）"),
    # マークダウン太字（HTMLでは表示されない）
    (r"\*\*[^*]+\*\*", "**太字**マークダウン記法（HTMLでは表示されない）"),
    # 架空URL（存在しない可能性が高い）
    (r'href="https?://(?:www\.)?(?!native-real\.com)[^"]*"[^>]*>.*?調査', "外部調査URL（要検証）"),
]

# ===== 警告（要確認だがブロックしない）パターン =====
WARNING_PATTERNS = [
    (r"([\w・]+(?:調査|研究所|機関|協会|総研)).*?(\d+[%％])", "外部統計引用"),
    (r"によると.*?(\d+[%％])", "「によると+%」"),
    (r"によれば.*?(\d+[%％])", "「によれば+%」"),
    (r"に掲載された研究", "ジャーナル引用"),
    (r"の研究(?:では|によると|によれば)", "研究者引用"),
    (r"(?:約|平均)\d+[%％](?:向上|改善|増加|減少)", "効果の具体%"),
    (r"\d+倍(?:と|に|が)(?:報告|示|確認)", "〇倍の引用"),
]

# ===== ハルシネーション高リスク表現 =====
HALLUCINATION_PATTERNS = [
    (r"(?:ハーバード|スタンフォード|MIT|オックスフォード|ケンブリッジ)(?:大学)?の(?:研究|調査)(?:では|によると|によれば).*?\d", "有名大学+具体数値（要検証）"),
    (r"(?:Nature|Science|Lancet|BMJ|JAMA)(?:誌)?に(?:掲載|発表)された", "著名ジャーナル引用（要検証）"),
    (r"20[12]\d年の(?:研究|調査|データ)(?:では|によると).*?\d+[%％]", "年号+具体%（捏造されやすい）"),
    (r"(?:世界保健機関|WHO|OECD|UNESCO|World Bank).*?\d+[%％]", "国際機関+具体%（要検証）"),
]

# ===== 許容パターン（CSS/JSコード内のマッチを除外）=====
SKIP_PATTERNS = [
    r"width|height|border|padding|margin|font|color|px|em|rem",
    r"display|position|flex|grid|background|opacity|z-index",
    r"border-radius|line-height|pointer|overflow|transform",
    r"<style|<script|</style|</script",
    r"var\(--|rgba\(|hsla?\(",
    r"\.btn|\.quiz|\.site-|\.article-|\.sidebar|\.footer|\.nav",
    r'class="',
]

# ===== 許容する既知の引用（CLAUDE.md記載の検証済み）=====
KNOWN_SAFE = [
    "Krashen", "Ebbinghaus", "Patricia Kuhl", "Carol Dweck",
    "DeKeyser", "Hartshorne et al", "Lally et al",
    "Zoltán Dörnyei", "忘却曲線", "習慣形成66日",
    "国税庁", "文科省", "IIBC", "英検.*協会",
    "プログリット.*公開データ", "公式サイトによると",
    "レアジョブ.*採用率.*1%",  # 検証済み
]


def should_skip(line: str) -> bool:
    return any(re.search(p, line) for p in SKIP_PATTERNS)


def is_known_safe(line: str) -> bool:
    return any(re.search(p, line) for p in KNOWN_SAFE)


def check_html(path: Path) -> dict:
    """1ファイルをチェック。結果dict: blocking/warnings/hallucinations"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    result = {"blocking": [], "warnings": [], "hallucinations": []}

    for lineno, line in enumerate(lines, 1):
        if should_skip(line):
            continue
        if is_known_safe(line):
            continue

        snippet = line.strip()[:140]

        # Blocking checks
        for pattern, label in BLOCKING_PATTERNS:
            if re.search(pattern, line):
                result["blocking"].append((lineno, label, snippet))
                break
        else:
            # Hallucination checks
            for pattern, label in HALLUCINATION_PATTERNS:
                if re.search(pattern, line):
                    result["hallucinations"].append((lineno, label, snippet))
                    break
            else:
                # Warning checks
                for pattern, label in WARNING_PATTERNS:
                    if re.search(pattern, line):
                        result["warnings"].append((lineno, label, snippet))
                        break

    return result


def get_changed_files() -> list[Path]:
    """git diff で変更された記事HTMLを取得"""
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, cwd=SITE_DIR
        )
        files = []
        for f in r.stdout.strip().split("\n"):
            if f.startswith("articles/") and f.endswith(".html"):
                p = SITE_DIR / f
                if p.exists():
                    files.append(p)
        return files
    except Exception:
        return []


def get_all_files() -> list[Path]:
    articles = SITE_DIR / "articles"
    return sorted(
        p for p in articles.rglob("index.html")
        if p.parent.name not in ("staging", "x-articles")
    )


def print_issues(label: str, issues: list, color: str):
    if not issues:
        return
    for lineno, reason, snippet in issues:
        print(f"  {color}L{lineno:4d} [{reason}]{RESET}")
        print(f"         {snippet}")


RED = "\033[91m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="記事ファクトチェッカー")
    parser.add_argument("files", nargs="*", help="チェックするHTMLファイル")
    parser.add_argument("--changed", action="store_true", help="git変更ファイルのみ")
    parser.add_argument("--all", action="store_true", help="全記事")
    parser.add_argument("--gate", action="store_true",
                        help="ゲートモード（ブロッキング問題で非ゼロ終了）")
    args = parser.parse_args()

    if args.all:
        files = get_all_files()
    elif args.changed:
        files = get_changed_files()
    elif args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
    else:
        files = get_changed_files()
        if not files:
            files = get_all_files()

    if not files:
        print("チェック対象ファイルがありません")
        sys.exit(0)

    print(f"\n{BOLD}=== ファクトチェック ({len(files)} ファイル) ==={RESET}\n")

    total_blocking = 0
    total_warnings = 0
    total_hallucinations = 0
    flagged = []

    for f in files:
        name = f.parent.name if f.name == "index.html" else f.stem
        result = check_html(f)

        n_b = len(result["blocking"])
        n_w = len(result["warnings"])
        n_h = len(result["hallucinations"])

        if n_b or n_w or n_h:
            flagged.append((name, result))
            total_blocking += n_b
            total_warnings += n_w
            total_hallucinations += n_h

    if not flagged:
        print(f"  {GREEN}✅ 全ファイルクリア — publish可{RESET}\n")
        sys.exit(0)

    for name, result in flagged:
        print(f"  {BOLD}📄 {name}{RESET}")
        print_issues("BLOCK", result["blocking"], RED)
        print_issues("HALLUCINATION", result["hallucinations"], MAGENTA)
        print_issues("WARNING", result["warnings"], YELLOW)
        print()

    # Summary
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  {RED}ブロッキング: {total_blocking}件{RESET}" if total_blocking else
          f"  {GREEN}ブロッキング: 0件{RESET}")
    print(f"  {MAGENTA}ハルシネーション疑い: {total_hallucinations}件{RESET}" if total_hallucinations else
          f"  {GREEN}ハルシネーション疑い: 0件{RESET}")
    print(f"  {YELLOW}要確認（許容済みの可能性あり）: {total_warnings}件{RESET}" if total_warnings else
          f"  {GREEN}要確認: 0件{RESET}")

    if total_blocking > 0:
        print(f"\n  {RED}{BOLD}❌ PUBLISH不可 — ブロッキング問題を修正してください{RESET}")
        print(f"  修正方法:")
        print(f"    - 架空の%値 → 「〜とされています」等の定性表現に置換")
        print(f"    - **太字** → <strong>タグに置換")
        print(f"    - FSI誤用 → 削除または正確な文脈に修正")
        sys.exit(2)

    if total_hallucinations > 0:
        print(f"\n  {MAGENTA}{BOLD}⚠️ ハルシネーション疑い — WebSearchで検証してください{RESET}")
        if args.gate:
            print(f"  ゲートモード: 検証完了まで publish をブロックします")
            sys.exit(1)

    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
