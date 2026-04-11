"""
ReadUpパッセージからSyncReader用音声・タイミングデータを一括生成

Usage:
  python3 generate_audio_readup.py          # 全200本生成
  python3 generate_audio_readup.py lv1      # Level 1のみ
  python3 generate_audio_readup.py --skip   # 既存ファイルをスキップ
"""

import asyncio
import json
import os
import re
import sys
import edge_tts

# 米（US）/ 英（GB）/ 豪（AU）の男女6種をラウンドロビンで割り当て
VOICES = [
    "en-US-AriaNeural",     # 0: US 女性
    "en-US-GuyNeural",      # 1: US 男性
    "en-GB-SoniaNeural",    # 2: GB 女性
    "en-GB-RyanNeural",     # 3: GB 男性
    "en-AU-NatashaNeural",  # 4: AU 女性
    "en-AU-WilliamNeural",  # 5: AU 男性
]
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
READUP_JS = os.path.join(os.path.dirname(__file__), "../reading/questions.js")
PASSAGES_JSON = os.path.join(os.path.dirname(__file__), "passages_readup.json")


def extract_readup_passages(js_path: str) -> dict:
    """questions.jsからユニークパッセージを抽出してレベル別に整理"""
    with open(js_path, encoding="utf-8") as f:
        content = f.read()

    pattern = r'\{\s*id:"([^"]+)",\s*pid:"([^"]+)",\s*diff:"([^"]+)",\s*axis:"[^"]+",\s*passage:"([^"]+)"'
    matches = re.findall(pattern, content)

    seen_pids = {}
    for _, pid, diff, passage in matches:
        if pid not in seen_pids:
            seen_pids[pid] = {"pid": pid, "diff": diff, "passage": passage}

    # レベル別に整理
    levels = {"lv1": [], "lv2": [], "lv3": [], "lv4": [], "lv5": []}
    for item in seen_pids.values():
        lv = item["diff"]
        if lv in levels:
            levels[lv].append(item)

    # 各レベルをpid順でソート
    for lv in levels:
        levels[lv].sort(key=lambda x: x["pid"])

    return levels


def estimate_word_timings(text: str, sentences: list) -> list:
    """SentenceBoundary情報 + 文字数比率で単語タイミングを推定"""
    result = []

    for sent in sentences:
        sent_words = re.findall(r'\S+', sent["text"])
        if not sent_words:
            continue

        clean_lens = [len(re.sub(r'[^\w]', '', w)) or 1 for w in sent_words]
        total_chars = sum(clean_lens)
        current = sent["start"] + 0.05
        remaining_dur = sent["duration"] - 0.05

        for i, (w, cl) in enumerate(zip(sent_words, clean_lens)):
            ratio = cl / total_chars
            if i == len(sent_words) - 1:
                end_time = sent["start"] + sent["duration"]
            else:
                end_time = round(current + remaining_dur * ratio, 3)
            result.append({"word": w, "start": round(current, 3), "end": end_time})
            current = end_time

    return result


async def generate_passage_audio(pid: str, text: str, voice: str, skip_existing: bool = False) -> bool:
    mp3_path = os.path.join(AUDIO_DIR, f"{pid}.mp3")
    json_path = os.path.join(AUDIO_DIR, f"{pid}.json")

    if skip_existing and os.path.exists(mp3_path) and os.path.exists(json_path):
        return False  # スキップ

    communicate = edge_tts.Communicate(text, voice)
    sentences = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "SentenceBoundary":
            sentences.append({
                "text": chunk["text"],
                "start": round(chunk["offset"] / 10_000_000, 3),
                "duration": round(chunk["duration"] / 10_000_000, 3)
            })

    with open(mp3_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    timings = estimate_word_timings(text, sentences)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False)

    return True


async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    target_lv = None
    skip_existing = "--skip" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("lv"):
            target_lv = arg

    print(f"ReadUpパッセージ抽出中...")
    levels = extract_readup_passages(READUP_JS)

    # passages_readup.json（フロントエンド用メタデータ）を生成
    meta = {}
    for lv, items in levels.items():
        meta[lv] = [
            {
                "pid": item["pid"],
                "wordCount": len(item["passage"].split())
            }
            for item in items
        ]
    with open(PASSAGES_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    total_generated = 0
    total_skipped = 0

    for lv, items in levels.items():
        if target_lv and lv != target_lv:
            continue

        print(f"\n── {lv} ({len(items)}本) ──")
        for i, item in enumerate(items):
            pid = item["pid"]
            text = item["passage"]
            words = len(text.split())
            voice = VOICES[i % len(VOICES)]
            generated = await generate_passage_audio(pid, text, voice, skip_existing)
            if generated:
                print(f"  [{i+1:3d}/{len(items)}] ✓ {pid}  {voice}  ({words}語)", flush=True)
                total_generated += 1
            else:
                print(f"  [{i+1:3d}/{len(items)}] - {pid} (スキップ)", flush=True)
                total_skipped += 1

    print(f"\n✅ 完了: 生成 {total_generated}本 / スキップ {total_skipped}本")


if __name__ == "__main__":
    asyncio.run(main())
