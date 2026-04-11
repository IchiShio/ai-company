#!/usr/bin/env python3
"""
grammar_pipeline.py — 文法問題自動生成パイプライン

フロー:
  1. Gemma4:e4b (Ollama) でドラフト問題生成 → grammar/staging.json
  2. Claude Code CLI (claude -p) でQC・修正 → grammar/questions_extra.js に追記
  3. git push でデプロイ

使い方:
  python3 grammar_pipeline.py              # デフォルト5問生成・QC・デプロイ
  python3 grammar_pipeline.py --count 10   # 10問生成
  python3 grammar_pipeline.py --dry-run    # デプロイしない（確認用）
  python3 grammar_pipeline.py --step generate  # Step1のみ
  python3 grammar_pipeline.py --step qc        # Step2のみ（既存 staging.json を使用）
  python3 grammar_pipeline.py --step deploy    # Step3のみ
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from pipeline_status import PipelineStatus

BASE_DIR = Path(__file__).resolve().parent
STAGING_PATH = BASE_DIR / "grammar" / "staging.json"
QUESTIONS_PATH = BASE_DIR / "grammar" / "questions_extra.js"
TODAY = date.today().isoformat()

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def log(msg: str, color: str = CYAN):
    print(f"{color}{msg}{RESET}")


def get_last_id() -> int:
    """questions_extra.js から最後の問題IDを取得"""
    content = QUESTIONS_PATH.read_text()
    ids = re.findall(r'id:\s*"g(\d+)"', content)
    return max(int(i) for i in ids) if ids else 1562


def get_sparse_topics(top_n: int = 20) -> list[str]:
    """既存問題のタグを分析して、問題数が少ないトピックタグを返す"""
    from collections import Counter
    content = QUESTIONS_PATH.read_text()
    tag_groups = re.findall(r'tags:\s*\[([^\]]+)\]', content)
    all_tags = []
    for group in tag_groups:
        all_tags.extend(re.findall(r'"([^"]+)"', group))

    # eiken/toeic/juken などの難易度タグは除外
    skip = {"eiken1", "eiken2", "eiken3", "toeic", "juken", "eikenpre1"}
    topic_tags = [t for t in all_tags if t not in skip]
    counts = Counter(topic_tags)

    # 出現数が少ない順（不足トピック）を返す
    sparse = [tag for tag, _ in counts.most_common()[:-top_n-1:-1]]
    return sparse


def build_prompt(start_id: int, count: int, topics: list[str]) -> str:
    ids = [f"g{start_id + i}" for i in range(count)]
    topic_lines = "\n".join(f"- {t}" for t in topics[:count])
    return f"""You are a Japanese English education content creator specializing in TOEIC/英検 grammar quizzes.
Generate exactly {count} grammar quiz questions in JavaScript object format.

EXAMPLE (follow this exact format):
{{ id: "g9001", diff: "lv3", axis: "form", tags: ["eiken2", "toeic"], stem: "It is essential that every employee ___ the new policy.", ja: "全従業員がその新しい方針に従うことが不可欠です。", answer: "follow", choices: ["follow", "follows", "followed", "following", "has followed"], expl: "【正解】follow：It is essential that S + 動詞原形（仮定法現在）。三人称単数でも -s をつけない。【誤答】follows：三人称単数現在形。仮定法現在では原形を使う（誤り）。【誤答】followed：過去形。時制が合わない（誤り）。【誤答】following：現在分詞。動詞の原形が必要（誤り）。【誤答】has followed：現在完了形。仮定法現在には使えない（誤り）。", rule: "It is essential/vital/important that S + 動詞原形：仮定法現在で動詞は常に原形", kp: ["It is essential that S follow = Sが従うことが不可欠（原形・三単現 -s なし）", "essential/vital/important that + 原形（= should + 原形の省略形）"] }},

