#!/usr/bin/env python3
"""X API v2 で直近投稿のパフォーマンスデータを取得する。"""

import os
import json
import requests


def bearer_headers():
    token = os.environ["X_BEARER_TOKEN"]
    return {"Authorization": f"Bearer {token}"}


def get_user_id():
    resp = requests.get("https://api.x.com/2/users/me", headers=bearer_headers())
    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def get_recent_tweets(user_id, max_results=10):
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,text",
        "exclude": "retweets,replies",
    }
    resp = requests.get(
        f"https://api.x.com/2/users/{user_id}/tweets",
        params=params,
        headers=bearer_headers(),
    )
    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()


def main():
    user_id = get_user_id()
    data = get_recent_tweets(user_id, max_results=10)

    if "data" not in data:
        print("No tweets found")
        return

    print("date,text_preview,impressions,likes,retweets,replies,quotes,bookmarks")
    for tweet in data["data"]:
        m = tweet.get("public_metrics", {})
        text_preview = tweet["text"][:40].replace(",", " ").replace("\n", " ")
        created = tweet["created_at"][:10]
        imp = m.get("impression_count", 0)
        likes = m.get("like_count", 0)
        rts = m.get("retweet_count", 0)
        replies = m.get("reply_count", 0)
        quotes = m.get("quote_count", 0)
        bookmarks = m.get("bookmark_count", 0)
        print(f"{created},{text_preview},{imp},{likes},{rts},{replies},{quotes},{bookmarks}")


if __name__ == "__main__":
    main()
