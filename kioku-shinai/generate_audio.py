#!/usr/bin/env python3
"""
記憶しない英単語 — Edge TTS 音声生成（native-real版）
語根グループJSONから各単語のword.mp3を生成する。
"""
import asyncio
import json
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("pip install edge-tts --break-system-packages")
    sys.exit(1)

VOICES = [
    "en-US-ChristopherNeural",
    "en-US-JennyNeural",
    "en-GB-RyanNeural",
    "en-GB-SoniaNeural",
    "en-AU-WilliamMultilingualNeural",
    "en-AU-NatashaNeural",
]

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "words"
AUDIO_DIR = ROOT / "audio"


async def gen(text, voice, path):
    c = edge_tts.Communicate(text, voice)
    await c.save(str(path))


async def main():
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("No JSON files found")
        return

    vi = 0
    total_new = 0
    for jf in files:
        data = json.load(open(jf))
        root_name = data["root"]
        for w in data["words"]:
            word = w["word"]
            d = AUDIO_DIR / word
            d.mkdir(parents=True, exist_ok=True)
            mp3 = d / "word.mp3"
            if mp3.exists():
                vi += 1
                continue
            voice = VOICES[vi % len(VOICES)]
            vi += 1
            try:
                await gen(word, voice, mp3)
                print(f"  {word} -> {voice}")
                total_new += 1
            except Exception as e:
                print(f"  ERROR {word}: {e}")

    print(f"\nDone. {total_new} new files generated.")
    print(f"Total audio dirs: {len(list(AUDIO_DIR.iterdir()))}")


if __name__ == "__main__":
    asyncio.run(main())