REQUIRED OUTPUT FORMAT (one object per line, no markdown, no code blocks):
{{ id: "gXXXX", diff: "lvN", axis: "AXIS", tags: ["TAG1", "TAG2"], stem: "Sentence with ONE blank ___.", ja: "日本語訳。", answer: "ACTUAL_CORRECT_WORD", choices: ["ACTUAL_WORD_1", "ACTUAL_WORD_2", "ACTUAL_WORD_3", "ACTUAL_WORD_4", "ACTUAL_WORD_5"], expl: "【正解】WORD：理由。【誤答】WORD2：なぜ誤りか。【誤答】WORD3：なぜ誤りか。【誤答】WORD4：なぜ誤りか。【誤答】WORD5：なぜ誤りか。", rule: "一行の文法ルール（日本語）", kp: ["英語フレーズ1 = 日本語（文法ポイント）", "英語フレーズ2 = 日本語（対比・補足）"] }},

STRICT CONSTRAINTS:
- Use exactly these IDs in order: {", ".join(ids)}
- diff: lv1(易)〜lv5(難)
- axis: exactly one of form / logic / tense / vocab / context
- choices: exactly 5 entries, ALL UNIQUE (zero duplicates allowed)
- answer: must exactly match one of the 5 choices
- expl: cover ALL 5 choices with 【正解】/【誤答】 labels in Japanese
- kp: exactly 2 strings, each "English = 日本語（note）"
- tags: pick from eiken3 / eiken2 / eiken1 / toeic, PLUS include the topic tag below

TOPIC ASSIGNMENTS (one topic per question, in order):
{topic_lines}

Output ONLY the {count} JS objects. Absolutely no markdown. No explanation text."""


# ─── Step 1: ドラフト生成 ────────────────────────────────────────────────────

def step_generate(count: int):
    log(f"\n{'─'*60}")
    log(f"  Step 1 / Gemma4:e4b → ドラフト {count}問 生成", BOLD + CYAN)
    log(f"{'─'*60}")

    last_id = get_last_id()
    log(f"  現在の最終ID: g{last_id}  →  g{last_id+1}〜g{last_id+count} を生成")

    topics = get_sparse_topics(top_n=count * 2)
    log(f"  不足トピック（生成対象）: {', '.join(topics[:count])}", YELLOW)

    prompt = build_prompt(last_id + 1, count, topics)
    payload = json.dumps({
        "model": "gemma4:e4b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 4096}
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
            raw = data["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        log(f"  ❌ Ollama接続エラー: {e}", RED)
        log("     → ollama serve が起動しているか確認してください", YELLOW)
        sys.exit(1)

    # マークダウンコードブロックを除去
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

    STAGING_PATH.write_text(raw + "\n")
    line_count = raw.count('{ id:')
    log(f"  ✅ {line_count}問 生成 → grammar/staging.json", GREEN)


# ─── Step 2a: Claude Code ファクトチェック ────────────────────────────────────

def step_factcheck():
    log(f"\n{'─'*60}")
    log(f"  Step 2a / Claude Code → 文法ファクトチェック", BOLD + CYAN)
    log(f"{'─'*60}")

    if not STAGING_PATH.exists() or not STAGING_PATH.read_text().strip():
        log("  ❌ grammar/staging.json が空です", RED)
        sys.exit(1)

    factcheck_prompt = """grammar/staging.json に英語文法問題のドラフトが入っています。
デプロイ前の最終ファクトチェックとして、以下を厳密に検証してください。

## 検証項目（全問・全選択肢）

### A. 文法ルールの正確性
- stem の英文が標準的な英語として自然か
- answer として指定された語句が、その文脈で**唯一の正解**か
- 他の choices が「誤答として本当に誤り」かを1つずつ確認する
  - 「文脈次第では正解になりうる」選択肢がないか特に注意
  - 例: "would give" と "would have given" は両方使える文脈があるため注意

### B. 解説の正確性
- expl の説明が言語学的・文法的に正確か
- 誤答の「なぜ誤りか」の理由が正確か（「時制が合わない」「不定詞が必要」など）
- rule フィールドの文法ルールが一般的に認められたルールか

