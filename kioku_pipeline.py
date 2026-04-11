#!/usr/bin/env python3
"""
kioku_pipeline.py — 語根で覚える英単語 新語根追加パイプライン

フロー:
  1. [generate]    Claude Code で新語根データ生成 → staging/ROOT.json
  2. [factcheck]   Claude Code で語源・認知言語学ファクトチェック
  3. [audio]       Edge TTS で単語音声生成 → audio/WORD/word.mp3
  4. [merge]       staging/ → data/words/ にマージ
  5. [deploy]      git push → native-real.com

使い方:
  python3 kioku_pipeline.py --root vert          # vert/vers 語根を追加
  python3 kioku_pipeline.py --root press         # press 語根を追加
  python3 kioku_pipeline.py --roots vert press lect  # 複数語根を順番に処理
  python3 kioku_pipeline.py --dry-run --root vert    # デプロイしない
  python3 kioku_pipeline.py --step generate --root vert   # ステップ個別実行
  python3 kioku_pipeline.py --step factcheck --root vert
  python3 kioku_pipeline.py --step audio
  python3 kioku_pipeline.py --step merge
  python3 kioku_pipeline.py --step deploy

推奨新語根（TOEIC頻出・未収録）:
  vert/vers  回る・向ける  convert, reverse, diverse, controversy
  press      押す・圧力    express, impress, compress, suppress
  lect       選ぶ・集める  collect, select, elect, intellect
  fuse       注ぐ・流す    refuse, confuse, infuse, diffuse
  pel/puls   駆る・押す    expel, compel, repel, impulse, propel
  graph      書く         paragraph, diagram, biography, autograph
  log/logy   言葉・学問    logic, apology, biology, analogy
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from pipeline_status import PipelineStatus

BASE_DIR     = Path(__file__).resolve().parent
KIOKU_DIR    = BASE_DIR / "kioku-shinai"
STAGING_DIR  = KIOKU_DIR / "staging"
DATA_DIR     = KIOKU_DIR / "data" / "words"
AUDIO_DIR    = KIOKU_DIR / "audio"
TODAY        = date.today().isoformat()

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def log(msg: str, color: str = CYAN):
    print(f"{color}{msg}{RESET}")


def get_existing_roots() -> list[str]:
    return [f.stem for f in DATA_DIR.glob("*.json")]


def staging_path(root_id: str) -> Path:
    return STAGING_DIR / f"{root_id}.json"


def run_claude(prompt: str, label: str, timeout: int = 360) -> bool:
    """claude -p でプロンプトを実行。成功なら True を返す"""
    cmd = [
        "claude", "-p", prompt,
        "--allowedTools", "Read,Edit,Write",
        "--dangerously-skip-permissions",
        "--system-prompt", "You are a linguistic expert specializing in English etymology and cognitive linguistics.",
    ]
    log(f"  claude -p 実行中: {label} ... （1〜2分）")
    try:
        result = subprocess.run(
            cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        log(f"  ❌ タイムアウト（{timeout}秒）: {label}", RED)
        return False

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")
    if result.returncode != 0:
        log(f"  ❌ 終了コード異常: {label}", RED)
        if result.stderr:
            for line in result.stderr.strip().split("\n")[:5]:
                print(f"  {RED}{line}{RESET}")
        return False
    return True


# ─── Step 1: 新語根データ生成 ────────────────────────────────────────────────

ROOT_META = {
    "vert":  {"full": "vert/vers",  "meaning": "回る・向ける", "lang": "ラテン語 vertere（PIE *wer-）",  "words": "convert, reverse, diverse, version, controversy, avert, revert, divert, invert, subvert, versatile, diversion, adversary, advertisement, extrovert, introvert, anniversary, vertigo, pervert, revert"},
    "press": {"full": "press",      "meaning": "押す・圧力",   "lang": "ラテン語 pressare/premere",       "words": "express, impress, compress, suppress, depress, repress, oppress, pressure, impression, depression, expression, compression, oppression, repression, irresistible, pressing, pressurize, fingerprint, espresso, bulldozer"},
    "lect":  {"full": "lect/lig",   "meaning": "選ぶ・集める", "lang": "ラテン語 legere（PIE *leg-）",    "words": "collect, select, elect, intellect, neglect, recollect, elegant, eligible, diligent, predilection, election, collection, selection, intellectual, negligent, lecture, legend, legible, illegible, religion"},
    "fuse":  {"full": "fuse/fund",  "meaning": "注ぐ・流す",   "lang": "ラテン語 fundere（PIE *gheu-）",  "words": "refuse, confuse, infuse, diffuse, transfuse, profuse, defuse, effuse, suffuse, confound, fundamental, profound, foundation, fund, fuse, fusion, confusion, refusal, diffusion, infusion"},
    "pel":   {"full": "pel/puls",   "meaning": "駆る・押す",   "lang": "ラテン語 pellere（PIE *pel-）",   "words": "expel, compel, repel, impel, propel, dispel, impulse, compulsory, repulsion, propulsion, appeal, expulsion, pulse, pulsate, repulsive, compelling, propeller, catapult, anvil, interpolate"},
    "graph": {"full": "graph/gram", "meaning": "書く・記録",   "lang": "ギリシャ語 graphein（PIE *gerbh-）","words": "paragraph, diagram, biography, autograph, photograph, geography, graphic, grammar, program, telegram, monograph, bibliography, cryptography, calligraphy, demographics, epigraph, ideogram, hologram, cardiogram, choreography"},
    "log":   {"full": "log/logy",   "meaning": "言葉・論理・学問", "lang": "ギリシャ語 logos（PIE *leg-）", "words": "logic, apology, biology, analogy, dialogue, catalog, epilogue, prologue, monologue, ideology, psychology, sociology, technology, chronology, mythology, terminology, tautology, ecology, anthology, eulogy"},
}


BATCH_SIZE = 5  # 1回のclaudeコールで生成する単語数（タイムアウト対策）


def _generate_batch(root_id: str, meta: dict, words_batch: list[str],
                    batch_no: int, total_batches: int, is_first: bool):
    """5語分のデータを生成してstaging JSONに追記/作成する"""

    toeic_start = (batch_no - 1) * BATCH_SIZE + 1

    if is_first:
        # 初回バッチ: ルートメタデータ + 最初の5語
        prompt = f"""以下の仕様で英語語根データを生成してください。

