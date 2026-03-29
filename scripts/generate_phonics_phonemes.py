#!/usr/bin/env python3
"""
Generate phoneme MP3 files using Google Cloud TTS REST API.

母音: SSML <phoneme alphabet="ipa"> タグ（精度高）
子音: 直接テキスト（"buh", "yuh" など）でTTSが正確に発音

Output: phonics/audio/phoneme_{a-z}.mp3

Usage:
    python3 scripts/generate_phonics_phonemes.py           # skip existing
    python3 scripts/generate_phonics_phonemes.py --force   # regenerate all
"""
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

# letter → (input_type, value)
# input_type: "ssml" = IPA phoneme tag, "text" = plain text
PHONEME_MAP = {
    # 母音: IPA SSML で正確に
    'a': ('ssml', 'æ'),    # /æ/ cat
    'e': ('ssml', 'ɛ'),    # /ɛ/ bed
    'i': ('ssml', 'ɪ'),    # /ɪ/ it
    'o': ('ssml', 'ɒ'),    # /ɒ/ on
    'u': ('ssml', 'ʌ'),    # /ʌ/ up
    # 子音: 直接テキスト（シュワ付き）でTTSが自然に発音
    'b': ('text', 'buh'),
    'c': ('text', 'kuh'),
    'd': ('text', 'duh'),
    'f': ('text', 'fff'),
    'g': ('text', 'guh'),
    'h': ('text', 'huh'),
    'j': ('text', 'juh'),
    'k': ('text', 'kuh'),
    'l': ('text', 'lll'),
    'm': ('text', 'mmm'),
    'n': ('text', 'nnn'),
    'p': ('text', 'puh'),
    'q': ('text', 'kwuh'),
    'r': ('text', 'rrr'),
    's': ('text', 'sss'),
    't': ('text', 'tuh'),
    'v': ('text', 'vvv'),
    'w': ('text', 'wuh'),
    'x': ('text', 'ks'),
    'y': ('text', 'yuh'),   # /j/ — NOT letter name "wai"
    'z': ('text', 'zzz'),
}


def build_payload(input_type: str, value: str) -> dict:
    if input_type == 'ssml':
        # IPA phoneme tag: display text is a neutral word so TTS doesn't fall back to letter name
        ssml = f'<speak><phoneme alphabet="ipa" ph="{value}">sound</phoneme></speak>'
        return {"input": {"ssml": ssml}}
    else:
        return {"input": {"text": value}}


def generate_phoneme(letter: str, input_type: str, value: str, force: bool = False) -> bool:
    filename = f"phoneme_{letter}.mp3"
    path = os.path.join(OUT_DIR, filename)
    if not force and os.path.exists(path):
        print(f"  skip  {filename}")
        return True

    payload = build_payload(input_type, value)
    payload["voice"] = {"languageCode": "en-US", "name": "en-US-Neural2-F"}
    payload["audioConfig"] = {"audioEncoding": "MP3", "speakingRate": 0.85}

    resp = requests.post(URL, json=payload)
    if resp.status_code != 200:
        print(f"  ERROR {filename}: {resp.status_code} {resp.text[:200]}")
        return False

    audio_content = base64.b64decode(resp.json()["audioContent"])
    with open(path, "wb") as f:
        f.write(audio_content)
    label = f'IPA /{value}/' if input_type == 'ssml' else f'text "{value}"'
    print(f"  gen   {filename}  {label}")
    return True


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating {len(PHONEME_MAP)} phoneme files → {OUT_DIR}\n")

    ok = err = 0
    for letter, (input_type, value) in PHONEME_MAP.items():
        if generate_phoneme(letter, input_type, value, force):
            ok += 1
        else:
            err += 1

    print(f"\nDone. {ok} generated, {err} errors.")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
