# SaaS-C MVP機能仕様書

## MVPスコープ

「サイトURLを入力 → トピック提案 → Claude APIで記事生成 → Markdown/HTMLダウンロード」のみ。
Phase 1ではGitHub連携・課金は最小実装（Stripe Checkout）。

---

## 機能仕様

### 1. サイト登録フォーム

**入力パラメータ**:

| パラメータ | 型 | 説明 | 例 |
|---|---|---|---|
| サイトURL | text | 対象サイトのURL | https://example.com |
| サイトジャンル | select | アフィリ / ブログ / 比較サイト / その他 | アフィリ |
| メインKW | text | サイトのメインキーワード | 英語学習 |
| ターゲット読者 | text | 想定読者層 | 英語を勉強したい社会人 |
| 文体 | select | です・ます調 / だ・である調 | です・ます調 |

### 2. トピック自動提案

サイト情報を元にClaude APIが記事候補を10件提案:
- タイトル案（SEO最適化）
- 想定検索KW（月間検索ボリューム推定付き）
- 記事の方向性（レビュー / 比較 / ハウツー / ランキング）

### 3. 記事生成フォーム

**入力パラメータ**:

| パラメータ | 型 | 説明 | デフォルト |
|---|---|---|---|
| 記事タイトル | text | SEO最適化済みタイトル | 提案から選択 |
| 文字数 | select | 2,000 / 4,000 / 8,000文字 | 4,000 |
| セクション構成 | multi-select | 導入 / 本論 / 比較表 / CTA | 全選択 |
| アフィリリンク | text[] | 挿入するアフィリURLとサービス名 | なし |
| CTAテキスト | text | 記事末尾のCTA文言 | 無料で始める |

**生成フロー**:
1. ローディング表示（生成中... 残り約XX秒）
2. Claude API呼び出し（Streaming）
3. 記事プレビュー（Markdown レンダリング）
4. ダウンロードボタン（Markdown / HTML）

### 4. 出力フォーマット

#### Markdownフォーマット
```markdown
---
title: "タイトル"
description: "メタディスクリプション（120文字以内）"
date: "2026-04-02"
keywords: ["KW1", "KW2", "KW3"]
---

# タイトル

## はじめに
...

## セクション1
...

## まとめ
```

#### HTMLフォーマット
- semantic HTML5（article / section / h1〜h3）
- メタタグ・OGP込み
- native-real互換スタイル（オプション）

### 5. 認証・プラン管理（MVP最小実装）

- メール/パスワード認証（NextAuth.js）
- Freeプランは登録なしで月3記事まで（IPベース制限）
- 有料プランはStripe Checkoutへリダイレクト
- 使用量カウント: Supabase（articles_usageテーブル）

---

## 技術スタック

### フロントエンド
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS + shadcn/ui
- **Markdown**: react-markdown + remark-gfm
- **フォーム**: React Hook Form + Zod

### バックエンド
- **API Routes**: Next.js API Routes
- **AI**: Anthropic SDK（claude-sonnet-4-6）
- **DB**: Supabase（PostgreSQL）
- **認証**: NextAuth.js + Supabase adapter

### インフラ・外部サービス
- **Hosting**: Vercel（無料枠→Proプランへ）
- **決済**: Stripe（Checkout + Webhooks）
- **メール**: Resend（トランザクションメール）

---

## Claude APIプロンプト設計

### トピック提案プロンプト

```
あなたはSEOの専門家です。以下のサイト情報を元に、検索流入が見込める記事トピックを10件提案してください。

サイトURL: {site_url}
ジャンル: {genre}
メインKW: {main_kw}
ターゲット読者: {target_reader}

各トピックは以下の形式でJSON配列として出力してください:
[
  {
    "title": "記事タイトル（32文字以内）",
    "keyword": "メインキーワード",
    "estimated_volume": "月間検索ボリューム推定（例: 1,000〜5,000）",
    "type": "レビュー|比較|ハウツー|ランキング",
    "reason": "このトピックを選んだ理由（1文）"
  }
]
```