## 語根情報
- root_id: {root_id}
- root（表示名）: {meta['full']}
- rootMeaning: {meta['meaning']}
- rootLang: {meta['lang']}

## 参照ファイル
`kioku-shinai/data/words/duct.json` を読んで、完全に同じスキーマで生成してください。

## 今回生成する単語（バッチ {batch_no}/{total_batches}）
{', '.join(words_batch)}（toeicRank {toeic_start}〜{toeic_start+len(words_batch)-1}）

## 出力形式
`kioku-shinai/staging/{root_id}.json` を新規作成してください。
内容:
{{
  "root": "{meta['full']}",
  "rootMeaning": "{meta['meaning']}",
  "rootLang": "{meta['lang']}",
  "imageSchema": "（この語根の身体的・空間的イメージ 1〜2文）",
  "hook": {{"label": "記憶フック", "text": "（語根が見えれば20語読める強烈なフック）"}},
  "words": [ ...{len(words_batch)}語分の完全なエントリ... ]
}}

各単語に必ず含めるフィールド:
word, phonetic（IPA）, toeicRank, parts（分解）,
etymology（oneliner/fact/source/cognates）,
cognitive（oneliner/fact/source）,
gap, gapOneliner, hook,
formats（5種・duct.jsonと同じ構造）,
examples（TOEIC例文3文・英語+日本語訳）

完了したら「✅ バッチ{batch_no} 完了: {len(words_batch)}語」と報告してください。
"""
    else:
        # 追加バッチ: 既存 staging.json の words 配列に追記
        prompt = f"""`kioku-shinai/staging/{root_id}.json` が既に存在します。
この words 配列に以下の単語を追記してください（既存の配列は変更しない）。

## 追記する単語（バッチ {batch_no}/{total_batches}）
{', '.join(words_batch)}（toeicRank {toeic_start}〜{toeic_start+len(words_batch)-1}）

## 参照
`kioku-shinai/data/words/duct.json` と同じスキーマで生成。

