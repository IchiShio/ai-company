#!/usr/bin/env python3
"""
Generate phoneme MP3 files using Google Cloud TTS REST API + SSML <phoneme> tags.
Output: phonics/audio/phoneme_{a-z}.mp3

Usage:
    python3 scripts/generate_phonics_phonemes.py

Requires:
    GOOGLE_CLOUD_API_KEY in .env (Google Cloud TTS API enabled)
"""
import asyncio
import base64
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

API_KEY = os.environ.get("GOOGLE_CLOUD_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_CLOUD_API_KEY not found in .env")
    sys.exit(1)

URL = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}"
OUT_DIR = os.path.join(os.path.dirname(__file__), "../phonics/audio")

# Letter → IPA phoneme mapping (short/consonant sounds for phonics)
PHONEME_MAP = {
    'a': 'æ',    # cat
    'b': 'b',    # bat
    'c': 'k',    # cat
    'd': 'd',    # dog
    'e': 'ɛ',    # bed
    'f': 'f',    # fox
    'g': 'ɡ',    # go
    'h': 'h',    # hat
    'i': 'ɪ',    # it
    'j': 'dʒ',   # jam
    'k': 'k',    # kit
    'l': 'l',    # lip
    'm': 'm',    # man
    'n': 'n',    # net
    'o': 'ɒ',    # on
    'p': 'p',    # pan
    'q': 'kw',   # quit
    'r': 'r',    # run
    's': 's',    # sun
    't': 't',    # tap
    'u': 'ʌ',    # up
    'v': 'v',    # van
    'w': 'w',    # wet
    'x': 'ks',   # fox
    'y': 'j',    # yes
    'z': 'z',    # zip
}


def generate_phoneme(letter: str, ipa: str, force: bool = False) -> bool:
    filename = f"phoneme_{letter}.mp3"
    path = os.path.join(OUT_DIR, filename)
    if not force and os.path.exists(path):
        print(f"  skip  {filename}")
        return True

    ssml = f'<speak><phoneme alphabet="ipa" ph="{ipa}">{letter}</phoneme></speak>'
    payload = {
        "input": {"ssml": ssml},
        "voice": {"languageCode": "en-US", "name": "en-US-Neural2-F"},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.85},
    }
    resp = requests.post(URL, json=payload)
    if resp.status_code != 200:
        print(f"  ERROR {filename}: {resp.status_code} {resp.text[:200]}")
        return False

    audio_content = base64.b64decode(resp.json()["audioContent"])
    with open(path, "wb") as f:
        f.write(audio_content)
    print(f"  gen   {filename}  /{ ipa }/")
    return True


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating {len(PHONEME_MAP)} phoneme files → {OUT_DIR}\n")

    ok = err = 0
    for letter, ipa in PHONEME_MAP.items():
        if generate_phoneme(letter, ipa, force):
            ok += 1
        else:
            err += 1

    print(f"\nDone. {ok} generated, {err} errors.")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
