#!/usr/bin/env python3
"""
edge-tts で瞬間英作文の音声MP3を一括生成
"""
import asyncio
import re
import sys
from pathlib import Path

import edge_tts

VOICES = [
    ("en-US-AvaNeural",             "🇺🇸", "US", "♀"),
    ("en-GB-RyanNeural",            "🇬🇧", "UK", "♂"),
    ("en-US-GuyNeural",             "🇺🇸", "US", "♂"),
    ("en-AU-NatashaNeural",         "🇦🇺", "AU", "♀"),
    ("en-GB-SoniaNeural",           "🇬🇧", "UK", "♀"),
    ("en-AU-WilliamMultilingualNeural", "🇦🇺", "AU", "♂"),
]

HTML_PATH  = Path(__file__).parent / "index.html"
AUDIO_DIR  = Path(__file__).parent / "audio"

def extract_mains(html: str) -> list[str]:
    return re.findall(r'main:"((?:[^"\\]|\\.)*)"', html)

async def gen_one(idx: int, text: str, out_path: Path):
    voice_name = VOICES[idx % len(VOICES)][0]
    comm = edge_tts.Communicate(text, voice_name, rate="-5%")
    await comm.save(str(out_path))

async def main():
    AUDIO_DIR.mkdir(exist_ok=True)
    html = HTML_PATH.read_text(encoding="utf-8")
    mains = extract_mains(html)
    print(f"抽出: {len(mains)}問")

    tasks = []
    for i, text in enumerate(mains):
        out = AUDIO_DIR / f"q{i+1:03d}.mp3"
        if out.exists():
            print(f"  skip q{i+1:03d} (already exists)")
            continue
        tasks.append((i, text, out))

    print(f"生成: {len(tasks)}ファイル")
    sem = asyncio.Semaphore(5)  # 並列5本

    async def bounded(i, text, out):
        async with sem:
            await gen_one(i, text, out)
            v = VOICES[i % len(VOICES)]
            print(f"  ✅ q{i+1:03d} {v[1]}{v[2]}{v[3]}  {text[:40]}")

    await asyncio.gather(*[bounded(i, t, o) for i, t, o in tasks])
    print(f"\n完了: {AUDIO_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