各単語に必ず含めるフィールド:
word, phonetic, toeicRank, parts, etymology, cognitive,
gap, gapOneliner, hook, formats（5種）, examples（3文）

ファイルを読んで words 配列の末尾に追記し、上書き保存してください。
完了したら「✅ バッチ{batch_no} 完了: {len(words_batch)}語追記」と報告してください。
"""

    return run_claude(prompt, f"{root_id} バッチ{batch_no}/{total_batches}", timeout=360)


def step_generate(root_id: str):
    log(f"\n{'─'*60}")
    log(f"  Step 1 / Claude Code → {root_id} 語根データ生成", BOLD + CYAN)
    log(f"{'─'*60}")

    if root_id in get_existing_roots():
        log(f"  ⚠️  {root_id} は既に data/words/ に存在します", YELLOW)
        sys.exit(1)

    meta = ROOT_META.get(root_id)
    if not meta:
        log(f"  ❌ 未定義の語根: {root_id}", RED)
        log(f"     定義済み: {', '.join(ROOT_META.keys())}", YELLOW)
        sys.exit(1)

    words_list = [w.strip() for w in meta["words"].split(",")][:20]
    batches = [words_list[i:i+BATCH_SIZE] for i in range(0, len(words_list), BATCH_SIZE)]
    log(f"  {len(words_list)}語を {len(batches)}バッチ（{BATCH_SIZE}語×）で生成")

    for i, batch in enumerate(batches, 1):
        log(f"\n  バッチ {i}/{len(batches)}: {', '.join(batch)}", YELLOW)
        ok = _generate_batch(root_id, meta, batch, i, len(batches), is_first=(i == 1))
        if not ok:
            log(f"  ❌ バッチ{i} 失敗 — 途中まで生成された staging/{root_id}.json を確認してください", RED)
            sys.exit(1)

    spath = staging_path(root_id)
    if not spath.exists():
        log(f"  ❌ staging/{root_id}.json が生成されませんでした", RED)
        sys.exit(1)

    try:
        data = json.load(open(spath))
        n = len(data.get("words", []))
        log(f"\n  ✅ {root_id} 生成完了: {n}語 → kioku-shinai/staging/{root_id}.json", GREEN)
    except json.JSONDecodeError as e:
        log(f"  ❌ JSON パースエラー: {e}", RED)
        sys.exit(1)


# ─── Step 2: ファクトチェック ─────────────────────────────────────────────────

def step_factcheck(root_id: str):
    log(f"\n{'─'*60}")
    log(f"  Step 2 / Claude Code → {root_id} ファクトチェック", BOLD + CYAN)
    log(f"{'─'*60}")

    spath = staging_path(root_id)
    if not spath.exists():
        log(f"  ❌ staging/{root_id}.json がありません — Step 1 を先に実行", RED)
        sys.exit(1)

    prompt = f"""`kioku-shinai/staging/{root_id}.json` の語源データをファクトチェックしてください。

## 検証項目（全単語）

### A. 語源の正確性
- etymology.fact が EtymOnline・Oxford Etymology で裏付けられる内容か
- 英語に入った年代が正確か（「〜世紀」レベルで）
- parts の語根分解が実際の語源と一致しているか
- cognates に無関係な単語が混入していないか

### B. 認知言語学の正確性
- cognitive.fact に記載のイメージスキーマ名が正しい学術用語か
- source に挙げた文献と記述内容が矛盾していないか

### C. 英語の正確性
- etymology.oneliner の意味の流れが自然か
- examples の英文が文法的・語彙的に正確か
- formats の choices に「正解になりうる選択肢」が混入していないか

### D. スキーマの完全性
- 全20語に全フィールドが存在するか（formats 5種・examples 3文含む）
- toeicRank が 1〜20 の重複なし昇順か

## アクション
- 誤りを発見したら `kioku-shinai/staging/{root_id}.json` を直接修正
- 修正不能な誤りは該当単語を削除

## 最後に必ず実行すること（必須）
全検証・修正が完了したら、`kioku-shinai/staging/{root_id}.json` を読み込み、
JSONのトップレベルに以下の2フィールドを追加して上書き保存してください:

  "fact_check": "APPROVED",
  "checked_at": "{TODAY}"

