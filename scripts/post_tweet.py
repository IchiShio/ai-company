#!/usr/bin/env python3
"""X API v2 で投稿するスクリプト。cronから呼び出される。"""

import sys
import os
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/projects/claude/ai-company/.env"))

auth = OAuth1(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_TOKEN_SECRET"),
)

def post_tweet(text):
    resp = requests.post(
        "https://api.x.com/2/tweets",
        json={"text": text},
        auth=auth,
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        tweet_id = data["data"]["id"]
        print(f"OK: https://x.com/ichi_eigo/status/{tweet_id}")
        return True
    else:
        print(f"ERROR {resp.status_code}: {resp.text}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 post_tweet.py <text>", file=sys.stderr)
        sys.exit(1)
    text = sys.argv[1]
    success = post_tweet(text)
    sys.exit(0 if success else 1)
