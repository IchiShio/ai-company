#!/usr/bin/env python3
"""@ichi_eigo 24時間経過したリポストを自動取り消し
- repost_log.json から24時間以上経過したエントリを unretweet
- 取り消し済みエントリはログから削除
"""
import urllib.request, urllib.parse, hmac, hashlib, base64
import time, random, json, os, datetime

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repost_log.json')
USER_ID = '1182187111182749696'
EXPIRE_HOURS = 24


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
        print("No reposts in log.")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    expire_delta = datetime.timedelta(hours=EXPIRE_HOURS)

    expired = []
    remaining = []
    for entry in repost_log:
        reposted_at = datetime.datetime.fromisoformat(entry['reposted_at'])
        if now - reposted_at >= expire_delta:
            expired.append(entry)
        else:
            remaining.append(entry)

    if not expired:
        print("No expired reposts to remove.")
        return

    # Deduplicate expired tweet_ids (unretweet each only once)
    seen = set()
    unique_expired = []
    for entry in expired:
        if entry['tweet_id'] not in seen:
            seen.add(entry['tweet_id'])
            unique_expired.append(entry)

    # Also skip if the tweet_id is still in remaining (recently reposted again)
    remaining_ids = {e['tweet_id'] for e in remaining}
    to_unrepost = [e for e in unique_expired if e['tweet_id'] not in remaining_ids]

    print(f"Found {len(expired)} expired entries ({len(to_unrepost)} unique to unrepost).")

    success = 0
    failed = 0
    for entry in to_unrepost:
        try:
            result = oauth_request(env, 'DELETE',
                f'https://api.twitter.com/2/users/{USER_ID}/retweets/{entry["tweet_id"]}'
            )
            print(f"  Unreposted: {entry['tweet_id']} -> {result}")
            success += 1
        except urllib.error.HTTPError as e:
            print(f"  Failed: {entry['tweet_id']} -> HTTP {e.code}")
            failed += 1
        time.sleep(1)

    # Keep only non-expired entries
    with open(LOG_PATH, 'w') as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Unreposted: {success}, Failed: {failed}, Remaining in log: {len(remaining)}")


if __name__ == '__main__':
    main()
