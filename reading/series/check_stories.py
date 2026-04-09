#!/usr/bin/env python3
"""
ReadUp Stories チェッカー（API不要）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【チェック1】文数チェック
  body_ja の文数が body より 2文以上多い → 別VL本文から翻訳された可能性

【チェック2】クロスVLリークチェック（メイン）
  同記事の他VLレベル(vl3000/5000/7000)にしか存在しない数字が
  vl2000の body_ja に混入していないか検出する。
  ※ 英語本文の「twelve → 12」変換ではなく、他VL本文との差分で判定するため
    false positive が発生しない。

【チェック3】ソース記事整合チェック
  body に含まれる重要な数字がソース記事に存在するか確認。

使い方:
  python3 reading/series/check_stories.py              # 全記事チェック
  python3 reading/series/check_stories.py --id 2026W12_03_vl2000
  python3 reading/series/check_stories.py --vl vl2000
  python3 reading/series/check_stories.py --errors-only
"""

import json, re, sys, argparse
from pathlib import Path
from collections import defaultdict

BASE         = Path(__file__).parent
STORIES_JS   = BASE / 'stories.js'
SOURCES_JSON = BASE / 'selected_articles.json'

# 英語の数字単語 → アラビア数字マッピング（body の数字抽出に使用）
EN_NUMBER_WORDS = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,
    'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,
    'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,
    'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,
    'sixty':60,'seventy':70,'eighty':80,'ninety':90,
}


# ── データ読み込み ────────────────────────────────────────
def load_stories():
    raw = STORIES_JS.read_text(encoding='utf-8').strip()
    raw = raw.removeprefix('const STORIES =').rstrip(';')
    return json.loads(raw)

def load_sources():
    if not SOURCES_JSON.exists():
        return {}
    sources = json.loads(SOURCES_JSON.read_text(encoding='utf-8'))
    return {s['url']: s for s in sources}


# ── テキスト解析ユーティリティ ───────────────────────────
def split_en_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

def split_ja_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[。！？])', text.strip()) if s.strip()]

def extract_digits(text):
    """
    テキストからアラビア数字の値セットを返す。
    "238,000" → {238000, 238}  のように正規化して格納。
    """
    nums = set()
    for m in re.finditer(r'\d[\d,]*', text):
        raw = m.group()
        nums.add(raw.replace(',', ''))  # カンマなし
    return nums

