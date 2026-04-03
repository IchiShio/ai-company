#!/usr/bin/env python3
"""X API v2 で投稿する（GitHub Actions用）。環境変数から認証情報を取得。"""

import sys
import os
import requests
from requests_oauthlib import OAuth1


def post_tweet(text):
    auth = OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = requests.post(
        "https://api.x.com/2/tweets",
        json={"text": text},
        auth=auth,
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        tweet_id = data["data"]["id"]
        print(f"OK: https://x.com/ichi_eigo/status/{tweet_id}")
        # GitHub Actions の後続ステップに tweet_id を渡す
        github_output = os.environ.get("GITHUB_OUTPUT", "")
        if github_output:
            with open(github_output, "a") as fh:
                fh.write(f"tweet_id={tweet_id}\n")
        return True
    else:
        print(f"ERROR {resp.status_code}: {resp.text}", file=sys.stderr)
        return False


if __name__ == "__main__":
    text = os.environ.get("POST_TEXT", "").strip()
    if not text and len(sys.argv) >= 2:
        text = sys.argv[1]
    if not text:
        print("ERROR: POST_TEXT env var or argument required", file=sys.stderr)
        sys.exit(1)
    success = post_tweet(text)
    sys.exit(0 if success else 1)