### C. 問題の品質
- 問題として成立しているか（曖昧さがないか）
- TOEIC・英検の出題傾向として適切か

## アクション

- 問題あり → staging.json の該当フィールドを直接修正する
- 修正不可能なレベルの問題（stem 自体が成立しないなど）→ その問題を staging.json から削除する
- 問題なし → そのまま

## 完了報告
各問題について「✅ 合格」または「⚠️ 修正: [内容]」または「❌ 削除: [理由]」を報告してください。
最後に「FACTCHECK DONE: N問合格 / M問修正 / K問削除」と出力してください。
"""

    cmd = [
        "claude", "-p", factcheck_prompt,
        "--allowedTools", "Read,Edit",
        "--dangerously-skip-permissions",
        "--system-prompt", "You are an expert English linguist and grammar fact-checker. Verify grammar rules with precision.",
    ]

    log(f"  claude -p 実行中 ... （1〜2分かかる場合があります）")
    try:
        result = subprocess.run(
            cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=360
        )
    except subprocess.TimeoutExpired:
        log("  ❌ ファクトチェックがタイムアウト（360秒）", RED)
        sys.exit(1)

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")
    if result.returncode != 0:
        log("  ❌ Claude Code 終了コード異常:", RED)
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(f"  {RED}{line}{RESET}")
        sys.exit(1)

    # staging が空になっていたら（全問削除）中断
    remaining = STAGING_PATH.read_text().strip()
    if not remaining or remaining in ("[]", ""):
        log("  ⚠️  全問削除されました — デプロイをスキップします", YELLOW)
        sys.exit(0)

    log(f"  ✅ ファクトチェック完了", GREEN)


# ─── Step 2b: Claude Code QC ─────────────────────────────────────────────────

def step_qc():
    log(f"\n{'─'*60}")
    log(f"  Step 2 / Claude Code → QC・修正・questions_extra.js 追記", BOLD + CYAN)
    log(f"{'─'*60}")

    if not STAGING_PATH.exists() or not STAGING_PATH.read_text().strip():
        log("  ❌ grammar/staging.json が空です — Step 1 を先に実行してください", RED)
        sys.exit(1)

    last_id = get_last_id()

    qc_prompt = f"""grammar/staging.json に Gemma4 が生成した英語文法問題のドラフトが入っています（JavaScript オブジェクト形式のテキスト）。

以下の手順で QC・修正してから grammar/questions_extra.js に追記してください。

## QC チェック（全問必須）

1. **choices 重複チェック**
   - 5つの選択肢がすべて異なる値か確認
   - 重複があれば文法的に意味のある別の誤答に差し替える

2. **answer の整合性**
   - answer の値が choices 配列の中に完全一致で含まれているか確認
   - 不一致なら修正する

3. **expl の品質**
   - 全5選択肢について説明があるか確認
   - 【正解】と【誤答】のラベルが付いているか
   - なければ補完する（日本語）

4. **kp のフォーマット**
   - ちょうど 2 要素か
   - 各要素が「英語フレーズ = 日本語（文法メモ）」形式か
   - 違えば修正する

5. **diff の妥当性**
   - eiken3 タグ → lv1〜2、eiken2 → lv2〜3、eiken1 → lv4〜5
   - toeic → lv2〜4 が目安
   - ズレていれば修正

6. **英語の正確性**
   - stem（問題文）の英語が自然か確認
   - answer が実際に正しい英語か確認

## questions_extra.js への追記

- `grammar/questions_extra.js` の末尾を確認する
- ファイル最終行の `);` の直前の行に追記する
- staging.json の各オブジェクトを `  {{ id: "...", ... }},` の形式で1行ずつ追記
- 追記後、`grammar/staging.json` の内容を `[]` にリセット（空配列）

