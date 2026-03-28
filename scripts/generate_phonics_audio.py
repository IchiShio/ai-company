#!/usr/bin/env python3
"""
Generate MP3 audio files for phonics/index.html
Voice: en-US-AriaNeural (same as ListenUp)
Output: phonics/audio/{word}.mp3
"""
import asyncio
import os
import sys
import edge_tts

VOICE = "en-US-AriaNeural"
OUT_DIR = os.path.join(os.path.dirname(__file__), "../phonics/audio")

# All words needed by phonics/index.html
WORDS = sorted(set([
    # Single letters A-Z
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    # ALPHABET card words
    "apple", "ant", "cat", "ball", "bat", "bus", "cup", "car",
    "dog", "dad", "bed", "egg", "end", "fox", "fish", "off",
    "go", "get", "big", "hat", "hot", "him", "it", "ink",
    "jam", "jet", "job", "kit", "key", "sky", "lip", "let",
    "man", "map", "net", "nap", "ten", "ox", "on", "hot",
    "pan", "pet", "quit", "quiz", "queen", "run", "red", "far",
    "sun", "sit", "tap", "up", "us", "cut", "van", "vet", "give",
    "wet", "win", "way", "box", "mix", "yes", "yell", "yet",
    "zip", "zoo", "buzz",
    # CODE 01 - Silent K
    "knife", "know", "knock", "knee", "kneel",
    # CODE 02 - Silent W
    "write", "wrong", "wrap", "wrist", "wreck",
    # CODE 03 - Magic E
    "cape", "bite", "note", "cute", "ride",
    # CODE 04 - Soft C/G
    "city", "cycle", "giant", "gym", "gem",
    # CODE 05 - GH
    "light", "tough", "ghost", "night", "laugh",
    # CODE 06 - OO
    "moon", "book", "food", "foot", "cool",
    # CODE 07 - PH
    "phone", "photo", "graph", "phrase", "physics",
    # CODE 08 - -TION
    "nation", "station", "action", "fiction", "passion",
    # CODE 09 - -ED
    "walked", "played", "wanted", "jumped", "lived",
    # CODE 10 - Silent letters
    "island", "debt", "receipt", "scissors", "wednesday",
]))


async def generate(word: str, force: bool = False):
    filename = word.lower().replace(" ", "_") + ".mp3"
    path = os.path.join(OUT_DIR, filename)
    if not force and os.path.exists(path):
        print(f"  skip  {filename}")
        return
    communicate = edge_tts.Communicate(word, VOICE)
    await communicate.save(path)
    print(f"  gen   {filename}")


async def main():
    force = "--force" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating {len(WORDS)} audio files → {OUT_DIR}")
    print(f"Voice: {VOICE}\n")
    tasks = [generate(w, force) for w in WORDS]
    await asyncio.gather(*tasks)
    print(f"\nDone. {len(WORDS)} files.")


if __name__ == "__main__":
    asyncio.run(main())
