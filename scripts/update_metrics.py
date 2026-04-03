#!/usr/bin/env python3
"""
投稿済みツイートのメトリクスを取得し、以下を自動更新する:
  - schedule.json に metrics フィールドを追記
  - x-knowledge/posts/pdca_log.md に日次サマリーを追記
  - 仮説テスト投稿 (hook_pattern が H で始まる) は active.md の投稿数・データも更新
"""

import json, os, re, sys, requests
from datetime import datetime, timezone, timedelta
from requests_oauthlib import OAuth1

JST = timezone(timedelta(hours=9))
SCRIPT_DIR = os.path.dirname(__file__)
BASE = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SCHEDULE_PATH = os.path.join(BASE, "x-knowledge", "posts", "schedule.json")
HYPOTHESIS_PATH = os.path.join(BASE, "x-knowledge", "hypotheses", "active.md")
PDCA_LOG_PATH = os.path.join(BASE, "x-knowledge", "posts", "pdca_log.md")


def get_auth():
    return OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def fetch_tweet_metrics(auth, tweet_ids):
    """tweet_id リストのメトリクスを X API v2 で一括取得する。"""
    results = {}
    for i in range(0, len(tweet_ids), 100):
        batch = tweet_ids[i : i + 100]
        resp = requests.get(
            "https://api.x.com/2/tweets",
            params={"ids": ",".join(batch), "tweet.fields": "public_metrics,created_at"},
            auth=auth,
        )
        if resp.status_code != 200:
            print(f"API error {resp.status_code}: {resp.text}", file=sys.stderr)
            continue
        for tweet in resp.json().get("data", []):
            m = tweet.get("public_metrics", {})
            imp = m.get("impression_count", 0)
            rts = m.get("retweet_count", 0)
            rt_rate = round(rts / imp * 100, 4) if imp > 0 else 0.0
            results[tweet["id"]] = {
                "imp": imp,
                "likes": m.get("like_count", 0),
                "rts": rts,
                "replies": m.get("reply_count", 0),
                "bookmarks": m.get("bookmark_count", 0),
                "rt_rate": rt_rate,
            }
    return results


def grade(imp):
    if imp >= 10000:
        return "S"
    if imp >= 5000:
        return "A"
    if imp >= 2000:
        return "B"
    if imp >= 1000:
        return "C"
    return "D"


def update_hypothesis(entry, m):
    """active.md の該当仮説の投稿数と現在のデータを更新する。"""
    hook = entry.get("hook_pattern", "")
    match = re.match(r"H(\d+)", hook)
    if not match:
        return
    h_num = match.group(1)

    if not os.path.exists(HYPOTHESIS_PATH):
        return

    with open(HYPOTHESIS_PATH, encoding="utf-8") as f:
        content = f.read()

    # 対象仮説ブロックを探す
    section_pattern = rf"(### H{h_num}:.*?)(?=\n### H|\Z)"
    section_match = re.search(section_pattern, content, re.DOTALL)
    if not section_match:
        return

    section = section_match.group(1)
    original_section = section

    # 投稿数の X/N を更新 (例: 1/5 → 2/5)
    def bump_count(m_obj):
        cur, total = int(m_obj.group(1)), m_obj.group(2)
        return f"- 投稿数: {cur + 1}/{total}"

    section = re.sub(r"- 投稿数: (\d+)/(\d+)[^\n]*", bump_count, section, count=1)

    # 現在のデータ行に新規結果を追記
    g = grade(m["imp"])
    new_data = (
        f"テスト{entry['date']}「{entry['text'][:20]}…」"
        f"→ {m['imp']:,} imp ({g}) / RT={m['rts']} ({m['rt_rate']}%)"
    )
    section = re.sub(
        r"(- 現在のデータ: [^\n]*)",
        lambda mo: mo.group(1) + f"。{new_data}",
        section,
        count=1,
    )

    if section != original_section:
        content = content[: section_match.start()] + section + content[section_match.end() :]
        with open(HYPOTHESIS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"active.md: H{h_num} 更新完了", file=sys.stderr)


def main():
    now_jst = datetime.now(JST)
    cutoff = now_jst - timedelta(hours=24)

    with open(SCHEDULE_PATH, encoding="utf-8") as f:
        schedule = json.load(f)

    # メトリクス未取得・tweet_id あり・24h以上経過のエントリを収集
    targets = []
    for entry in schedule:
        if not entry.get("posted"):
            continue
        if "metrics" in entry:
            continue
        if not entry.get("tweet_id"):
            continue
        posted_at_str = entry.get("posted_at")
        if posted_at_str:
            posted_dt = datetime.fromisoformat(posted_at_str)
            if posted_dt.tzinfo is None:
                posted_dt = posted_dt.replace(tzinfo=JST)
            if posted_dt > cutoff:
                print(
                    f"Skip (< 24h): {entry['date']} {entry['slot']}", file=sys.stderr
                )
                continue
        targets.append(entry)

    if not targets:
        print("メトリクス更新対象なし", file=sys.stderr)
        return

    auth = get_auth()
    metrics_map = fetch_tweet_metrics(auth, [e["tweet_id"] for e in targets])

    pdca_rows = []
    for entry in targets:
        m = metrics_map.get(entry["tweet_id"])
        if not m:
            print(f"メトリクス取得失敗: {entry['tweet_id']}", file=sys.stderr)
            continue

        entry["metrics"] = m
        g = grade(m["imp"])
        print(
            f"更新: {entry['date']} {entry['slot']} → {m['imp']:,} imp ({g}), RT={m['rts']}",
            file=sys.stderr,
        )

        # 仮説テスト投稿は active.md も更新
        if re.match(r"H\d+", entry.get("hook_pattern", "")):
            update_hypothesis(entry, m)

        pdca_rows.append(
            f"| {entry['date']} {entry['slot']} "
            f"| {entry.get('theme', '-')} "
            f"| {entry.get('hook_pattern', '-')} "
            f"| {m['imp']:,} ({g}) "
            f"| {m['rts']} ({m['rt_rate']}%) "
            f"| {m['likes']} "
            f"| {m['replies']} |"
        )

    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    if pdca_rows:
        header = (
            f"\n## {now_jst.strftime('%Y-%m-%d')} 自動取得\n\n"
            "| 日時 | テーマ | フック | imp | RT (率) | likes | replies |\n"
            "|---|---|---|---|---|---|---|\n"
        )
        log_block = header + "\n".join(pdca_rows) + "\n"
        with open(PDCA_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_block)
        print(f"pdca_log.md に {len(pdca_rows)} 件追記", file=sys.stderr)


if __name__ == "__main__":
    main()
