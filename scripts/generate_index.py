"""
output/x_articles/ の全ツイート記事からindex.mdを生成する
"""
import json
import os
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("output/x_articles")
DATA_FILE = Path("data/popular_tweets.json")
INDEX_FILE = OUTPUT_DIR / "index.md"


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    tweets = {t["id"]: t for t in data["tweets"]}

    rows = []
    complete = 0
    incomplete = 0

    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name == "index.md":
            continue
        tweet_id = d.name
        files = list(d.iterdir())
        file_names = {f.name for f in files}
        is_complete = len(files) >= 5

        if is_complete:
            complete += 1
        else:
            incomplete += 1

        meta_file = d / "metadata.json"
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass

        tweet = tweets.get(tweet_id, {})
        rows.append({
            "id": tweet_id,
            "likes": tweet.get("like_count", meta.get("like_count", 0)),
            "chars": meta.get("article_char_count", "?"),
            "figures": meta.get("figure_count", len([f for f in file_names if f.endswith(".svg")])),
            "fact": meta.get("fact_check_result", "?"),
            "text": tweet.get("text", "")[:50],
            "complete": is_complete,
            "created_at": tweet.get("created_at", ""),
        })

    rows.sort(key=lambda x: x["likes"] if isinstance(x["likes"], int) else 0, reverse=True)

    lines = [
        "# @ichi_eigo 人気ツイート 深掘り記事インデックス",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"記事数: {complete} / {complete + incomplete} (完了 / 全体)",
        f"ソース: data/popular_tweets.json ({data['fetched_at'][:10]}取得)",
        "",
        "---",
        "",
        "## 記事一覧（いいね数順）",
        "",
        "| # | いいね | ツイートID | ツイート（抜粋） | 文字数 | 図解 | ファクトチェック | 状態 |",
        "|---|--------|------------|-----------------|--------|------|-----------------|------|",
    ]

    for i, r in enumerate(rows, 1):
        status = "✅" if r["complete"] else "⏳"
        fact_badge = "✅" if r["fact"] == "PASS" else ("❌" if r["fact"] == "FAIL" else r["fact"])
        text_preview = r["text"].replace("|", "｜")
        lines.append(
            f"| {i} | {r['likes']} | [{r['id']}](./{r['id']}/) | {text_preview}... | {r['chars']} | {r['figures']} | {fact_badge} | {status} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 統計サマリー",
        "",
    ]

    complete_rows = [r for r in rows if r["complete"]]
    char_counts = [r["chars"] for r in complete_rows if isinstance(r["chars"], int)]
    if char_counts:
        lines += [
            f"- 完了記事数: {len(complete_rows)}",
            f"- 平均文字数: {sum(char_counts) // len(char_counts)} 字",
            f"- 最大文字数: {max(char_counts)} 字",
            f"- 最小文字数: {min(char_counts)} 字",
            f"- ファクトチェックPASS: {sum(1 for r in complete_rows if r['fact'] == 'PASS')}",
            f"- ファクトチェックFAIL: {sum(1 for r in complete_rows if r['fact'] == 'FAIL')}",
        ]

    lines += [
        "",
        "---",
        "*このインデックスは scripts/generate_index.py で自動生成されます*",
    ]

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Generated {INDEX_FILE}")
    print(f"Complete: {complete}, Incomplete: {incomplete}")


if __name__ == "__main__":
    main()
