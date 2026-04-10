#!/usr/bin/env python3
"""X API v2 で投稿するスクリプト。ローカル実行用（.envから認証情報を取得）。"""

import sys
import os
import requests
from requests_oauthlib import OAuth1
from pathlib import Path

# .env を読み込む（python-dotenvがなくても動くように自前実装）
def load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

load_env()


def get_auth():
    return OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
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
