# X API v2 セットアップガイド

このガイドでは、PDCAアナライザーに必要な X API v2 の認証情報を取得する手順を説明する。

---

## 必要なプラン

| プラン | 月額 | 取得可能データ | 推奨度 |
|--------|------|-------------|--------|
| Free | $0 | 投稿のみ（読み取り不可） | ✗ 不可 |
| Basic | $200 | public_metrics（インプレ・いいね・RT・リプ・ブクマ） | ○ 十分 |
| Pro | $5,000 | public + non_public_metrics（プロフクリック・URLクリック等） | ◎ 完全 |

**Basicプラン（$200/月）で十分な分析が可能。** プロフィールクリック等の細かい指標が不要なら Basic で始めるのがおすすめ。

---

## Step 1: X Developer Portal でアプリを作成

1. https://developer.x.com/en/portal/dashboard にアクセス
2. X（Twitter）アカウントでログイン
3. 「Sign up for Free Account」→ 利用目的を入力して申請
4. 申請が承認されたら「Projects & Apps」でプロジェクトを作成
5. App の「Keys and tokens」ページで以下を取得:

### 取得する認証情報

| キー | 用途 | 必須度 |
|------|------|--------|
| Bearer Token | API読み取り（public_metrics） | 必須 |
| API Key | OAuth 1.0a 認証用 | 推奨 |
| API Key Secret | OAuth 1.0a 認証用 | 推奨 |
| Access Token | 自分のアカウントでの認証 | 推奨 |
| Access Token Secret | 自分のアカウントでの認証 | 推奨 |

Bearer Token だけでも基本的な分析は可能。
OAuth 1.0a（全5つ）があると non_public_metrics（プロフクリック等）も取得できる。

---

## Step 2: アプリの権限設定

1. Developer Portal → 作成したApp → 「Settings」
2. 「User authentication settings」→「Set up」
3. 以下を設定:
   - **App permissions**: `Read`（読み取りのみでOK）
   - **Type of App**: `Web App, Automated App or Bot`
   - **Callback URL**: `https://localhost`（使わないがダミーで入力）
   - **Website URL**: 任意のURL

---

## Step 3: .env ファイルに保存

プロジェクトルート（`ai-company/`）に `.env` ファイルを作成（または追記）:

```bash
# X API v2 認証情報
X_BEARER_TOKEN=AAAA...your_bearer_token...ZZZZ
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

`.env` は `.gitignore` に必ず追加すること（認証情報の流出防止）。

---

## Step 4: 動作確認

```bash
# 必要ライブラリのインストール
pip install requests python-dotenv requests-oauthlib --break-system-packages

# 動作テスト
python ai-company/skills/x-post-pdca-analyzer/scripts/fetch_tweet_metrics.py \
  --username ichi_eigo \
  --count 3
```

正常に動けば投稿3件分のJSON形式データが出力される。

---

## よくあるエラー

| エラー | 原因 | 対処 |
|--------|------|------|
| 401 Unauthorized | Bearer Tokenが無効 | Developer PortalでTokenを再生成 |
| 403 Forbidden | Freeプランでは読み取り不可 | Basicプラン以上にアップグレード |
| 429 Too Many Requests | レート制限到達 | 15分待つか、リクエスト回数を減らす |
| non_public_metrics error | OAuth 1.0aが未設定 | Access Token/Secretを.envに追加 |

---

## 複数アカウントの対応

`@ichi_eigo` と `@careermigaki` の両アカウントの投稿を分析する場合:

- **同一オーナーのアカウント**: 1つのAPIアプリから両方のpublic_metricsを取得可能
- **non_public_metrics**: 各アカウントの Access Token が必要。異なるアカウントの場合は、それぞれのトークンを `.env` に追加:

```bash
# メインアカウント
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...

# サブアカウント（必要な場合）
X_ACCESS_TOKEN_SUB=...
X_ACCESS_TOKEN_SECRET_SUB=...
```

public_metrics であれば Bearer Token 1つで両アカウントのデータを取得可能。
