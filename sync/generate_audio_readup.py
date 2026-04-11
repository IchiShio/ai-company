"""
ReadUp Graded Series (stories.js) から音声・タイミングデータを一括生成

Usage:
  python3 generate_audio_readup.py          # 全記事を生成
  python3 generate_audio_readup.py vl2000   # VLレベル指定
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
STORIES_JS = os.path.join(os.path.dirname(__file__), "../reading/series/stories.js")


def load_stories(js_path: str) -> list:
    """stories.js から全ストーリーを抽出（id・vl・body）"""
    with open(js_path, encoding="utf-8") as f:
        content = f.read()
    # JSON部分を抽出してパース
    m = re.search(r'const STORIES\s*=\s*(\[.*\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        raise ValueError("stories.js から STORIES 配列を抽出できませんでした")
    return json.loads(m.group(1))


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


async def generate_audio(story_id: str, text: str, voice: str, skip_existing: bool = False) -> bool:
    mp3_path = os.path.join(AUDIO_DIR, f"{story_id}.mp3")
    json_path = os.path.join(AUDIO_DIR, f"{story_id}.json")

    if skip_existing and os.path.exists(mp3_path) and os.path.exists(json_path):
        return False

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

    target_vl = None
    skip_existing = "--skip" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("vl"):
            target_vl = arg

    print("stories.js 読み込み中...")
    stories = load_stories(STORIES_JS)

    # VLレベル別に整理（id順でソート）
    levels = {}
    for s in stories:
        vl = s.get("vl", "unknown")
        if target_vl and vl != target_vl:
            continue
        levels.setdefault(vl, []).append(s)
    for vl in levels:
        levels[vl].sort(key=lambda x: x["id"])

    total_generated = 0
    total_skipped = 0

    for vl in sorted(levels.keys()):
        items = levels[vl]
        print(f"\n── {vl} ({len(items)}本) ──")
        for i, story in enumerate(items):
            story_id = story["id"]
            text = story.get("body", "")
            if not text:
                print(f"  [{i+1:3d}/{len(items)}] ⚠ {story_id} (body なし、スキップ)")
                continue
            words = len(text.split())
            voice = VOICES[i % len(VOICES)]
            generated = await generate_audio(story_id, text, voice, skip_existing)
            if generated:
                print(f"  [{i+1:3d}/{len(items)}] ✓ {story_id}  {voice}  ({words}語)", flush=True)
                total_generated += 1
            else:
                print(f"  [{i+1:3d}/{len(items)}] - {story_id} (スキップ)", flush=True)
                total_skipped += 1

    print(f"\n✅ 完了: 生成 {total_generated}本 / スキップ {total_skipped}本")


if __name__ == "__main__":
    asyncio.run(main())