### 記事生成プロンプト

```
あなたはSEOライターです。以下の条件で日本語記事を生成してください。

タイトル: {title}
メインKW: {keyword}
文字数: 約{word_count}文字
文体: {writing_style}
ターゲット読者: {target_reader}

要件:
- h2見出し4〜6個、h3見出しを適宜使用
- キーワードを自然に3〜5回使用
- 読者の検索意図に完全に答える構成
- 最後にCTA: {cta_text}

Markdownで出力してください。
```

---

## データベース設計

```sql
-- ユーザーテーブル
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'free',  -- free / solo / growth / agency
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 登録サイトテーブル
CREATE TABLE sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  url TEXT NOT NULL,
  genre TEXT,
  main_kw TEXT,
  target_reader TEXT,
  writing_style TEXT DEFAULT 'polite',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 記事使用量テーブル
CREATE TABLE articles_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  ip_address TEXT,
  count INTEGER NOT NULL DEFAULT 0,
  period TEXT NOT NULL,  -- '2026-04' 形式（月次リセット）
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 生成記事テーブル
CREATE TABLE generated_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  site_id UUID REFERENCES sites(id),
  title TEXT NOT NULL,
  keyword TEXT,
  content_md TEXT NOT NULL,
  content_html TEXT,
  meta_description TEXT,
  word_count INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 実装計画（2週間スプリント）

### Week 1: コア機能

| Day | タスク |
|---|---|
| 1 | Next.jsプロジェクト作成、Vercelデプロイ設定 |
| 2 | サイト登録フォームUI実装 |
| 3 | Claude API連携（トピック提案API Route） |
| 4 | 記事生成フォームUI + Streaming実装 |
| 5 | Markdown/HTMLエクスポート、使用量制限（IP） |

### Week 2: 課金・公開準備

| Day | タスク |
|---|---|
| 6 | Supabase設定、ユーザー認証（NextAuth.js） |
| 7 | Stripe Checkout統合 |
| 8 | Stripeウェブフック、プラン別制限実装 |
| 9 | LP作成（料金表・native-real実績・CTA） |
| 10 | テスト・バグ修正・本番リリース |

---

## Phase 2: GitHub連携（MVP後）

native-realと同等の自動デプロイ機能を追加:

```python
# native-realのgithub_deploy.pyを参照実装
class GitHubDeployer:
    def commit_and_push(self, article_path: str, content: str):
        # 1. 記事ファイルをリポジトリに書き込み
        # 2. git add → commit → push
        # 3. GitHub Pages自動デプロイ
```

**連携フロー**:
1. ユーザーがGitHub OAuthで認証
2. 対象リポジトリを選択
3. 生成記事を自動コミット → GitHub Pages自動更新

---

## 先行販売戦略（Gumroad）

MVP完成前にGumroadで「アーリーアクセス」販売:
- 価格: ¥5,980（通常Soloプランの2ヶ月分相当）
- 対象: 先着30名
- 特典: 永久Soloプラン相当 + 1on1セットアップ支援（30分）
- 告知: native-real・note・X（Twitter）

---

## KPI・成功指標

| 指標 | 1ヶ月目 | 3ヶ月目 | 6ヶ月目 |
|---|---|---|---|
| 無料登録数 | 100 | 400 | 1,000 |
| 有料転換率 | - | 8% | 12% |
| MRR | ¥30,000 | ¥130,000 | ¥490,000 |
| Churn率 | - | < 8% | < 6% |
| 生成記事数/月 | 500 | 3,000 | 10,000 |

---

## 差別化ポイント（競合対策）

| 競合 | 弱点 | SaaS-Cの優位性 |
|---|---|---|
| Xwrite・BringFly等 | WordPress前提・英語UI | 静的サイト対応・完全日本語UI |
| ChatGPT直接利用 | 毎回プロンプト手入力 | テンプレート管理・SEO最適化済みプロンプト |
| 人力SEOライター | 高コスト（¥5〜15万/月） | 1/10以下のコストで同等品質 |
