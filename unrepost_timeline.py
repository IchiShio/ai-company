#!/usr/bin/env python3
"""@ichi_eigo のタイムラインを取得してリポストを全て取り消す（GitHub Actions用）
- repost_log.json に依存しない
- 環境変数から認証情報を取得
"""
import urllib.request, urllib.parse, hmac, hashlib, base64
import time, random, json, os, sys

USER_ID = '1182187111182749696'

def oauth_request(method, url, params=None, body=None):
    env = {
        'X_API_KEY':            os.environ['X_API_KEY'],
        'X_API_SECRET':         os.environ['X_API_SECRET'],
        'X_ACCESS_TOKEN':       os.environ['X_ACCESS_TOKEN'],
        'X_ACCESS_TOKEN_SECRET': os.environ['X_ACCESS_TOKEN_SECRET'],
    }
    if params is None:
        params = {}
    oauth_params = {
        'oauth_consumer_key':     env['X_API_KEY'],
        'oauth_nonce':            str(random.randint(100000000, 999999999)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp':        str(int(time.time())),
        'oauth_token':            env['X_ACCESS_TOKEN'],
        'oauth_version':          '1.0',
    }
    all_params = {**params, **oauth_params}
    sorted_params = '&'.join(
        f'{urllib.parse.quote(k, "")}'
        f'={urllib.parse.quote(str(v), "")}'
        for k, v in sorted(all_params.items())
    )
    base_url = url.split('?')[0]
    base_string = f'{method}&{urllib.parse.quote(base_url, "")}&{urllib.parse.quote(sorted_params, "")}'
    signing_key = (
        f'{urllib.parse.quote(env["X_API_SECRET"], "")}'
        f'&{urllib.parse.quote(env["X_ACCESS_TOKEN_SECRET"], "")}'
    )
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth_params['oauth_signature'] = signature
    auth_header = 'OAuth ' + ', '.join(
        f'{k}="{urllib.parse.quote(str(v), "")}"'
        for k, v in sorted(oauth_params.items())
    )
    if params and method == 'GET':
        query = urllib.parse.urlencode(params)
        full_url = f'{url}?{query}'
    else:
        full_url = url
    req = urllib.request.Request(full_url, method=method)
    req.add_header('Authorization', auth_header)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code


def fetch_retweets():
    """タイムラインからリポスト（RT）を全件取得"""
    retweet_ids = []
    pagination_token = None
    page = 1

    while True:
        params = {
            'tweet.fields': 'referenced_tweets',
            'expansions':   'referenced_tweets.id',
            'max_results':  '100',
            'exclude':      'replies',
        }
        if pagination_token:
            params['pagination_token'] = pagination_token

        print(f"  タイムライン取得中... ページ {page}")
        data, status = oauth_request(
            'GET',
            f'https://api.twitter.com/2/users/{USER_ID}/tweets',
            params=params
        )

        if status != 200:
            print(f"  タイムライン取得失敗: HTTP {status} -> {data}")
            break

        tweets = data.get('data', [])
        for tweet in tweets:
            refs = tweet.get('referenced_tweets', [])
            for ref in refs:
                if ref['type'] == 'retweeted':
                    retweet_ids.append(ref['id'])

        meta = data.get('meta', {})
        pagination_token = meta.get('next_token')
        if not pagination_token or not tweets:
            break
        page += 1
        time.sleep(1)

    return retweet_ids


def main():
    print("リポスト一覧を取得中...")
    retweet_ids = fetch_retweets()

    if not retweet_ids:
        print("リポストは見つかりませんでした。")
        return

    # 重複除去
    retweet_ids = list(dict.fromkeys(retweet_ids))
    print(f"\n{len(retweet_ids)} 件のリポストを取り消します。\n")

    success = 0
    failed = 0
    for tweet_id in retweet_ids:
        data, status = oauth_request(
            'DELETE',
            f'https://api.twitter.com/2/users/{USER_ID}/retweets/{tweet_id}'
        )
        if status == 200:
            print(f"  ✅ 取り消し: {tweet_id}")
            success += 1
        else:
            print(f"  ❌ 失敗: {tweet_id} -> HTTP {status} {data}")
            failed += 1
        time.sleep(1)  # レート制限対策

    print(f"\n完了: 成功 {success} 件 / 失敗 {failed} 件")


if __name__ == '__main__':
    main()
