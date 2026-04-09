#!/usr/bin/env python3
"""
vocab_notes が欠けている outside 単語に、文脈に沿った英英定義を追加する。
Claude API (Haiku) を使用。

使い方:
  python3 reading/series/add_vocab_notes.py --dry-run  # 対象確認のみ
  python3 reading/series/add_vocab_notes.py            # 実行
"""

import json, re, sys, os, time, argparse
from pathlib import Path

BASE        = Path(__file__).parent
STORIES_JS  = BASE / 'stories.js'
DOTENV      = BASE.parent.parent / '.env'

# .env から ANTHROPIC_API_KEY を読む
def load_env():
    if DOTENV.exists():
        for line in DOTENV.read_text().splitlines():
            if line.startswith('ANTHROPIC_API_KEY='):
                os.environ.setdefault('ANTHROPIC_API_KEY', line.split('=',1)[1].strip())

load_env()

import anthropic

MODEL = 'claude-haiku-4-5-20251001'

# ── データ読み込み ──────────────────────────────────────────
def load_stories():
    raw = STORIES_JS.read_text(encoding='utf-8').strip()
    raw = raw.removeprefix('const STORIES =').rstrip(';')
    return json.loads(raw)

def save_stories(stories):
    STORIES_JS.write_text(
        'const STORIES = ' + json.dumps(stories, ensure_ascii=False, indent=2) + ';\n',
        encoding='utf-8'
    )

# ── 欠けている vocab_notes を検出 ──────────────────────────
def find_missing(stories):
    """[(story_index, word), ...] を返す"""
    missing = []
    for i, s in enumerate(stories):
        noted = {n['word'].lower() for n in s.get('vocab_notes', [])}
        seen = set()
        for tok in s.get('body_annotated', []):
            w = tok.get('w', '')
            if (tok.get('outside')
                    and re.match(r'^[a-zA-Z]+$', w)
                    and w.lower() not in noted
                    and w.lower() not in seen):
                seen.add(w.lower())
                missing.append((i, w))
    return missing

# ── Claude API で文脈に沿った定義を生成 ────────────────────
def generate_definition(client, word, body):
    """
    英語本文 body の文脈で word の意味を英語で簡潔に説明する。
    """
    prompt = (
        f"In the following passage, define the word \"{word}\" "
        f"as it is used in this specific context. "
        f"Write a single concise English definition (one sentence, under 15 words). "
        f"Do not include the word itself in the definition. "
        f"Reply with only the definition, no extra text.\n\n"
        f"Passage: {body}"
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=60,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return msg.content[0].text.strip().rstrip('.')

# ── メイン ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--id', type=str, help='特定ストーリーIDのみ')
    args = parser.parse_args()

    stories = load_stories()
    missing = find_missing(stories)

    if args.id:
        prefix = re.match(r'(\d{4}W\d+_\d+_\w+)', args.id)
        sid = prefix.group(1) if prefix else args.id
        missing = [(i, w) for i, w in missing if stories[i]['id'] == sid]

    print(f'vocab_note 欠け: {len(missing)} 件')
    for i, w in missing:
        print(f'  {stories[i]["id"]}: {w}')

    if args.dry_run or not missing:
        return

    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    updated = 0

    for idx, (i, word) in enumerate(missing):
        s = stories[i]
        body = s.get('body', '')
        print(f'[{idx+1}/{len(missing)}] {s["id"]}: {word} ... ', end='', flush=True)
        try:
            definition = generate_definition(client, word, body)
            if 'vocab_notes' not in s:
                s['vocab_notes'] = []
            s['vocab_notes'].append({'word': word, 'definition': definition})
            print(f'"{definition}"')
            updated += 1
        except Exception as e:
            print(f'ERROR: {e}')
        time.sleep(0.3)

    if updated:
        save_stories(stories)
        print(f'\n✅ {updated} 件追加 → stories.js 更新済み')
    else:
        print('\n変更なし')

if __name__ == '__main__':
    main()
