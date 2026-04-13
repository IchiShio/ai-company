#!/usr/bin/env python3
"""
edge-tts で瞬間英作文の音声MP3を一括生成
イントネーション制御:
  疑問文 (?)  → pitch +15%  rate -8%  (上昇調)
  感嘆文 (!)  → pitch +8%   rate +0%
  平叙文 (.)  → pitch +0%   rate -5%  (下降調・自然)

使い方:
  python3 gen_audio.py          # 未生成のみ生成
  python3 gen_audio.py --all    # 全ファイル再生成（イントネーション適用）
"""
import asyncio
import re
import sys
from pathlib import Path

import edge_tts

VOICES = [
    ("en-US-AvaNeural",                  "🇺🇸", "US", "♀"),
    ("en-GB-RyanNeural",                 "🇬🇧", "UK", "♂"),
    ("en-US-GuyNeural",                  "🇺🇸", "US", "♂"),
    ("en-AU-NatashaNeural",              "🇦🇺", "AU", "♀"),
    ("en-GB-SoniaNeural",                "🇬🇧", "UK", "♀"),
    ("en-AU-WilliamMultilingualNeural",  "🇦🇺", "AU", "♂"),
]

HTML_PATH = Path(__file__).parent / "index.html"
AUDIO_DIR = Path(__file__).parent / "audio"


WH_WORDS = re.compile(r'^(what|where|when|who|whom|whose|which|why|how)\b', re.IGNORECASE)


def get_intonation(text: str) -> tuple[str, str]:
    """文末記号とWh語からイントネーション(pitch Hz, rate)を返す
    edge-tts の pitch は ±NHz 形式
    - Yes/No疑問文 (?)  → pitch +20Hz  rate -8%  (上昇調 ↗)
    - Wh疑問文    (?)  → pitch +0Hz   rate -5%  (下降調 ↘ ネイティブ自然)
    - 感嘆文      (!)  → pitch +10Hz  rate +0%
    - 平叙文      (.)  → pitch +0Hz   rate -5%  (下降調)
    """
    t = text.strip()
    if t.endswith("?"):
        if WH_WORDS.match(t):
            return ("+0Hz",  "-5%")   # Wh疑問文: 下降調（ネイティブ自然）
        else:
            return ("+20Hz", "-8%")   # Yes/No疑問文: 上昇調
    elif t.endswith("!"):
        return ("+10Hz", "+0%")       # 感嘆文: やや高め
    else:
        return ("+0Hz",  "-5%")       # 平叙文: 自然な下降調


def extract_mains(html: str) -> list[str]:
    return re.findall(r'main:"((?:[^"\\]|\\.)*)"', html)


async def gen_one(idx: int, text: str, out_path: Path):
    voice_name = VOICES[idx % len(VOICES)][0]
    pitch, rate = get_intonation(text)
    comm = edge_tts.Communicate(text, voice_name, pitch=pitch, rate=rate)
    await comm.save(str(out_path))


async def main():
    regen_all = "--all" in sys.argv
    AUDIO_DIR.mkdir(exist_ok=True)
    html = HTML_PATH.read_text(encoding="utf-8")
    mains = extract_mains(html)
    print(f"抽出: {len(mains)}問")

    tasks = []
    for i, text in enumerate(mains):
        out = AUDIO_DIR / f"q{i+1:03d}.mp3"
        if out.exists() and not regen_all:
            continue
        tasks.append((i, text, out))

    if not tasks:
        print("全ファイル生成済み。再生成するには --all を付けてください。")
        return

    q_count  = sum(1 for _, t, _ in tasks if t.strip().endswith("?"))
    ex_count = sum(1 for _, t, _ in tasks if t.strip().endswith("!"))
    st_count = len(tasks) - q_count - ex_count
    print(f"生成: {len(tasks)}ファイル  (疑問文:{q_count} / 感嘆文:{ex_count} / 平叙文:{st_count})")

    sem = asyncio.Semaphore(5)

    async def bounded(i, text, out):
        async with sem:
            await gen_one(i, text, out)
            v = VOICES[i % len(VOICES)]
            pitch, _ = get_intonation(text)
            tone = "↗" if text.strip().endswith("?") else ("↗↘" if text.strip().endswith("!") else "↘")
            print(f"  ✅ q{i+1:03d} {v[1]}{v[2]}{v[3]} {tone} pitch{pitch}  {text[:40]}")

    await asyncio.gather(*[bounded(i, t, o) for i, t, o in tasks])
    print(f"\n完了: {AUDIO_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