## 完了報告
最後に「✅ N問追記完了（g{last_id+1}〜）」と出力してください。
"""

    cmd = [
        "claude", "-p", qc_prompt,
        "--allowedTools", "Read,Edit",
        "--dangerously-skip-permissions",
        # プロジェクトの CLAUDE.md（11K tokens）をロードしない
        # → 起動が速くなりタイムアウトを回避
        "--system-prompt", "You are a grammar QC assistant. Read files, fix issues, and edit files as instructed.",
    ]

    log(f"  claude -p 実行中 ... （1〜2分かかる場合があります）")
    try:
        result = subprocess.run(
            cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=360
        )
    except subprocess.TimeoutExpired:
        log("  ❌ Claude Code がタイムアウトしました（360秒）", RED)
        sys.exit(1)

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")
    if result.returncode != 0:
        log("  ❌ Claude Code 終了コード異常:", RED)
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(f"  {RED}{line}{RESET}")
        sys.exit(1)

    log(f"  ✅ QC・追記完了", GREEN)


# ─── Step 3: デプロイ ─────────────────────────────────────────────────────────

def step_deploy():
    log(f"\n{'─'*60}")
    log(f"  Step 3 / git push → native-real.com デプロイ", BOLD + CYAN)
    log(f"{'─'*60}")

    diff = subprocess.run(
        ["git", "diff", "--stat", "grammar/"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    if not diff.stdout.strip():
        log("  変更なし — デプロイをスキップ", YELLOW)
        return

    steps = [
        (["git", "add", "grammar/questions_extra.js", "grammar/staging.json"], "git add"),
        (["git", "commit", "-m", f"grammar: auto-generate questions ({TODAY})"], "git commit"),
        (["git", "stash"], "git stash"),
        (["git", "pull", "--rebase", "origin", "main"], "git pull --rebase"),
        (["git", "stash", "pop"], "git stash pop"),
        (["git", "push", "origin", "main"], "git push → native-real.com"),
    ]
    for cmd, label in steps:
        r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        ok = r.returncode == 0
        icon = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
        print(f"  {icon} {label}")
        if not ok and label not in ("git stash", "git stash pop"):
            log(f"     {r.stderr.strip()}", RED)
            sys.exit(1)

    log(f"  ✅ デプロイ完了", GREEN)


# ─── エントリポイント ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="文法問題自動生成パイプライン (Gemma4 → Claude Code QC → Deploy)")
    parser.add_argument("--count", type=int, default=5, metavar="N", help="生成問題数 (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="デプロイしない（確認用）")
    parser.add_argument("--step", choices=["generate", "factcheck", "qc", "deploy"],
                        help="特定ステップのみ実行")
    args = parser.parse_args()

    log(f"\n{'═'*60}", BOLD)
    log(f"  Grammar Pipeline  —  {TODAY}", BOLD)
    log(f"  Gemma4:e4b → Factcheck → QC → native-real.com", BOLD)
    log(f"{'═'*60}")

    ps = PipelineStatus("grammar")

    if args.step:
        {"generate":   lambda: step_generate(args.count),
         "factcheck":  step_factcheck,
         "qc":         step_qc,
         "deploy":     step_deploy}[args.step]()
    else:
        ps.start(total_steps=4, description=f"GrammarUp: {args.count}問生成→QC→deploy")
        try:
            ps.update(1, "Gemma4 ドラフト生成")
            step_generate(args.count)
            ps.update(2, "Factcheck (claude -p)")
            step_factcheck()
            ps.update(3, "QC・questions_extra.js 追記")
            step_qc()
            if args.dry_run:
                log(f"\n  [dry-run] デプロイをスキップしました", YELLOW)
                log(f"  grammar/questions_extra.js を確認してください", YELLOW)
                ps.done(success=True, message="dry-run完了")
            else:
                ps.update(4, "git push")
                step_deploy()
                ps.done(success=True)
        except SystemExit as e:
            ps.done(success=(e.code == 0), message=f"exit {e.code}")
            raise

    log(f"\n{'═'*60}", GREEN)
    log(f"  パイプライン完了！", GREEN)
    log(f"{'═'*60}\n", GREEN)


if __name__ == "__main__":
    main()