def extract_numbers_from_en(text):
    """
    英語本文から数値を抽出（アラビア数字 + 英語数字単語）。
    "twelve" → 12, "two hundred" → 200 なども含む。
    """
    nums = extract_digits(text)
    tokens = re.findall(r'\b[a-z]+\b', text.lower())
    i = 0
    while i < len(tokens):
        w = tokens[i]
        if w in EN_NUMBER_WORDS:
            val = EN_NUMBER_WORDS[w]
            # "twenty-one" 形式（ハイフン区切りは既にトークン分割されない）
            # "two hundred" 形式
            if i+1 < len(tokens) and tokens[i+1] == 'hundred':
                val *= 100
                i += 1
                if i+1 < len(tokens) and tokens[i+1] in EN_NUMBER_WORDS:
                    val += EN_NUMBER_WORDS[tokens[i+1]]
                    i += 1
            nums.add(str(val))
        i += 1
    # ハイフン結合数字 "thirty-seven" → 37
    for m in re.finditer(r'\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)-'
                         r'(one|two|three|four|five|six|seven|eight|nine)\b', text.lower()):
        tens = EN_NUMBER_WORDS[m.group(1)]
        units = EN_NUMBER_WORDS[m.group(2)]
        nums.add(str(tens + units))
    # "N decade(s)" パターン: "three decades" → 30, "a decade" → 10
    decade_pfx = {'a':1,'one':1,'two':2,'three':3,'four':4,'five':5,
                  'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
    for m in re.finditer(r'\b(a|one|two|three|four|five|six|seven|eight|nine|ten)\s+decade[s]?\b',
                         text.lower()):
        nums.add(str(decade_pfx[m.group(1)] * 10))
    # 万単位端数: 238300 → 日本語で "23万8,300" と書くため 8300 も許容
    extended = set()
    for n in list(nums):
        try:
            val = int(n)
            if val >= 10000:
                remainder = val % 10000
                if remainder >= 100:
                    extended.add(str(remainder))
        except ValueError:
            pass
    nums.update(extended)
    return nums

IGNORE_NUMS = {'2026','2025','2024','2023','2022','2021','2020','2019','2018',
               '2017','2016','2015','2014','2013','2012','2011','2010',
               '1971','1903','1867','1871','1997','1983','1992','2032'}


# ── チェック1: 文数チェック ──────────────────────────────
def check_sentence_count(story):
    issues = []
    body    = story.get('body', '').strip()
    body_ja = story.get('body_ja', '').strip()
    if not body or not body_ja:
        return [('ERROR', 'EMPTY', 'body または body_ja が空')]
    en_n = len(split_en_sentences(body))
    ja_n = len(split_ja_sentences(body_ja))
    diff = ja_n - en_n
    if diff >= 3:
        issues.append(('ERROR', 'SENT_COUNT',
            f'body_ja が body より {diff}文多い (EN={en_n} JA={ja_n})'))
    elif diff == 2:
        issues.append(('WARN', 'SENT_COUNT',
            f'body_ja が body より {diff}文多い (EN={en_n} JA={ja_n}) → 目視確認推奨'))
    return issues


# ── チェック2: クロスVLリークチェック ────────────────────
def check_cross_vl_leak(story, siblings):
    """
    story の body_ja に、他VLレベルにしか存在しない数字が混入していないか検出。
    siblings: 同一記事の他VLバージョンのリスト
    """
    issues = []
    body_ja = story.get('body_ja', '')
    own_body = story.get('body', '')
    if not body_ja or not siblings:
        return issues

    own_nums  = extract_numbers_from_en(own_body)
    ja_digits = extract_digits(body_ja)

    for sib in siblings:
        sib_nums = extract_digits(sib.get('body', ''))
        # 他VLにあって自VLにない数字（= 他VLからしか来ない数字）
        exclusive = {n for n in sib_nums
                     if n not in own_nums
                     and n not in IGNORE_NUMS
                     and len(n) >= 2}
        # それがbody_jaに混入しているか
        leaked = exclusive & ja_digits
        if leaked:
            issues.append(('ERROR', 'VL_LEAK',
                f'{sib["vl"]}の本文にしかない数字 {leaked} が body_ja に存在 '
                f'→ {sib["vl"]}の本文から翻訳された可能性'))
    return issues


# ── チェック3: ソース記事整合チェック ────────────────────
def check_source_consistency(story, source):
    """
    body の数字がソース記事に存在するか確認（創作・誤変換の検出）。
    """
    issues = []
    if not source:
        return issues
    body        = story.get('body', '')
    source_text = source.get('text', '')
    if not source_text:
        return issues

    body_nums   = extract_numbers_from_en(body)
    source_nums = extract_numbers_from_en(source_text)

    invented = {n for n in body_nums
                if n not in source_nums
                and n not in IGNORE_NUMS
                and len(n) >= 3}
    if invented:
        issues.append(('WARN', 'SRC_MISMATCH',
            f'body の数字 {invented} がソース記事に見当たらない → 要確認'))
    return issues


# ── メイン ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='ReadUp Stories チェッカー')
    parser.add_argument('--id',          type=str,  help='特定ストーリーIDのみ')
    parser.add_argument('--vl',          type=str,  help='特定レベルのみ')
    parser.add_argument('--errors-only', action='store_true', help='ERRORのみ表示')
    args = parser.parse_args()

    stories = load_stories()
    sources = load_sources()

    # フィルタリング
    target_ids = None
    if args.id:
        # 同記事の全VLも含めてチェック（クロスVL比較のため）
        m = re.match(r'(\d{4}W\d+_\d+)', args.id)
        prefix = m.group(1) if m else args.id
        target_ids = {s['id'] for s in stories if s['id'].startswith(prefix)}

    # 記事グループを構築（週+番号でグループ化）
    article_groups = defaultdict(list)
    for s in stories:
        m = re.match(r'(\d{4}W\d+_\d+)', s['id'])
        if m:
            article_groups[m.group(1)].append(s)

    # チェック対象のストーリー
    if args.id:
        check_stories = [s for s in stories if s['id'] in target_ids]
        if args.vl:
            check_stories = [s for s in check_stories if s['vl'] == args.vl]
    elif args.vl:
        check_stories = [s for s in stories if s['vl'] == args.vl]
    else:
        check_stories = stories

    print(f'📖 チェック対象: {len(check_stories)} ストーリー')
    if args.errors_only:
        print('   (ERRORのみ表示)')
    print()

    counts = defaultdict(int)
    all_errors = []

    for story in check_stories:
        sid = story['id']
        m   = re.match(r'(\d{4}W\d+_\d+)', sid)
        key = m.group(1) if m else sid

        siblings = [s for s in article_groups[key] if s['id'] != sid]
        source   = sources.get(story.get('source_url', ''), {})

        issues  = check_sentence_count(story)
        issues += check_cross_vl_leak(story, siblings)
        issues += check_source_consistency(story, source)

        errors = [i for i in issues if i[0] == 'ERROR']
        warns  = [i for i in issues if i[0] == 'WARN']

        if errors:
            counts['error'] += 1
            print(f'🔴 {sid}')
            for _, code, msg in errors:
                print(f'   ERROR [{code}] {msg}')
            if not args.errors_only:
                for _, code, msg in warns:
                    print(f'   WARN  [{code}] {msg}')
            all_errors.extend([(sid, *e) for e in errors])
        elif warns:
            counts['warn'] += 1
            if not args.errors_only:
                print(f'🟡 {sid}')
                for _, code, msg in warns:
                    print(f'   WARN  [{code}] {msg}')
        else:
            counts['ok'] += 1
            if not args.errors_only:
                print(f'✅ {sid}')

    print()
    print('=' * 60)
    print('📊 チェック結果サマリー')
    print('=' * 60)
    print(f'✅ OK:    {counts["ok"]}件')
    print(f'🟡 WARN:  {counts["warn"]}件')
    print(f'🔴 ERROR: {counts["error"]}件')

    if all_errors:
        print()
        print('🔴 ERROR 一覧:')
        for sid, _, code, msg in all_errors:
            print(f'  [{code}] {sid}: {msg}')
        sys.exit(1)
    else:
        print()
        if counts['warn']:
            print('⚠️  WARNあり（目視確認推奨）')
        else:
            print('✅ 全件問題なし')


if __name__ == '__main__':
    main()
