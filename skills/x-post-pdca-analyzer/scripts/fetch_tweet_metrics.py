#!/usr/bin/env python3
"""
X API v2 を使って指定ユーザーの直近投稿＋メトリクスを取得する。
PDCAアナライザーのデータ収集ステップで使用。

使い方:
  python fetch_tweet_metrics.py --username ichi_eigo --count 10 --output /tmp/tweet_metrics.json

環境変数（.env から読み込み）:
  X_BEARER_TOKEN          (必須) Bearer Token
  X_API_KEY               (任意) OAuth 1.0a 用
  X_API_SECRET            (任意) OAuth 1.0a 用
  X_ACCESS_TOKEN          (任意) OAuth 1.0a 用
  X_ACCESS_TOKEN_SECRET   (任意) OAuth 1.0a 用
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    import requests
except ImportError:
    print("ERROR: requests ライブラリが必要です。pip install requests --break-system-packages")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv がなくても環境変数から直接読む

JST = timezone(timedelta(hours=9))
BASE_URL = "https://api.x.com/2"


def get_bearer_headers():
    token = os.getenv("X_BEARER_TOKEN")
    if not token:
        print("ERROR: X_BEARER_TOKEN が設定されていません。")
        print("  .env ファイルに X_BEARER_TOKEN=xxx を設定してください。")
        print("  詳しくは references/api-setup-guide.md を参照。")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}"}


def has_oauth1_credentials():
    """OAuth 1.0a の認証情報が全て揃っているか確認"""
    keys = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    return all(os.getenv(k) for k in keys)


def get_oauth1_session():
    """OAuth 1.0a セッションを返す（requests_oauthlib 使用）"""
    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        return None

    auth = OAuth1(
        os.getenv("X_API_KEY"),
        os.getenv("X_API_SECRET"),
        os.getenv("X_ACCESS_TOKEN"),
        os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    return auth


def get_user_id(username: str, headers: dict) -> str:
    """ユーザー名からユーザーIDを取得"""
    resp = requests.get(
        f"{BASE_URL}/users/by/username/{username}",
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()
    if "data" not in data:
        print(f"ERROR: ユーザー @{username} が見つかりません。")
        print(f"  APIレスポンス: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)
    return data["data"]["id"]


def fetch_tweets(user_id: str, count: int, headers: dict, oauth1=None):
    """直近の投稿をメトリクス付きで取得"""

    # 使用するメトリクスフィールドを決定
    tweet_fields = [
        "created_at",
        "public_metrics",
        "entities",
        "attachments",
        "text",
    ]

    # OAuth 1.0a があれば non_public_metrics も要求
    use_non_public = False
    if oauth1:
        tweet_fields.append("non_public_metrics")
        tweet_fields.append("organic_metrics")
        use_non_public = True

    params = {
        "max_results": min(count, 100),
        "tweet.fields": ",".join(tweet_fields),
        "media.fields": "type,url,preview_image_url",
        "expansions": "attachments.media_keys",
        "exclude": "retweets,replies",
    }

    # OAuth 1.0a がある場合はそちらを使う（non_public_metrics 取得のため）
    if oauth1:
        resp = requests.get(
            f"{BASE_URL}/users/{user_id}/tweets",
            params=params,
            auth=oauth1,
        )
    else:
        resp = requests.get(
            f"{BASE_URL}/users/{user_id}/tweets",
            headers=headers,
            params=params,
        )

    if resp.status_code == 401:
        print("ERROR: 認証エラー (401)。トークンが無効または期限切れです。")
        sys.exit(1)
    elif resp.status_code == 403:
        if use_non_public:
            # non_public_metrics が使えない場合、public_metrics のみで再試行
            print("WARNING: non_public_metrics が利用不可。public_metrics のみで取得します。")
            tweet_fields = [f for f in tweet_fields if f not in ("non_public_metrics", "organic_metrics")]
            params["tweet.fields"] = ",".join(tweet_fields)
            use_non_public = False
            resp = requests.get(
                f"{BASE_URL}/users/{user_id}/tweets",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
        else:
            print("ERROR: アクセス拒否 (403)。APIプラン（Basic以上: $200/月）が必要です。")
            sys.exit(1)
    elif resp.status_code == 429:
        reset = resp.headers.get("x-rate-limit-reset", "不明")
        print(f"ERROR: レート制限 (429)。リセット時刻: {reset}")
        sys.exit(1)
    else:
        resp.raise_for_status()

    return resp.json(), use_non_public


def process_tweets(raw_data: dict, username: str, use_non_public: bool) -> dict:
    """APIレスポンスを分析用の構造化データに変換"""

    tweets = raw_data.get("data", [])
    media_map = {}
    if "includes" in raw_data and "media" in raw_data["includes"]:
        for m in raw_data["includes"]["media"]:
            media_map[m["media_key"]] = m

    results = []
    for tw in tweets:
        pm = tw.get("public_metrics", {})
        npm = tw.get("non_public_metrics", {})

        # 投稿日時をJSTに変換
        created_utc = datetime.fromisoformat(tw["created_at"].replace("Z", "+00:00"))
        created_jst = created_utc.astimezone(JST)

        # メディアタイプ判定
        media_types = []
        if "attachments" in tw and "media_keys" in tw["attachments"]:
            for mk in tw["attachments"]["media_keys"]:
                if mk in media_map:
                    media_types.append(media_map[mk].get("type", "unknown"))

        # エンティティ抽出
        entities = tw.get("entities", {})
        hashtags = [h["tag"] for h in entities.get("hashtags", [])]
        urls = [u["expanded_url"] for u in entities.get("urls", [])]
        mentions = [m["username"] for m in entities.get("mentions", [])]

        # メトリクス
        impressions = pm.get("impression_count", 0)
        likes = pm.get("like_count", 0)
        retweets = pm.get("retweet_count", 0)
        replies = pm.get("reply_count", 0)
        quotes = pm.get("quote_count", 0)
        bookmarks = pm.get("bookmark_count", 0)

        entry = {
            "tweet_id": tw["id"],
            "created_at": created_jst.strftime("%Y-%m-%d %H:%M"),
            "weekday": ["月", "火", "水", "木", "金", "土", "日"][created_jst.weekday()],
            "hour": created_jst.hour,
            "text": tw["text"],
            "text_length": len(tw["text"]),
            "first_line": tw["text"].split("\n")[0][:50],
            "media_types": media_types,
            "hashtags": hashtags,
            "urls": urls,
            "mentions": mentions,
            "metrics": {
                "impressions": impressions,
                "likes": likes,
                "retweets": retweets,
                "replies": replies,
                "quotes": quotes,
                "bookmarks": bookmarks,
                "reposts_total": retweets + quotes,
            },
        }

        # non_public_metrics があれば追加
        if use_non_public and npm:
            entry["metrics"]["profile_clicks"] = npm.get("user_profile_clicks", 0)
            entry["metrics"]["url_clicks"] = npm.get("url_link_clicks", 0)

        # KPI算出
        if impressions > 0:
            engagement_total = likes + retweets + quotes + replies + bookmarks
            entry["kpi"] = {
                "engagement_rate": round(engagement_total / impressions * 100, 2),
                "like_rate": round(likes / impressions * 100, 2),
                "repost_rate": round((retweets + quotes) / impressions * 100, 2),
                "reply_rate": round(replies / impressions * 100, 2),
                "bookmark_rate": round(bookmarks / impressions * 100, 2),
            }
            if use_non_public and npm:
                pc = npm.get("user_profile_clicks", 0)
                entry["kpi"]["profile_click_rate"] = round(pc / impressions * 100, 2)
        else:
            entry["kpi"] = {}

        results.append(entry)

    return {
        "account": f"@{username}",
        "fetched_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "tweet_count": len(results),
        "has_non_public_metrics": use_non_public,
        "tweets": results,
    }


def main():
    parser = argparse.ArgumentParser(description="X投稿メトリクス取得ツール")
    parser.add_argument("--username", required=True, help="Xユーザー名（@なし）")
    parser.add_argument("--count", type=int, default=10, help="取得件数（デフォルト: 10）")
    parser.add_argument("--output", default=None, help="出力JSONファイルパス（省略時は標準出力）")
    args = parser.parse_args()

    headers = get_bearer_headers()

    # OAuth 1.0a の確認
    oauth1 = None
    if has_oauth1_credentials():
        oauth1 = get_oauth1_session()
        if oauth1:
            print("INFO: OAuth 1.0a 認証を使用（non_public_metrics 取得可能）")
        else:
            print("WARNING: requests_oauthlib 未インストール。Bearer Token のみで取得します。")
            print("  pip install requests-oauthlib --break-system-packages")
    else:
        print("INFO: Bearer Token のみで取得（public_metrics のみ）")

    # ユーザーID取得
    print(f"INFO: @{args.username} のユーザーIDを取得中...")
    user_id = get_user_id(args.username, headers)
    print(f"INFO: ユーザーID = {user_id}")

    # ツイート取得
    print(f"INFO: 直近 {args.count} 件の投稿を取得中...")
    raw_data, use_non_public = fetch_tweets(user_id, args.count, headers, oauth1)

    # データ整形
    result = process_tweets(raw_data, args.username, use_non_public)

    # 出力
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"INFO: {args.output} に保存しました（{result['tweet_count']} 件）")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
