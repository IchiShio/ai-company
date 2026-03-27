#!/usr/bin/env python3
"""@ichi_eigo リポストスクリプト
- いいね20超の投稿からランダムに1件リポスト
- 4日以内にリポスト済みの投稿は除外
"""
import urllib.request, urllib.parse, hmac, hashlib, base64
import time, random, json, os, datetime, sys

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repost_log.json')
USER_ID = '1182187111182749696'
LIKE_THRESHOLD = 20
COOLDOWN_DAYS = 4

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
        f'{urllib.parse.quote(k,"")}'
        f'={urllib.parse.quote(str(v),"")}'
        for k, v in sorted(all_params.items())
    )
    base_string = f'{method}&{urllib.parse.quote(url,"")}&{urllib.parse.quote(sorted_params,"")}'
    signing_key = (
        f'{urllib.parse.quote(env["X_API_SECRET"],"")}'
        f'&{urllib.parse.quote(env["X_ACCESS_TOKEN_SECRET"],"")}'
    )
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth_params['oauth_signature'] = signature
    auth_header = 'OAuth ' + ', '.join(
        f'{k}="{urllib.parse.quote(str(v),"")}"'
        for k, v in sorted(oauth_params.items())
    )
    query = '&'.join(f'{k}={urllib.parse.quote(str(v),"")}' for k, v in params.items())
    full_url = f'{url}?{query}' if query else url
    req = urllib.request.Request(full_url, method=method)
    req.add_header('Authorization', auth_header)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(body).encode()
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    env = load_env(ENV_PATH)

    # Fetch tweets
    data = oauth_request(env, 'GET',
        f'https://api.twitter.com/2/users/{USER_ID}/tweets',
        params={
            'max_results': '100',
            'tweet.fields': 'public_metrics,created_at',
            'exclude': 'retweets,replies'
        }
    )
    candidates = [t for t in data.get('data', [])
                  if t['public_metrics']['like_count'] > LIKE_THRESHOLD]

    # Load log, filter cooldown
    try:
        with open(LOG_PATH) as f:
            repost_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        repost_log = []

    now = datetime.datetime.now(datetime.timezone.utc)
    cooldown = datetime.timedelta(days=COOLDOWN_DAYS)
    recent_ids = {
        e['tweet_id'] for e in repost_log
        if now - datetime.datetime.fromisoformat(e['reposted_at']) < cooldown
    }

    eligible = [t for t in candidates if t['id'] not in recent_ids]
    if not eligible:
        print("No eligible tweets to repost.")
        return

    # Random pick & repost
    chosen = random.choice(eligible)
    result = oauth_request(env, 'POST',
        f'https://api.twitter.com/2/users/{USER_ID}/retweets',
        body={'tweet_id': chosen['id']}
    )
    print(f"Reposted: {chosen['id']} (likes={chosen['public_metrics']['like_count']})")
    print(f"  {chosen['text'][:80]}")
    print(f"  Result: {result}")

    # Update log
    repost_log.append({
        'tweet_id': chosen['id'],
        'text_preview': chosen['text'][:80],
        'likes': chosen['public_metrics']['like_count'],
        'reposted_at': now.isoformat()
    })
    with open(LOG_PATH, 'w') as f:
        json.dump(repost_log, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
