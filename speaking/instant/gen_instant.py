#!/usr/bin/env python3
"""
gen_instant.py — 瞬間英作文問題生成スクリプト
Claude API (claude-sonnet-4-6) で問題を生成し、index.html の DATA 配列に追記する。

使用例:
  python3 gen_instant.py --count 100            # 全カテゴリ均等に100問
  python3 gen_instant.py --count 50 --cat daily # 日常会話のみ50問
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic パッケージが見つかりません。pip install anthropic でインストールしてください。")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
    load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')
    load_dotenv()
except ImportError:
    pass

BATCH_SIZE = 30

CATEGORIES = {
    'daily':    ('日常会話',   '日常的な会話・感想・軽い気持ち・家庭・友人との会話'),
    'business': ('ビジネス',   '仕事・メール・会議・職場での依頼・報告・謝罪'),
    'travel':   ('旅行',       'ホテル・移動・観光・店頭・交通機関・道案内'),
    'emotion':  ('感情表現',   '喜怒哀楽・共感・驚き・感謝・後悔・励まし'),
}


def count_words(text: str) -> int:
    return len(text.strip().split())


def assign_diff(main: str) -> int:
    wc = count_words(main)
    if wc <= 5:
        return 1
    elif wc <= 10:
        return 2
    else:
        return 3


def extract_existing_mains(html_path: Path) -> list[str]:
    """index.html から既存の main フィールドを抽出する。"""
    text = html_path.read_text(encoding='utf-8')
    # main:"..." or main:'...' パターンを抽出
    pattern = r'main:\s*["\']([^"\']+)["\']'
    return re.findall(pattern, text)


def build_prompt(cat: str, cl: str, cat_desc: str, count: int, existing_mains: list[str]) -> str:
    # 重複回避リスト（長くなりすぎないよう最大300件）
    exclude_list = existing_mains[-300:] if len(existing_mains) > 300 else existing_mains
    exclude_str = json.dumps(exclude_list, ensure_ascii=False) if exclude_list else '[]'

    return f"""ネイティブ英語話者が日常・職場・旅行でよく使う英語フレーズを{count}個生成してください。
カテゴリ: {cat_desc}

以下のJSONフォーマットで返してください（配列のみ、説明文なし）:
[
  {{
    "cat": "{cat}",
    "cl": "{cl}",
    "ja": "日本語の表現（10文字以内）",
    "ctx": "使用場面（省略可、20文字以内）",
    "main": "英語フレーズ（ネイティブが実際に使う自然な表現）",
    "alt": "別の言い方: <em>\\"代替表現1\\"</em> / <em>\\"代替表現2\\"</em>",
    "tip": "学習ポイント（50文字以内）"
  }}
]

