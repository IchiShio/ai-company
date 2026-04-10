#!/usr/bin/env python3
"""
passages.ts の全パッセージに日本語訳(ja)フィールドを追加するスクリプト。
Claude Haiku を使って一括翻訳し、passages.ts を上書きする。
"""
import re, json, os, sys
import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    # .env から読む
    env_path = os.path.join(os.path.dirname(__file__), "../.env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("ANTHROPIC_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
                break

if not API_KEY:
    print("Error: ANTHROPIC_API_KEY not found")
    sys.exit(1)

client = anthropic.Anthropic(api_key=API_KEY)

PASSAGES_FILE = os.path.join(os.path.dirname(__file__), "src/passages.ts")

def extract_passages(ts_src: str) -> list[dict]:
    """passages.ts から全パッセージを抽出する。"""
    # {pid:"...",wc:N,text:"..."} または {pid:"...",wc:N,text:"...",ja:"..."} にマッチ
    pattern = r'\{pid:"([^"]+)",wc:(\d+),text:"([^"]+)"(?:,ja:"([^"]*)")?\}'
    results = []
    for m in re.finditer(pattern, ts_src):
        results.append({
            "pid": m.group(1),
            "wc": int(m.group(2)),
            "text": m.group(3),
            "ja": m.group(4) or "",
        })
    return results

def translate_batch(passages: list[dict], retries: int = 3) -> list[str]:
    """Claude Haiku で一括翻訳。テキストのリストを受け取りjaのリストを返す。"""
    texts_json = json.dumps([p["text"] for p in passages], ensure_ascii=False)
    prompt = f"""以下のJSON配列の英文を、それぞれ自然な日本語に翻訳してください。
英語学習者向けの参考訳として、意訳ではなく意味の通る訳にしてください。
出力はJSON配列（文字列のリスト）のみ。余計な説明不要。コードブロック不要。

{texts_json}"""

    for attempt in range(retries):
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        # コードブロックがあれば除去
        raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start < 0 or end <= 0:
            print(f"    Warning: no JSON array found (attempt {attempt+1}), raw={raw[:100]}")
            continue
        try:
            result = json.loads(raw[start:end])
            if len(result) == len(passages):
                return result
            print(f"    Warning: got {len(result)} items, expected {len(passages)} (attempt {attempt+1})")
        except json.JSONDecodeError as e:
            print(f"    Warning: JSON parse error (attempt {attempt+1}): {e}")
    # フォールバック: 1件ずつ翻訳
    print("    Falling back to one-by-one translation...")
    results = []
    for p in passages:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": f"次の英文を自然な日本語に翻訳してください。訳文のみ出力。\n\n{p['text']}"}]
        )
        results.append(msg.content[0].text.strip())
    return results

def rebuild_ts(ts_src: str, translations: dict[str, str]) -> str:
    """passages.ts の各パッセージに ja フィールドを追加して再構築する。"""
    def replace_match(m: re.Match) -> str:
        pid = m.group(1)
        wc  = m.group(2)
        text = m.group(3)
        ja = translations.get(pid, "")
        # ダブルクォートをエスケープ
        ja_escaped = ja.replace('"', '\\"')
        return f'{{pid:"{pid}",wc:{wc},text:"{text}",ja:"{ja_escaped}"}}'

    # 既存の ja フィールドあり・なし両方にマッチ
    pattern = r'\{pid:"([^"]+)",wc:(\d+),text:"([^"]+)"(?:,ja:"[^"]*")?\}'
    return re.sub(pattern, replace_match, ts_src)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "translation_cache.json")

def load_cache() -> dict[str, str]:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict[str, str]):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def main():
    print("Reading passages.ts ...")
    with open(PASSAGES_FILE, encoding="utf-8") as f:
        ts_src = f.read()

    passages = extract_passages(ts_src)
    print(f"Found {len(passages)} passages")

    # キャッシュを読む（既に翻訳済みのもの）
    cache = load_cache()

    # 既にtsに埋め込まれているjaもキャッシュに追加
    for p in passages:
        if p["ja"] and p["pid"] not in cache:
            cache[p["pid"]] = p["ja"]

    need_translate = [p for p in passages if p["pid"] not in cache]
    print(f"{len(need_translate)} passages need translation ({len(cache)} cached)")

    if not need_translate:
        print("All passages already have translations.")
    else:
        # バッチサイズ20で処理
        BATCH = 20
        for i in range(0, len(need_translate), BATCH):
            batch = need_translate[i:i+BATCH]
            print(f"  Translating batch {i//BATCH + 1}/{(len(need_translate)+BATCH-1)//BATCH} ({len(batch)} passages)...")
            ja_list = translate_batch(batch)
            for p, ja in zip(batch, ja_list):
                cache[p["pid"]] = ja
            save_cache(cache)  # バッチごとに保存
            print(f"    Done. Sample: {ja_list[0][:40]}...")

    print("Rebuilding passages.ts ...")
    new_ts = rebuild_ts(ts_src, cache)

    with open(PASSAGES_FILE, "w", encoding="utf-8") as f:
        f.write(new_ts)

    print(f"Done! Updated {PASSAGES_FILE}")
    # キャッシュ削除（不要になったので）
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("Cache file removed.")

if __name__ == "__main__":
    main()