## 完了報告
ファイル保存後に「FACTCHECK DONE: N語合格 / M語修正 / K語削除 — APPROVED書き込み済み」と出力してください。
"""

    ok = run_claude(prompt, f"{root_id} ファクトチェック", timeout=720)
    if not ok:
        sys.exit(1)

    # fact_check: APPROVED が付いているか確認
    try:
        data = json.load(open(spath))
        if data.get("fact_check") != "APPROVED":
            log(f"  ⚠️  fact_check が APPROVED になっていません", YELLOW)
            log(f"     手動確認してから --step merge を実行してください", YELLOW)
            sys.exit(1)
    except json.JSONDecodeError:
        log(f"  ❌ JSON パースエラー", RED)
        sys.exit(1)

    log(f"  ✅ ファクトチェック完了 (APPROVED)", GREEN)


# ─── Step 3: 音声生成 ─────────────────────────────────────────────────────────

def step_audio(root_id: str):
    log(f"\n{'─'*60}")
    log(f"  Step 3 / Edge TTS → {root_id} 音声生成", BOLD + CYAN)
    log(f"{'─'*60}")

    spath = staging_path(root_id)
    if not spath.exists():
        log(f"  ❌ staging/{root_id}.json がありません", RED)
        sys.exit(1)

    data  = json.load(open(spath))
    words = [w["word"] for w in data.get("words", [])]

    # 既存音声のある単語はスキップ
    new_words = [w for w in words if not (AUDIO_DIR / w / "word.mp3").exists()]
    if not new_words:
        log(f"  全{len(words)}語の音声が既に存在します — スキップ", YELLOW)
        return

    log(f"  新規音声生成: {len(new_words)}語 / スキップ: {len(words)-len(new_words)}語")

    result = subprocess.run(
        ["python3", "generate_audio.py", "--words"] + new_words,
        cwd=KIOKU_DIR, capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        # generate_audio.py が --words オプションを持たない場合は全体実行
        log(f"  --words オプション未対応 → 全体実行", YELLOW)
        result = subprocess.run(
            ["python3", "generate_audio.py"],
            cwd=KIOKU_DIR, capture_output=True, text=True, timeout=300
        )

    if result.stdout:
        for line in result.stdout.strip().split("\n")[-10:]:
            print(f"  {line}")
    if result.returncode != 0:
        log(f"  ❌ 音声生成エラー", RED)
        sys.exit(1)

    log(f"  ✅ 音声生成完了", GREEN)


# ─── Step 4: data/words にマージ ──────────────────────────────────────────────

def step_merge(root_id: str):
    log(f"\n{'─'*60}")
    log(f"  Step 4 / staging → data/words/{root_id}.json マージ", BOLD + CYAN)
    log(f"{'─'*60}")

    spath = staging_path(root_id)
    dpath = DATA_DIR / f"{root_id}.json"

    if not spath.exists():
        log(f"  ❌ staging/{root_id}.json がありません", RED)
        sys.exit(1)

    staging_data = json.load(open(spath))

    if staging_data.get("fact_check") != "APPROVED":
        log(f"  ❌ fact_check が APPROVED でないためマージを拒否します", RED)
        sys.exit(1)

    if dpath.exists():
        log(f"  ⚠️  {root_id}.json は既に存在します — 上書きしますか？ [y/N]: ", YELLOW)
        ans = input().strip().lower()
        if ans != "y":
            log(f"  キャンセルしました", YELLOW)
            sys.exit(0)

    # staging から fact_check / checked_at を除いた本体を data/words に保存
    output = {k: v for k, v in staging_data.items()
              if k not in ("root_id", "fact_check", "checked_at")}

    with open(dpath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    n = len(output.get("words", []))
    log(f"  ✅ {n}語 → data/words/{root_id}.json", GREEN)

    # staging を削除
    spath.unlink()
    log(f"  🗑  staging/{root_id}.json を削除", YELLOW)


# ─── Step 5: デプロイ ──────────────────────────────────────────────────────────

def step_deploy(root_id: str):
    log(f"\n{'─'*60}")
    log(f"  Step 5 / git push → native-real.com デプロイ", BOLD + CYAN)
    log(f"{'─'*60}")

    steps = [
        (["git", "add",
          f"kioku-shinai/data/words/{root_id}.json",
          "kioku-shinai/audio/",
          "kioku-shinai/staging/"],
         "git add"),
        (["git", "commit", "-m",
          f"kioku-shinai: add {root_id} root ({TODAY})"],
         "git commit"),
        (["git", "push", "origin", "main"],
         "git push → native-real.com"),
    ]
    for cmd, label in steps:
        r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        ok = r.returncode == 0
        icon = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
        print(f"  {icon} {label}")
        if not ok:
            log(f"     {r.stderr.strip()}", RED)
            sys.exit(1)

    log(f"  ✅ デプロイ完了 → native-real.com/kioku-shinai/", GREEN)


# ─── エントリポイント ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="kioku-shinai 新語根追加パイプライン")
    parser.add_argument("--root",  help="追加する語根ID (例: vert, press, lect)")
    parser.add_argument("--roots", nargs="+", help="複数語根を順番に処理")
    parser.add_argument("--dry-run", action="store_true", help="デプロイしない")
    parser.add_argument("--step",
                        choices=["generate", "factcheck", "audio", "merge", "deploy"],
                        help="特定ステップのみ実行")
    parser.add_argument("--list-roots", action="store_true",
                        help="追加可能な語根一覧を表示")
    args = parser.parse_args()

    if args.list_roots:
        existing = set(get_existing_roots())
        log(f"\n  追加可能な語根（未収録）:", BOLD)
        for rid, meta in ROOT_META.items():
            status = f"{RED}収録済み{RESET}" if rid in existing else f"{GREEN}追加可能{RESET}"
            print(f"  {rid:8s}  {meta['full']:12s}  {meta['meaning']:16s}  [{status}]")
        print()
        return

    # --root next: ROOT_META の中で未収録の最初の語根を自動選択
    root_arg = args.root
    if root_arg == "next":
        existing = set(get_existing_roots())
        root_arg = next((rid for rid in ROOT_META if rid not in existing), None)
        if root_arg is None:
            log("  ✅ すべての語根が収録済みです。追加する語根がありません。", GREEN)
            sys.exit(0)
        log(f"  [auto] 次の未収録語根を選択: {root_arg}", CYAN)

    roots = args.roots if args.roots else ([root_arg] if root_arg else [])
    if not roots and not args.step:
        parser.print_help()
        sys.exit(1)

    for root_id in roots or [args.root]:
        if root_id is None:
            continue

        log(f"\n{'═'*60}", BOLD)
        log(f"  Kioku Pipeline  —  {root_id}  —  {TODAY}", BOLD)
        log(f"  Claude Code生成 → Factcheck → Audio → Deploy", BOLD)
        log(f"{'═'*60}")

        ps = PipelineStatus("kioku")

        if args.step:
            {
                "generate":  lambda: step_generate(root_id),
                "factcheck": lambda: step_factcheck(root_id),
                "audio":     lambda: step_audio(root_id),
                "merge":     lambda: step_merge(root_id),
                "deploy":    lambda: step_deploy(root_id),
            }[args.step]()
        else:
            ps.start(total_steps=5, description=f"kioku: {root_id} 語根追加")
            try:
                ps.update(1, f"generate ({root_id})")
                step_generate(root_id)
                ps.update(2, "factcheck (claude -p)")
                step_factcheck(root_id)
                ps.update(3, "audio (Edge TTS)")
                step_audio(root_id)
                ps.update(4, "merge → data/words/")
                step_merge(root_id)
                if not args.dry_run:
                    ps.update(5, "git push")
                    step_deploy(root_id)
                    ps.done(success=True, message=f"{root_id} 完了")
                else:
                    log(f"\n  [dry-run] デプロイをスキップ", YELLOW)
                    ps.done(success=True, message="dry-run完了")
            except SystemExit as e:
                ps.done(success=(e.code == 0), message=f"exit {e.code}")
                raise

        log(f"\n{'═'*60}", GREEN)
        log(f"  {root_id} 完了！", GREEN)
        log(f"{'═'*60}\n", GREEN)


if __name__ == "__main__":
    main()