制約:
- main はネイティブが口語でよく使う自然な英語のみ
- 既存フレーズと重複しない: {exclude_str}
- バランスよく diff 1〜3 を混在させる（diff 1が40%、diff 2が45%、diff 3が15%目安）
- diff はワード数で後から自動付与するため出力不要
- JSON配列のみ返すこと（前後の説明文や```jsonなどのコードブロック記号は不要）
"""


def generate_batch(client: anthropic.Anthropic, cat: str, cl: str, cat_desc: str,
                   count: int, existing_mains: list[str]) -> list[dict]:
    prompt = build_prompt(cat, cl, cat_desc, count, existing_mains)

    print(f"  → Claude API 呼び出し中 ({count}問, cat={cat})...")
    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': prompt}],
    )

    raw = message.content[0].text.strip()

    # コードブロック記号を除去
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  警告: JSON パースエラー: {e}")
        print(f"  レスポンス先頭200文字: {raw[:200]}")
        return []

    if not isinstance(data, list):
        print(f"  警告: レスポンスがリストではありません: {type(data)}")
        return []

    return data


def format_question_js(q: dict) -> str:
    """問題オブジェクトを JavaScript オブジェクトリテラル形式に変換する。"""
    def esc(s: str) -> str:
        return s.replace('\\', '\\\\').replace('"', '\\"')

    cat  = esc(q.get('cat', ''))
    cl   = esc(q.get('cl', ''))
    ja   = esc(q.get('ja', ''))
    ctx  = esc(q.get('ctx', ''))
    main = esc(q.get('main', ''))
    alt  = esc(q.get('alt', ''))
    tip  = esc(q.get('tip', ''))
    diff = assign_diff(q.get('main', ''))

    return (
        f'  {{cat:"{cat}",cl:"{cl}",ja:"{ja}",ctx:"{ctx}",'
        f'main:"{main}",alt:"{alt}",tip:"{tip}",diff:{diff}}}'
    )


def append_to_index_html(html_path: Path, questions: list[dict]) -> None:
    """index.html の DATA 配列末尾（]; の直前）に問題を追記する。"""
    text = html_path.read_text(encoding='utf-8')

    # DATA 配列の閉じ括弧 ]; を探す
    # _i 付与の行は変更しない
    marker = '];\n\n/* ━'
    if marker not in text:
        # フォールバック
        marker = '];\n'

    insert_lines = ',\n'.join(format_question_js(q) for q in questions)

    if '];\n\n/* ━' in text:
        new_text = text.replace(
            '];\n\n/* ━',
            ',\n' + insert_lines + '\n];\n\n/* ━',
            1
        )
    else:
        # DATA 配列の最後の ]; を見つけて挿入
        # DATA=[...]; パターンを想定
        pos = text.rfind('];\n')
        if pos == -1:
            print("エラー: DATA 配列の閉じ括弧 ]; が見つかりませんでした。")
            sys.exit(1)
        new_text = text[:pos] + ',\n' + insert_lines + '\n' + text[pos:]

    html_path.write_text(new_text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='瞬間英作文問題生成スクリプト')
    parser.add_argument('--count', type=int, default=100, help='生成する問題数（デフォルト: 100）')
    parser.add_argument('--cat', choices=list(CATEGORIES.keys()),
                        help='特定カテゴリのみ生成（省略時は全カテゴリ均等）')
    args = parser.parse_args()

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    html_path = Path(__file__).parent / 'index.html'
    if not html_path.exists():
        print(f"エラー: {html_path} が見つかりません。")
        sys.exit(1)

    existing_mains = extract_existing_mains(html_path)
    print(f"既存問題数: {len(existing_mains)} 件")

    # 生成対象カテゴリの決定
    if args.cat:
        targets = [(args.cat, *CATEGORIES[args.cat])]
        counts = [args.count]
    else:
        cats = list(CATEGORIES.items())
        base = args.count // len(cats)
        remainder = args.count % len(cats)
        counts = [base + (1 if i < remainder else 0) for i in range(len(cats))]
        targets = [(k, v[0], v[1]) for k, v in cats]

    all_questions: list[dict] = []

    for (cat, cl, cat_desc), count in zip(targets, counts):
        if count == 0:
            continue
        print(f"\n[{cl}] {count}問生成中...")

        remaining = count
        batch_existing = list(existing_mains)

        while remaining > 0:
            batch_count = min(BATCH_SIZE, remaining)
            questions = generate_batch(client, cat, cl, cat_desc, batch_count, batch_existing)

            if not questions:
                print(f"  警告: 問題を生成できませんでした。スキップします。")
                break

            # diff を付与
            for q in questions:
                q['diff'] = assign_diff(q.get('main', ''))

            all_questions.extend(questions)
            batch_existing.extend(q.get('main', '') for q in questions)
            remaining -= len(questions)
            print(f"  ✓ {len(questions)}問取得 (残り: {remaining}問)")

    if not all_questions:
        print("\n問題を生成できませんでした。")
        sys.exit(1)

    print(f"\n合計 {len(all_questions)}問 を index.html に追記中...")
    append_to_index_html(html_path, all_questions)
    print(f"✓ 追記完了: {html_path}")
    print(f"\n次のステップ: git add speaking/instant/index.html && git commit && git push origin main")


if __name__ == '__main__':
    main()
