#!/usr/bin/env python3
"""@ichi_eigo 過去リポストを全て取り消すスクリプト
- repost_log.json の全エントリに対して unretweet を実行
- 完了したエントリに unreposted_at を記録
"""
import urllib.request, urllib.parse, hmac, hashlib, base64
import time, random, json, os, sys

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repost_log.json')
USER_ID = '1182187111182749696'


def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    return env


def oauth_request(env, method, url, params=None, body=None):
    if params is None:
        params = {}
    oauth_params = {
        'oauth_consumer_key': env['X_API_KEY'],
        'oauth_nonce': str(random.randint(100000000, 999999999)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': env['X_ACCESS_TOKEN'],
        'oauth_version': '1.0'
    }
    all_params = {**params, **oauth_params}
    sorted_params = '&'.join(
        f'{urllib.parse.quote(k, "")}'
        f'={urllib.parse.quote(str(v), "")}'
        for k, v in sorted(all_params.items())
    )
    base_string = f'{method}&{urllib.parse.quote(url, "")}&{urllib.parse.quote(sorted_params, "")}'
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
    full_url = url
    req = urllib.request.Request(full_url, method=method)
    req.add_header('Authorization', auth_header)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(body).encode()
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    env = load_env(ENV_PATH)

    try:
        with open(LOG_PATH) as f:
            repost_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No repost log found.")
        return

    if not repost_log:
        print("No reposts to undo.")
        return

    # Deduplicate by tweet_id (keep latest entry)
    seen = set()
    unique_ids = []
    for entry in reversed(repost_log):
        if entry['tweet_id'] not in seen:
            seen.add(entry['tweet_id'])
            unique_ids.append(entry['tweet_id'])
    unique_ids.reverse()

    print(f"Found {len(unique_ids)} unique tweets to unrepost.")

    success = 0
    failed = 0
    for tweet_id in unique_ids:
        try:
            result = oauth_request(env, 'DELETE',
                f'https://api.twitter.com/2/users/{USER_ID}/retweets/{tweet_id}'
            )
            print(f"  Unreposted: {tweet_id} -> {result}")
            success += 1
        except urllib.error.HTTPError as e:
            print(f"  Failed: {tweet_id} -> HTTP {e.code}")
            failed += 1
        # Rate limit: small delay between requests
        time.sleep(1)

    print(f"\nDone. Success: {success}, Failed: {failed}")

    # Clear the log
    with open(LOG_PATH, 'w') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print("Cleared repost_log.json")


if __name__ == '__main__':
    main()
