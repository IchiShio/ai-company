#!/usr/bin/env python3
"""X API v2 で直近投稿のパフォーマンスデータを取得する。"""

import os
import json
import sys
import requests
from requests_oauthlib import OAuth1


def get_auth():
    return OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def get_user_id(auth):
    resp = requests.get("https://api.x.com/2/users/me", auth=auth)
    print(f"GET /2/users/me -> {resp.status_code}", file=sys.stderr)
    if resp.status_code != 200:
        print(f"Response: {resp.text}", file=sys.stderr)
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def get_recent_tweets(auth, user_id, max_results=10):
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,text",
        "exclude": "retweets,replies",
    }
    resp = requests.get(
        f"https://api.x.com/2/users/{user_id}/tweets",
        params=params,
        auth=auth,
    )
    print(f"GET /2/users/{user_id}/tweets -> {resp.status_code}", file=sys.stderr)
    if resp.status_code != 200:
        print(f"Response: {resp.text}", file=sys.stderr)
    resp.raise_for_status()
    return resp.json()


def main():
    auth = get_auth()
    user_id = get_user_id(auth)
    data = get_recent_tweets(auth, user_id, max_results=20)

    if "data" not in data:
        print("No tweets found", file=sys.stderr)
        return
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
