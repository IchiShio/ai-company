#!/usr/bin/env python3
"""X API v2 で投稿するスクリプト。cronから呼び出される。"""

import sys
import os
import subprocess
import requests
from requests_oauthlib import OAuth1

OP_ITEM = "X API - @ichi_eigo"
OP_ACCOUNT = "my.1password.com"


def op_read(field):
    """1Passwordからフィールドを取得する。"""
    result = subprocess.run(
        ["op", "read", f"op://Private/{OP_ITEM}/{field}", "--account", OP_ACCOUNT],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"op read failed for {field}: {result.stderr.strip()}")
    return result.stdout.strip()


def get_auth():
    return OAuth1(
        op_read("X_API_KEY"),
        op_read("X_API_SECRET"),
        op_read("X_ACCESS_TOKEN"),
        op_read("X_ACCESS_TOKEN_SECRET"),
    )

def post_tweet(text):
    auth = get_auth()
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
