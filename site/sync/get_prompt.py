#!/usr/bin/env python3
"""
SyncReader 新規パッセージ生成用プロンプトを作成し、クリップボードにコピーする。

Usage:
  python3 get_prompt.py --level lv1 --count 20
  python3 get_prompt.py --level lv2 --count 10
"""

import argparse
import os
import re
import subprocess

PASSAGES_TS = os.path.join(os.path.dirname(__file__), "../sync-src/src/passages.ts")

LEVEL_SPECS = {
    "lv1": {
        "wc": "25–45 words",
        "desc": "Very simple English. Short sentences. Basic everyday vocabulary only. Present or past tense. Easy enough for absolute beginners.",
    },
    "lv2": {
        "wc": "40–65 words",
        "desc": "Simple to intermediate. Clear sentence structure. Occasional common idioms. Suitable for elementary learners.",
    },
    "lv3": {
        "wc": "60–95 words",
        "desc": "Intermediate. Mix of simple and complex sentences. Some idioms and less common vocabulary. For intermediate learners.",
    },
    "lv4": {
        "wc": "85–120 words",
        "desc": "Upper-intermediate. Complex sentences. Nuanced vocabulary, phrasal verbs, idiomatic expressions. For advanced learners.",
    },
    "lv5": {
        "wc": "100–140 words",
        "desc": "Advanced. Sophisticated vocabulary and syntax. Dense information. Abstract ideas. For near-native learners.",
    },
}

EXISTING_TOPICS = [
    "arts", "biz", "comm", "daily", "edu", "env", "food", "global",
    "health", "hist", "life", "nature", "psych", "sci", "society",
    "sports", "tech", "travel", "urban", "work",
]

def load_existing_pids() -> set[str]:
    with open(PASSAGES_TS, encoding="utf-8") as f:
        ts = f.read()
    return set(re.findall(r'pid:"([^"]+)"', ts))


def make_prompt(level: str, count: int, existing_pids: set[str]) -> str:
    spec = LEVEL_SPECS[level]
    existing_str = ", ".join(sorted(existing_pids)[:30]) + ("..." if len(existing_pids) > 30 else "")

    # Suggest new topic names
    suggested = [
        "animals", "career", "cities", "climate", "culture", "design",
        "economy", "emotion", "energy", "family", "fashion", "film",
        "finance", "fitness", "friendship", "future", "games", "garden",
        "geography", "government", "habits", "housing", "innovation",
        "internet", "justice", "kids", "language", "law", "leadership",
        "media", "memory", "money", "music", "news", "ocean", "parenting",
        "pets", "philosophy", "politics", "reading", "relationships",
        "religion", "research", "robots", "safety", "school", "shopping",
        "sleep", "space", "stress", "time", "transport", "vegetables",
        "water", "weather", "wildlife", "writing",
    ]
    new_topics = [t for t in suggested if t not in EXISTING_TOPICS][:20]

    prompt = f"""You are writing English reading passages for a Japanese learner app called SyncReader.

## Level: {level.upper()}
- Word count: {spec["wc"]}
- Style: {spec["desc"]}

## Task
Generate exactly {count} new reading passages.

Rules:
1. Each passage must be a self-contained paragraph on a single topic.
2. Word count must stay within {spec["wc"]}.
3. Use NEW topic prefixes — do NOT reuse existing ones.
4. Existing topic prefixes already in use: {", ".join(EXISTING_TOPICS)}
5. Suggested new topic prefixes: {", ".join(new_topics[:15])}
6. pid format: {{topic}}_01 (e.g., media_01, money_01, ocean_01)
7. "ja" must be a natural Japanese translation of the English text.
8. No markdown, no explanation — output ONLY the JSON array.

## Output format (strict JSON array):
[
  {{
    "pid": "media_01",
    "level": "{level}",
    "text": "English passage here.",
    "ja": "日本語訳をここに。"
  }},
  ...
]

Generate {count} passages now:"""

    return prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, choices=list(LEVEL_SPECS.keys()))
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    existing_pids = load_existing_pids()
    prompt = make_prompt(args.level, args.count, existing_pids)

    # Copy to clipboard
    subprocess.run(["pbcopy"], input=prompt.encode(), check=True)

    print(f"✅ プロンプトをクリップボードにコピーしました")
    print(f"   レベル: {args.level}  件数: {args.count}")
    print()
    print("次のステップ:")
    print("  1. Claude.ai (https://claude.ai) を開いてプロンプトを貼り付け")
    print("  2. 出力されたJSONを sync/staging.json に保存")
    print("  3. python3 add_passages.py を実行")


if __name__ == "__main__":
    main()
