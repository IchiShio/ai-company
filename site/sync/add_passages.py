#!/usr/bin/env python3
"""
staging.json を passages.ts に追記し、音声生成・ビルド・git push まで一括実行。

Usage:
  python3 add_passages.py               # sync/staging.json を処理
  python3 add_passages.py my_output.json
  python3 add_passages.py --dry-run     # 変更確認のみ（ファイル更新なし）
"""

import json
import os
import re
import subprocess
import sys

SYNC_DIR      = os.path.dirname(os.path.abspath(__file__))
PASSAGES_TS   = os.path.join(SYNC_DIR, "../sync-src/src/passages.ts")
SYNC_SRC_DIR  = os.path.join(SYNC_DIR, "../sync-src")
STAGING_JSON  = os.path.join(SYNC_DIR, "staging.json")
AUDIO_DIR     = os.path.join(SYNC_DIR, "audio")

LEVELS = ["lv1", "lv2", "lv3", "lv4", "lv5"]


# ─── ユーティリティ ──────────────────────────────────────────────────────────

def load_existing_pids(ts: str) -> set[str]:
    return set(re.findall(r'pid:"([^"]+)"', ts))


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def escape_ts(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def format_entry(pid: str, wc: int, text: str, ja: str) -> str:
    return f'{{pid:"{pid}",wc:{wc},text:"{escape_ts(text)}",ja:"{escape_ts(ja)}"}}'


def insert_into_level(content: str, level: str, entries: list[str]) -> str:
    """passages.ts の指定レベルの末尾に entries を追記する"""
    lines = content.split("\n")
    in_target = False
    insert_at = -1

    for i, line in enumerate(lines):
        if f'"{level}": [' in line:
            in_target = True
        elif in_target and line.strip() == "],":
            insert_at = i
            break

    if insert_at == -1:
        raise ValueError(f"Level '{level}' が passages.ts 内に見つかりません")

    for j, entry in enumerate(entries):
        lines.insert(insert_at + j, f"    {entry},")

    return "\n".join(lines)


# ─── メイン ─────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv
    staging_path = STAGING_JSON
    for arg in sys.argv[1:]:
        if not arg.startswith("--") and arg.endswith(".json"):
            staging_path = arg

    # staging.json 読み込み
    if not os.path.exists(staging_path):
        print(f"❌ {staging_path} が見つかりません")
        print("   python3 get_prompt.py --level lv1 --count 20 でプロンプトを生成してください")
        sys.exit(1)

    with open(staging_path, encoding="utf-8") as f:
        raw = f.read().strip()

    # JSON を抽出（コードブロック対応）
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    # 先頭の [ から末尾の ] まで抽出
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        print("❌ staging.json から JSON 配列を抽出できませんでした")
        sys.exit(1)
    passages = json.loads(m.group(0))

    # passages.ts 読み込み
    with open(PASSAGES_TS, encoding="utf-8") as f:
        ts = f.read()

    existing_pids = load_existing_pids(ts)

    # バリデーション
    errors = []
    new_by_level: dict[str, list] = {lv: [] for lv in LEVELS}
    new_pids = set()

    for p in passages:
        pid   = p.get("pid", "")
        level = p.get("level", "")
        text  = p.get("text", "")
        ja    = p.get("ja", "")

        if not pid:
            errors.append("pid が空のエントリがあります")
        elif pid in existing_pids:
            errors.append(f"pid '{pid}' は既に存在します（スキップ）")
        elif pid in new_pids:
            errors.append(f"pid '{pid}' が staging 内で重複しています")
        elif level not in LEVELS:
            errors.append(f"'{pid}': level='{level}' が無効です（lv1〜lv5）")
        elif not text:
            errors.append(f"'{pid}': text が空です")
        elif not ja:
            errors.append(f"'{pid}': ja が空です")
        else:
            new_by_level[level].append({"pid": pid, "text": text, "ja": ja})
            new_pids.add(pid)

    total_new = sum(len(v) for v in new_by_level.values())

    # サマリー表示
    print(f"staging.json: {len(passages)} エントリ読み込み")
    for lv in LEVELS:
        if new_by_level[lv]:
            print(f"  {lv}: {len(new_by_level[lv])}本")
    if errors:
        print("\n⚠️  警告:")
        for e in errors:
            print(f"  {e}")
    if total_new == 0:
        print("\n追加する新規パッセージがありません")
        sys.exit(0)

    print(f"\n追加予定: {total_new}本")
    for lv in LEVELS:
        for p in new_by_level[lv]:
            wc = count_words(p["text"])
            print(f"  {p['pid']:15s}  {lv}  {wc}語  {p['text'][:40]}...")

    if dry_run:
        print("\n--- dry-run: 変更は行いません ---")
        return

    # passages.ts に追記
    updated_ts = ts
    for lv in LEVELS:
        if not new_by_level[lv]:
            continue
        entries = [format_entry(p["pid"], count_words(p["text"]), p["text"], p["ja"])
                   for p in new_by_level[lv]]
        updated_ts = insert_into_level(updated_ts, lv, entries)

    with open(PASSAGES_TS, "w", encoding="utf-8") as f:
        f.write(updated_ts)
    print(f"\n✅ passages.ts を更新しました")

    # Vite ビルド
    print("⚙️  ビルド中...")
    result = subprocess.run(["npm", "run", "build"], cwd=SYNC_SRC_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ ビルド失敗:")
        print(result.stderr)
        sys.exit(1)
    print("✅ ビルド完了")

    # 音声生成（新規分のみ）
    print("🔊 音声生成中（新規分のみ）...")
    import asyncio
    import edge_tts

    # generate_voices.py のロジックを再利用
    generate_py = os.path.join(SYNC_DIR, "generate_voices.py")
    pids_to_generate = list(new_pids)
    for pid in pids_to_generate:
        result = subprocess.run(
            ["python3", generate_py, pid],
            cwd=SYNC_DIR,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ❌ {pid}: {result.stderr.strip()}")
        else:
            print(result.stdout.strip())

    # git commit & push
    print("\n📦 Git コミット中...")
    repo_root = os.path.join(SYNC_DIR, "..")
    cmds = [
        ["git", "add",
         "sync/assets/", "sync/index.html",
         "sync-src/src/passages.ts",
         f"sync/audio/"],
        ["git", "commit", "-m",
         f"sync: パッセージ {total_new}本追加（{'・'.join(lv for lv in LEVELS if new_by_level[lv])}）"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=repo_root)
        if r.returncode != 0:
            print(f"❌ {' '.join(cmd)} が失敗しました")
            sys.exit(1)

    print(f"\n🎉 完了！ {total_new}本を追加・デプロイしました")


if __name__ == "__main__":
    main()
