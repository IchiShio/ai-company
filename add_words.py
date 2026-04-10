#!/usr/bin/env python3
"""
add_words.py - words/staging.json の問題を questions.js に追加

処理フロー:
  1. words/staging.json 読み込み・バリデーション
  2. Edge TTS で MP3 音声を生成（5ボイスローテーション）
  3. words/questions.js 末尾に新問題を追記（audioフィールド付き）
  4. git add . && git commit && git push
  5. staging.json をクリア

前提: check_questions.py --type words で PASS 済みであること
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from lib import WORDS_VALID_FIELDS, VALID_AXES_WORDS, VALID_DIFFS

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "words" / "questions.js"
STAGING_JSON = REPO_ROOT / "words" / "staging.json"
AUDIO_DIR = REPO_ROOT / "words" / "audio"

VOICES = [
    "en-US-AriaNeural",
    "en-GB-SoniaNeural",
    "en-US-GuyNeural",
    "en-AU-NatashaNeural",
    "en-GB-RyanNeural",
]


def load_staging():
    if not STAGING_JSON.exists():
        print(f"ERROR: {STAGING_JSON} が見つかりません")
        sys.exit(1)

    content = STAGING_JSON.read_text(encoding="utf-8").strip()
    if not content or content == "[]":
        print("staging.json が空です。generate_words.py を先に実行してください。")
        sys.exit(0)

    data = json.loads(content)
    if not isinstance(data, list):
        print("ERROR: staging.json はリスト形式である必要があります")
        sys.exit(1)

    print(f"staging.json から {len(data)} 問を読み込みました")

    # バリデーション
    errors = []
    auto_fixed = []
    for i, q in enumerate(data):
        missing = WORDS_VALID_FIELDS - set(q.keys())
        if missing:
            errors.append(f"  [{i}] 必須フィールドが不足: {missing}")
        if q.get("diff") not in VALID_DIFFS:
            errors.append(f"  [{i}] diff が不正: {q.get('diff')}")
        if q.get("axis") not in VALID_AXES_WORDS:
            errors.append(f"  [{i}] axis が不正: {q.get('axis')}")
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 4:
            errors.append(f"  [{i}] choices は4要素のリストが必要")

        # answer === choices[0] の自動補正
        choices = q.get("choices", [])
        if isinstance(choices, list) and len(choices) > 0:
            if q.get("answer") != choices[0]:
                original = q.get("answer", "")
                if original in choices:
                    idx = choices.index(original)
                    choices[0], choices[idx] = choices[idx], choices[0]
                    q["choices"] = choices
                    auto_fixed.append(f"  [{i}] choices スワップ: [0]<->[{idx}]")
                else:
                    q["answer"] = choices[0]
                    auto_fixed.append(f"  [{i}] answer 自動補正: \"{original}\" -> \"{choices[0]}\"")

    if auto_fixed:
        print("WARNING: answer/choices 自動補正:")
        for msg in auto_fixed:
            print(msg)

    if errors:
        print("ERROR: バリデーションエラー:")
        for e in errors:
            print(e)
        sys.exit(1)

    return data


def get_next_audio_num():
    """既存の最大のq番号を取得"""
    if not AUDIO_DIR.exists():
        AUDIO_DIR.mkdir(parents=True)
        return 1
    existing = list(AUDIO_DIR.glob("q*.mp3"))
    if not existing:
        return 1
    nums = []
    for f in existing:
        m = re.match(r'q(\d+)\.mp3', f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def generate_audio(questions, start_num):
    """Edge TTS で音声生成"""
    print(f"\n音声生成開始: {len(questions)} 問 (q{start_num:02d}〜)")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for i, q in enumerate(questions):
        num = start_num + i
        voice = VOICES[(num - 1) % len(VOICES)]
        filename = f"q{num:02d}.mp3"
        filepath = AUDIO_DIR / filename

        q["audio"] = f"audio/{filename}"

        if filepath.exists():
            print(f"  [{i+1}/{len(questions)}] SKIP {filename} (exists)")
            continue

        for attempt in range(3):
            try:
                result = subprocess.run(
                    ["edge-tts", "--voice", voice, "--text", q["text"], "--write-media", str(filepath)],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    print(f"  [{i+1}/{len(questions)}] OK {filename} ({voice})")
                    break
                else:
                    print(f"  [{i+1}/{len(questions)}] ERROR {filename}: {result.stderr[:100]}")
                    break
            except subprocess.TimeoutExpired:
                if attempt < 2:
                    print(f"  [{i+1}/{len(questions)}] TIMEOUT {filename}, retry {attempt+2}/3...")
                    import time; time.sleep(2)
                else:
                    print(f"  [{i+1}/{len(questions)}] TIMEOUT {filename} (skipped after 3 attempts)")

    return questions


def get_existing_count():
    """questions.jsの現在の問題数を取得"""
    if not QUESTIONS_JS.exists():
        return 0
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    return len(re.findall(r'\bword:', content))


def format_question_js(q):
    """問題をJS形式の文字列にフォーマット"""
    def esc(s):
        return (str(s).replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n"))

    choices = json.dumps(q["choices"], ensure_ascii=False)

    parts = [
        f'diff: "{q["diff"]}"',
        f'axis: "{q["axis"]}"',
        f'word: "{esc(q["word"])}"',
        f'text: "{esc(q["text"])}"',
        f'ja: "{esc(q["ja"])}"',
        f'answer: "{esc(q["answer"])}"',
        f'choices: {choices}',
        f'audio: "{q["audio"]}"',
        f'expl: "{esc(q["expl"])}"',
    ]
    return "  { " + ", ".join(parts) + " }"


def append_to_questions_js(questions):
    """questions.jsに問題を追記"""
    content = QUESTIONS_JS.read_text(encoding="utf-8")

    new_lines = ",\n".join(format_question_js(q) for q in questions)

    # ]; の前に追記
    content = content.replace("\n];", f",\n{new_lines}\n];")

    # コメントの問題数を更新
    old_count = get_existing_count()
    new_count = old_count + len(questions)
    content = re.sub(
        r'// questions\.js — \d+ questions',
        f'// questions.js — {new_count} questions',
        content,
    )

    QUESTIONS_JS.write_text(content, encoding="utf-8")
    print(f"\nquestions.js に {len(questions)} 問を追加（合計 {new_count} 問）")


def git_push(count):
    """git add, commit, push"""
    print("\ngit push...")
    subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True)
    msg = f"WordsUp: {count}問追加（品質チェック済み）"
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, check=True)
    print("push 完了!")


def main():
    questions = load_staging()

    # 音声生成
    start_num = get_next_audio_num()
    questions = generate_audio(questions, start_num)

    # questions.js に追記
    append_to_questions_js(questions)

    # staging.json をクリア
    STAGING_JSON.write_text("[]", encoding="utf-8")

    # git push
    git_push(len(questions))


if __name__ == "__main__":
    main()
