"""
@ichi_eigoの直近投稿からいいね30+を取得してJSONに保存する。
OAuth 1.0a使用版。

使い方:
  source ai-company/.env && python3 scripts/fetch_popular_tweets.py
"""
import os, json, time
from datetime import datetime
from requests_oauthlib import OAuth1Session

USERNAME = "ichi_eigo"
MIN_LIKES = int(os.environ.get("MIN_LIKES", "30"))
OUTPUT = "data/popular_tweets.json"

API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

def get_oauth():
    return OAuth1Session(API_KEY, client_secret=API_SECRET,
                         resource_owner_key=ACCESS_TOKEN,
                         resource_owner_secret=ACCESS_TOKEN_SECRET)

def get_user_id(oauth, username):
    r = oauth.get(f"https://api.x.com/2/users/by/username/{username}")
    r.raise_for_status()
    return r.json()["data"]["id"]

def fetch_tweets(oauth, user_id, max_pages=5):
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    params = {
        "tweet.fields": "public_metrics,created_at,entities",
        "max_results": 100,
        "exclude": "retweets,replies"
    }
    all_tweets = []
    total_consumed = 0
    pagination_token = None

    for page in range(max_pages):
        if pagination_token:
            params["pagination_token"] = pagination_token

        r = oauth.get(url, params=params)

        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        r.raise_for_status()
        data = r.json()

        tweets = data.get("data", [])
        total_consumed += len(tweets)
        print(f"Page {page+1}: {len(tweets)} tweets fetched")

        for t in tweets:
            likes = t["public_metrics"]["like_count"]
            if likes >= MIN_LIKES:
                all_tweets.append({
                    "id": t["id"],
                    "text": t["text"],
                    "like_count": likes,
                    "retweet_count": t["public_metrics"]["retweet_count"],
                    "reply_count": t["public_metrics"]["reply_count"],
                    "impression_count": t["public_metrics"].get("impression_count", 0),
                    "created_at": t["created_at"],
                    "entities": t.get("entities", {})
                })

        pagination_token = data.get("meta", {}).get("next_token")
        if not pagination_token:
            break

        time.sleep(2)

    print(f"\nAPI consumed: {total_consumed} posts (monthly cap: 10,000)")
    print(f"Popular tweets (>={MIN_LIKES} likes): {len(all_tweets)}")
    return all_tweets

def main():
    if not API_KEY:
        print("ERROR: X_API_KEY not set")
        return

    oauth = get_oauth()
    user_id = get_user_id(oauth, USERNAME)
    print(f"User ID for @{USERNAME}: {user_id}")

    tweets = fetch_tweets(oauth, user_id)
    tweets.sort(key=lambda x: x["like_count"], reverse=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "min_likes": MIN_LIKES,
            "count": len(tweets),
            "tweets": tweets
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(tweets)} tweets to {OUTPUT}")
    if tweets:
        print(f"Top tweet: {tweets[0]['like_count']} likes - {tweets[0]['text'][:60]}...")

if __name__ == "__main__":
    main()
