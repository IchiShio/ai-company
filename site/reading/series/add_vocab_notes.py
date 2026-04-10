#!/usr/bin/env python3
"""
vocab_notes が欠けている outside 単語を管理するスクリプト。

【運用フロー】
新記事追加後:
  1. python3 reading/series/add_vocab_notes.py --export-missing
     → missing_vocab.json を生成（Claude Code に渡す用）
  2. Claude Code に「missing_vocab.json を読んで vocab_notes を追加して」と依頼
     → Claude Code が定義を生成して stories.js を直接更新

APIクレジットがある場合のみ:
  python3 reading/series/add_vocab_notes.py  # Claude Haiku で自動生成

確認:
  python3 reading/series/add_vocab_notes.py --dry-run
"""

import json, re, sys, os, time, argparse
from pathlib import Path

BASE          = Path(__file__).parent
STORIES_JS    = BASE / 'stories.js'
MISSING_JSON  = BASE / 'missing_vocab.json'
DOTENV        = BASE.parent.parent / '.env'


# ── データ読み込み・保存 ─────────────────────────────────────
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
    """[{'i': story_index, 'id': story_id, 'word': word, 'body': body}, ...] を返す"""
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
                # body は最初の3文に絞る（Claude Code に渡す際に読みやすくする）
                sentences = re.split(r'(?<=[.!?])\s+', s.get('body', '').strip())
                missing.append({
                    'i':    i,
                    'id':   s['id'],
                    'word': w,
                    'body': ' '.join(sentences[:3]),
                })
    return missing


# ── Claude API で定義生成（クレジットがある場合のみ）─────────
def generate_definition_api(client, word, body):
    prompt = (
        f'In the following passage, define the word "{word}" '
        f'as it is used in this specific context. '
        f'Write a single concise English definition (one sentence, under 15 words). '
        f'Do not include the word itself in the definition. '
        f'Reply with only the definition, no extra text.\n\n'
        f'Passage: {body}'
    )
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=60,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return msg.content[0].text.strip().rstrip('.')


# ── 定義を stories.js に書き込む ────────────────────────────
def apply_definitions(stories, defs):
    """
    defs: [{'i': int, 'word': str, 'definition': str}, ...]
    """
    added = 0
    for d in defs:
        i, word, definition = d['i'], d['word'], d['definition']
        s = stories[i]
        if 'vocab_notes' not in s:
            s['vocab_notes'] = []
        if any(n['word'].lower() == word.lower() for n in s['vocab_notes']):
            continue
        s['vocab_notes'].append({'word': word, 'definition': definition})
        added += 1
    return added


# ── メイン ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='ReadUp vocab_notes 管理')
    parser.add_argument('--dry-run',       action='store_true', help='欠けている単語を表示するだけ')
    parser.add_argument('--export-missing', action='store_true', help='missing_vocab.json を生成（Claude Code 用）')
    parser.add_argument('--id',            type=str, help='特定ストーリーIDのみ対象')
    args = parser.parse_args()

    stories = load_stories()
    missing = find_missing(stories)

    if args.id:
        m = re.match(r'(\d{4}W\d+_\d+(?:_\w+)?)', args.id)
        sid = m.group(1) if m else args.id
        missing = [e for e in missing if e['id'] == sid or e['id'].startswith(sid.rstrip('_'))]

    # ── --dry-run: 確認のみ ──────────────────────────────────
    if args.dry_run or args.export_missing:
        print(f'vocab_note 欠け: {len(missing)} 件')
        for e in missing:
            print(f'  {e["id"]}: {e["word"]}')

        if args.export_missing and missing:
            MISSING_JSON.write_text(
                json.dumps(missing, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f'\n→ {MISSING_JSON.name} に保存しました。')
            print('  Claude Code に「missing_vocab.json を読んで vocab_notes を追加して」と依頼してください。')
        return

    if not missing:
        print('vocab_note 欠け: 0 件 — 対応不要')
        return

    # ── Claude API モード ───────────────────────────────────
    if DOTENV.exists():
        for line in DOTENV.read_text().splitlines():
            if line.startswith('ANTHROPIC_API_KEY='):
                os.environ.setdefault('ANTHROPIC_API_KEY', line.split('=', 1)[1].strip())

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    except Exception:
        print('ERROR: anthropic がインストールされていないか APIキーが見つかりません。')
        print('  --export-missing を使って Claude Code に依頼してください。')
        sys.exit(1)

    defs = []
    print(f'vocab_note 欠け: {len(missing)} 件 → Claude Haiku で生成中...')
    for idx, e in enumerate(missing):
        print(f'[{idx+1}/{len(missing)}] {e["id"]}: {e["word"]} ... ', end='', flush=True)
        try:
            definition = generate_definition_api(client, e['word'], e['body'])
            defs.append({'i': e['i'], 'word': e['word'], 'definition': definition})
            print(f'"{definition}"')
        except Exception as ex:
            print(f'ERROR: {ex}')
            print('  APIクレジット切れの可能性があります。--export-missing を使ってください。')
            break
        time.sleep(0.3)

    if defs:
        added = apply_definitions(stories, defs)
        save_stories(stories)
        print(f'\n✅ {added} 件追加 → stories.js 更新済み')


if __name__ == '__main__':
    main()
