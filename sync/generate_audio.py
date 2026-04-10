"""
SyncReader 音声・タイミングデータ生成スクリプト

Usage:
  python3 generate_audio.py              # 全パッセージを生成
  python3 generate_audio.py lv1_0        # 特定のパッセージのみ再生成
"""

import asyncio
import json
import os
import re
import sys
import edge_tts

VOICE = "en-US-JennyNeural"
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
PASSAGES_FILE = os.path.join(os.path.dirname(__file__), "passages.json")

# ──────────────────────────────────────────────
# PASSAGES DATA
# ──────────────────────────────────────────────
PASSAGES = {
    1: [
        {
            "title": "Morning Routine",
            "text": "Every morning, I wake up at seven. I make a cup of coffee and sit by the window. The city is quiet in the early hours. I check my phone and read the news. Then I get ready for work. It is a simple routine, but it helps me start the day right."
        },
        {
            "title": "A Dog's Day",
            "text": "My dog loves to go for walks. We visit the park every evening after work. He runs and plays with other dogs along the way. I always bring water and a small snack for him. Watching him enjoy himself is the best part of my day."
        },
        {
            "title": "The Corner Café",
            "text": "She works at a small café near the station. She starts at eight in the morning and finishes at three. The café gets busy around lunchtime. Her favorite part of the job is talking to regular customers. After so many years there, she feels at home."
        },
        {
            "title": "First Snow",
            "text": "Snow fell overnight and covered everything in white. The streets were quiet and the air was cold. Children came out early to build snowmen in the park. Schools were closed for the day. It was the first real snow of the winter season."
        },
        {
            "title": "Weekend Market",
            "text": "The outdoor market opens every Saturday morning. Local farmers sell fresh vegetables and fruit. There are also stalls with bread, cheese, and flowers. Many families come here together each week. It is a great way to support local producers."
        },
    ],
    2: [
        {
            "title": "Working From Home",
            "text": "Working from home has changed how many people think about their daily routine. Without a commute, they have more time for themselves. However, the line between work and personal life can easily blur. Setting a clear schedule helps a great deal. So does having a dedicated workspace, even a small corner of a room."
        },
        {
            "title": "Learning a Language",
            "text": "Learning a new language takes time and patience. Many people give up too soon, expecting results within a few weeks. The key is to practice a little every single day. Even fifteen minutes of focused study makes a real difference. Over time, those small daily steps add up to remarkable progress."
        },
        {
            "title": "Online Shopping",
            "text": "Online shopping has become a normal part of life for millions of people worldwide. It saves time and offers far more choices than any physical store could. However, it also has real drawbacks. You cannot try items before buying, and returns can be slow and complicated. Many shoppers are finding a balance between online and in-store purchasing."
        },
        {
            "title": "The Value of Sleep",
            "text": "Most adults need between seven and nine hours of sleep each night. Yet many people regularly get far less than that. Lack of sleep affects concentration, mood, and long-term health in serious ways. Simple habits like going to bed at the same time each night can make a big difference. Small changes in routine often lead to better rest."
        },
        {
            "title": "City Cycling",
            "text": "More cities around the world are building dedicated cycling lanes to encourage people to ride bikes. Cycling reduces traffic congestion and cuts carbon emissions significantly. It is also better for personal health than sitting in a car. However, safety remains a key concern for many potential riders. Better infrastructure is needed to make cycling a realistic option for everyone."
        },
    ],
    3: [
        {
            "title": "AI and the Workforce",
            "text": "The rapid development of artificial intelligence is reshaping industries at an unprecedented pace. Tasks that once required years of specialized training are now being automated with increasing accuracy. While this technological shift creates new categories of work, it also raises legitimate concerns about job displacement. Workers who proactively develop new skills will likely hold a significant advantage in the changing labor market. Organizations that invest in retraining their employees now are better positioned for long-term success."
        },
        {
            "title": "Remote Work Migration",
            "text": "Remote work has fundamentally altered the relationship between employees and the organizations they work for. Companies are reconsidering their office space requirements, while workers are reassessing where they want to live and raise families. This shift has accelerated a notable migration from expensive major cities to smaller regional towns. The long-term effects on urban real estate, local economies, and public infrastructure remain complex and deeply uncertain."
        },
        {
            "title": "The Science of Habit",
            "text": "Research in behavioral psychology suggests that habits are formed through a cycle of cue, routine, and reward. Once a behavior becomes automatic through repetition, the brain requires significantly less conscious effort to perform it. This efficiency is useful, but it also means that harmful habits can be difficult to break once they are established. Replacing an existing habit with a new one, rather than attempting to eliminate it entirely, is often a more effective long-term strategy for behavioral change."
        },
        {
            "title": "Climate and Food Supply",
            "text": "Climate change is increasingly affecting global food production in ways that researchers are only beginning to fully understand. Shifting rainfall patterns and rising average temperatures are reducing crop yields in vulnerable regions across Africa and Asia. Meanwhile, extreme weather events are disrupting supply chains that the modern food system depends on. International cooperation on agricultural adaptation and food security will be essential in the decades ahead, as the window for preventive action continues to narrow."
        },
        {
            "title": "The Value of Deep Work",
            "text": "Cognitive scientists distinguish between shallow work, such as answering emails, and deep work, which involves intense concentration on cognitively demanding tasks. The ability to focus deeply for extended periods is becoming increasingly rare in a world of constant digital interruption, yet it is simultaneously more economically valuable. Individuals who cultivate the discipline to engage in sustained, distraction-free concentration are producing the kind of complex, high-quality output that is genuinely difficult to replicate or automate."
        },
    ]
}


