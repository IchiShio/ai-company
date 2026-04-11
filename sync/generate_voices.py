#!/usr/bin/env python3
"""
SyncReader 音声ファイルを6種の音声（US/GB/AU × 男女）でバランスよく再生成するスクリプト。

Usage:
  python3 generate_voices.py          # 全200本を再生成
  python3 generate_voices.py arts_01  # 特定1本のみ再生成
  python3 generate_voices.py --dry-run  # 割り当て確認のみ（生成なし）
"""

import asyncio
import json
import os
import re
import sys

import edge_tts

# ─── 音声設定 ──────────────────────────────────────────────────────────────────
# 米（US）/ 英（GB）/ 豪（AU）の男女6種。アクセントと性別がバランスよく分散されるよう選定。
VOICES = [
    "en-US-AriaNeural",     # 0: US 女性
    "en-US-GuyNeural",      # 1: US 男性
    "en-GB-SoniaNeural",    # 2: GB 女性
    "en-GB-RyanNeural",     # 3: GB 男性
    "en-AU-NatashaNeural",  # 4: AU 女性
    "en-AU-WilliamNeural",  # 5: AU 男性
]

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
PASSAGES_TS = os.path.join(os.path.dirname(__file__), "../sync-src/src/passages.ts")


# ─── passages.ts から全パッセージを抽出 ────────────────────────────────────────
def load_passages() -> list[dict]:
    with open(PASSAGES_TS, encoding="utf-8") as f:
        ts = f.read()
    pattern = r'\{pid:"([^"]+)",wc:(\d+),text:"([^"]*)"'
    passages = []
    for m in re.finditer(pattern, ts):
        passages.append({"pid": m.group(1), "text": m.group(3)})
    return passages


def assign_voices(passages: list[dict]) -> list[tuple[dict, str]]:
    """pid をソートしてラウンドロビンで6種の音声を割り当てる。"""
    sorted_passages = sorted(passages, key=lambda p: p["pid"])
    return [(p, VOICES[i % len(VOICES)]) for i, p in enumerate(sorted_passages)]


# ─── タイミング推定 ────────────────────────────────────────────────────────────
def estimate_word_timings(text: str, sentences: list[dict]) -> list[dict]:
    all_words = re.findall(r"\S+", text)
    result = []
    word_idx = 0

    for sent in sentences:
        sent_text = sent["text"]
        sent_start = sent["start"]
        sent_dur = sent["duration"]
        sent_words = re.findall(r"\S+", sent_text)
        if not sent_words:
            continue

        clean_lens = [len(re.sub(r"[^\w]", "", w)) or 1 for w in sent_words]
        total_chars = sum(clean_lens)
        current = sent_start + 0.05
        remaining = sent_dur - 0.05

        for i, (w, cl) in enumerate(zip(sent_words, clean_lens)):
            ratio = cl / total_chars
            dur = remaining * ratio
            end_t = sent_start + sent_dur if i == len(sent_words) - 1 else round(current + dur, 3)
            result.append({"word": w, "start": round(current, 3), "end": end_t})
            current = end_t
            word_idx += 1

    return result


# ─── 1パッセージの生成 ─────────────────────────────────────────────────────────
async def generate_passage(pid: str, text: str, voice: str) -> None:
    mp3_path = os.path.join(AUDIO_DIR, f"{pid}.mp3")
    json_path = os.path.join(AUDIO_DIR, f"{pid}.json")

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
                "duration": round(chunk["duration"] / 10_000_000, 3),
            })

    with open(mp3_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    timings = estimate_word_timings(text, sentences)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False)

    dur = (sentences[-1]["start"] + sentences[-1]["duration"]) if sentences else 0
    print(f"  ✓ {pid:15s}  {voice:30s}  {len(timings):3d}語  {dur:.1f}秒")


# ─── メイン ────────────────────────────────────────────────────────────────────
async def main() -> None:
    target = None
    dry_run = False
    skip_existing = False

    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--skip-existing":
            skip_existing = True
        else:
            target = arg

    passages = load_passages()
    assigned = assign_voices(passages)
    print(f"全 {len(assigned)} パッセージの音声割り当て:")

    # 割り当てサマリーを表示
    voice_counts: dict[str, int] = {}
    for _, v in assigned:
        voice_counts[v] = voice_counts.get(v, 0) + 1
    for v, c in sorted(voice_counts.items()):
        print(f"  {v}: {c}本")
    print()

    if dry_run:
        print("--- dry-run: 生成は行いません ---")
        for p, v in assigned:
            print(f"  {p['pid']:15s} → {v}")
        return

    os.makedirs(AUDIO_DIR, exist_ok=True)
    count = 0
    skipped = 0
    for p, voice in assigned:
        pid = p["pid"]
        if target and pid != target:
            continue
        if skip_existing:
            mp3 = os.path.join(AUDIO_DIR, f"{pid}.mp3")
            jsn = os.path.join(AUDIO_DIR, f"{pid}.json")
            if os.path.exists(mp3) and os.path.exists(jsn):
                skipped += 1
                continue
        await generate_passage(pid, p["text"], voice)
        count += 1

    if skipped:
        print(f"  ⏭  {skipped}本スキップ（既存ファイルあり）")

    print(f"\n✅ {count}本 生成完了")


if __name__ == "__main__":
    asyncio.run(main())