def estimate_word_timings(text: str, sentences: list[dict]) -> list[dict]:
    """
    SentenceBoundaryの時間情報と文字数比率から単語ごとのタイミングを推定する。

    Returns: [{"word": str, "start": float, "end": float}, ...]
    """
    # 全テキストをトークン分割（単語 + 区切り文字）
    all_words = re.findall(r'\S+', text)
    word_index = 0
    result = []

    for sent in sentences:
        sent_text = sent["text"]
        sent_start = sent["start"]
        sent_dur = sent["duration"]

        # この文に含まれる単語を抽出
        sent_words = re.findall(r'\S+', sent_text)
        if not sent_words:
            continue

        # 文字数（句読点除く）ベースで各単語の比率を計算
        clean_lens = [len(re.sub(r'[^\w]', '', w)) or 1 for w in sent_words]
        total_chars = sum(clean_lens)

        # 先頭に小さなポーズを入れる（50ms）
        current = sent_start + 0.05
        remaining_dur = sent_dur - 0.05

        for i, (w, cl) in enumerate(zip(sent_words, clean_lens)):
            ratio = cl / total_chars
            duration = remaining_dur * ratio
            # 最後の単語は文の終端まで
            if i == len(sent_words) - 1:
                end_time = sent_start + sent_dur
            else:
                end_time = round(current + duration, 3)
            result.append({
                "word": w,
                "start": round(current, 3),
                "end": end_time
            })
            current = end_time

    return result


async def generate_passage(level: int, index: int, passage: dict) -> None:
    key = f"lv{level}_{index}"
    mp3_path = os.path.join(AUDIO_DIR, f"{key}.mp3")
    json_path = os.path.join(AUDIO_DIR, f"{key}.json")

    print(f"  生成中: {key} — {passage['title']}", flush=True)

    communicate = edge_tts.Communicate(passage["text"], VOICE)
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

    # MP3保存
    with open(mp3_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    # タイミングJSON保存
    timings = estimate_word_timings(passage["text"], sentences)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {key}: {len(timings)}語 / {sentences[-1]['start'] + sentences[-1]['duration']:.1f}秒", flush=True)


async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # フィルター（引数で特定キーのみ再生成可能）
    target = sys.argv[1] if len(sys.argv) > 1 else None

    for level, passages in PASSAGES.items():
        print(f"\n── Level {level} ──")
        for i, passage in enumerate(passages):
            key = f"lv{level}_{i}"
            if target and key != target:
                continue
            await generate_passage(level, i, passage)

    # passages.json を書き出し（フロントエンド用メタデータ）
    meta = {}
    for level, passages in PASSAGES.items():
        meta[str(level)] = [
            {"title": p["title"], "wordCount": len(re.findall(r'\S+', p["text"]))}
            for p in passages
        ]
    with open(PASSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\n✅ 全パッセージ生成完了")


if __name__ == "__main__":
    asyncio.run(main())
