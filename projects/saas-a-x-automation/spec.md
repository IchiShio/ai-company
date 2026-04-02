# SaaS-A MVP機能仕様書

## MVPスコープ

「テーマを入力 → Claude APIで投稿案を複数生成 → コピーして手動投稿」のみ。
Phase 1ではX API自動投稿・スケジュール機能は含まない（X API申請・審査コスト回避）。
Stripe Checkoutによる最小課金実装を含む。

---

## 機能仕様

### 1. アカウント設定フォーム

ユーザーのX運用コンテキストを登録:

| パラメータ | 型 | 説明 | 例 |
|---|---|---|---|
| Xアカウント名 | text | @handle（表示用） | @example_user |
| ジャンル | select | ビジネス / 副業 / エンタメ / 学習 / その他 | 副業 |
| ペルソナ | textarea | どんな人として発信するか | 本業会社員×副業ブロガー、AI活用で月5万円稼ぐ方法を発信 |
| 投稿スタイル | select | 丁寧・ポップ・ストイック・カジュアル | ポップ |
| 投稿テーマ（複数） | tags | 主要テーマ | AI活用, 副業, Claude Code |

### 2. AI投稿生成フォーム

**入力パラメータ**:

| パラメータ | 型 | 説明 | デフォルト |
|---|---|---|---|
| 生成モード | radio | テーマ自由入力 / 記事URL変換 / トレンド活用 | テーマ自由入力 |
| テーマ/入力テキスト | textarea | 投稿のネタ・URLなど | - |
| 投稿形式 | select | 単発 / スレッド(3〜5ツイート) / 引用リポスト風 | 単発 |
| 生成数 | select | 3案 / 5案 / 10案 | 5案 |
| CTA | checkbox | フォロー促進 / いいね促進 / リンク誘導 / なし | なし |

**生成フロー**:
1. ローディング表示（生成中...）
2. Claude API呼び出し（Streaming）
3. 投稿案カード表示（各案にコピーボタン付き）
4. 気に入った案を「保存」してカレンダーに追加可能

### 3. 投稿管理カレンダー（MVP: 簡易版）

- 生成した投稿案を日付別に保存・管理
- 投稿ステータス管理: 未投稿 / 投稿済み
- MVPでは自動投稿なし（手動コピー&投稿フロー）

### 4. 簡易パフォーマンスメモ（MVP: 手動入力）

- 投稿後にインプレッション数・いいね数を手動入力
- 週次グラフで推移確認
- 「バズった投稿」のタグ付け → 次回生成時の参考データに反映

### 5. 認証・プラン管理

- Google OAuth（NextAuth.js）
- Freeプランは未認証で月10投稿まで生成可（ローカルストレージで管理）
- 有料プランはStripe Checkoutへリダイレクト
- 使用量カウント: Supabase（generations_usageテーブル）

---

## 技術スタック

### フロントエンド
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS + shadcn/ui
- **カレンダー**: react-big-calendar または 独自実装（シンプル版）
- **フォーム**: React Hook Form + Zod
- **グラフ**: Recharts（パフォーマンス表示）

### バックエンド
- **API Routes**: Next.js API Routes
- **AI**: Anthropic SDK（claude-sonnet-4-6）
- **DB**: Supabase（PostgreSQL）
- **認証**: NextAuth.js + Google OAuth + Supabase adapter

### インフラ・外部サービス
- **Hosting**: Vercel
- **決済**: Stripe（Checkout + Webhooks）
- **メール**: Resend（登録確認・週次レポートメール）

---

## Claude APIプロンプト設計

### 単発投稿生成プロンプト

```
あなたはX（Twitter）マーケティングの専門家です。
以下の条件でXの投稿文を{count}案生成してください。

【発信者情報】
ペルソナ: {persona}
投稿スタイル: {style}
ジャンル: {genre}

【今回の投稿条件】
テーマ/ネタ: {theme}
投稿形式: 単発ツイート（140文字以内）
CTA: {cta}

【重要ルール】
- 140文字以内（URLや改行は文字数にカウント）
- 最初の1〜2文で興味を引く
- 具体的な数字・事例を含める（可能な場合）
- ハッシュタグは0〜2個まで

JSON配列で出力してください:
[
  {
    "text": "投稿テキスト",
    "estimated_engagement": "高|中|低",
    "reason": "このテキストを提案した理由（1文）"
  }
]
```

### スレッド生成プロンプト

```
あなたはX（Twitter）マーケティングの専門家です。
以下の条件でXのスレッド投稿（{thread_count}ツイート）を生成してください。

【発信者情報】
ペルソナ: {persona}
投稿スタイル: {style}

【スレッドの内容】
テーマ: {theme}
参考テキスト/URL内容: {source_text}

【重要ルール】
- 1ツイート目: フック（興味を引く問いかけや驚きの事実）
- 2〜{thread_count-1}ツイート目: 本論（各140文字以内）
- 最終ツイート: まとめ + CTA（フォロー促進 or リンク誘導）

JSON配列で出力してください:
[
  {"index": 1, "text": "1ツイート目のテキスト"},
  {"index": 2, "text": "2ツイート目のテキスト"},
  ...
]
```

### PDCA自動反映（Phase 3）

```
以下のパフォーマンスデータを分析して、今後の投稿改善方針をまとめてください。

【過去30日のデータ】
バズった投稿（インプレッション上位5件）:
{top_posts}

振るわなかった投稿（エンゲージメント率下位5件）:
{bottom_posts}

【分析してほしいこと】
1. バズった投稿の共通パターン（文体・構成・テーマ）
2. 振るわなかった投稿の改善点
3. 次の30日で試すべき投稿スタイルの推奨（具体的に3つ）

JSON形式で出力してください。
```

---

## データベース設計

```sql
-- ユーザーテーブル
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'free',  -- free / starter / pro / business
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Xアカウント設定テーブル
CREATE TABLE x_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  handle TEXT NOT NULL,          -- @username
  persona TEXT,
  genre TEXT,
  posting_style TEXT DEFAULT 'casual',
  themes TEXT[],                 -- 投稿テーマタグ
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 生成投稿テーブル
CREATE TABLE generated_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  account_id UUID REFERENCES x_accounts(id),
  mode TEXT NOT NULL,            -- single / thread / quote
  theme TEXT,
  content JSONB NOT NULL,        -- 生成結果（複数案）
  selected_text TEXT,            -- 実際に使った投稿
  status TEXT DEFAULT 'draft',   -- draft / posted
  scheduled_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- パフォーマンスメモテーブル
CREATE TABLE performance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID REFERENCES generated_posts(id),
  impressions INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  reposts INTEGER DEFAULT 0,
  replies INTEGER DEFAULT 0,
  is_viral BOOLEAN DEFAULT FALSE,
  posted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 生成使用量テーブル
CREATE TABLE generations_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  ip_address TEXT,
  count INTEGER NOT NULL DEFAULT 0,
  period TEXT NOT NULL,          -- '2026-04' 形式（月次リセット）
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 実装計画（2週間スプリント）

### Week 1: コア機能

| Day | タスク |
|---|---|
| 1 | Next.jsプロジェクト作成、Vercelデプロイ設定、Supabase初期化 |
| 2 | Google OAuth認証（NextAuth.js）、ユーザー登録フロー |
| 3 | Xアカウント設定フォームUI実装 |
| 4 | Claude API連携（投稿生成API Route + Streaming） |
| 5 | 投稿生成フォームUI + 結果カード（コピーボタン付き） |

### Week 2: 管理・課金・公開

| Day | タスク |
|---|---|
| 6 | 生成投稿管理カレンダー（簡易版）、ステータス管理 |
| 7 | パフォーマンスメモ機能 + Rechartsグラフ |
| 8 | Stripe Checkout統合、プラン別生成上限実装 |
| 9 | LP作成（差別化訴求・料金表・無料トライアルCTA） |
| 10 | テスト・バグ修正・本番リリース |

---

## Phase 2: X API自動投稿（MVP後）

X API v2を使った自動スケジュール投稿:

```typescript
// X API v2 投稿
async function postTweet(text: string, accessToken: string): Promise<string> {
  const response = await fetch('https://api.twitter.com/2/tweets', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
  const data = await response.json();
  return data.data.id;
}
```

**実装フロー**:
1. ユーザーがX OAuth 2.0で認証（PKCE）
2. アクセストークンをSupabaseに暗号化保存
3. Vercel Cron Jobsで指定時刻に自動投稿
4. 投稿結果をperformance_logsに自動記録

---

## 先行販売戦略（Gumroad）

MVP完成前にGumroadで「アーリーアクセス」販売:
- 価格: ¥3,980（通常Starterプランの2ヶ月分相当）
- 対象: 先着50名
- 特典: 永久Starterプラン相当 + 個別ペルソナ設定サポート（DM対応）
- 告知: note・X（Twitter）・native-realメルマガ

---

## KPI・成功指標

| 指標 | 1ヶ月目 | 3ヶ月目 | 6ヶ月目 |
|---|---|---|---|
| 無料登録数 | 200 | 800 | 2,000 |
| 有料転換率 | - | 6% | 10% |
| MRR | ¥50,000 | ¥150,000 | ¥570,000 |
| Churn率 | - | < 10% | < 7% |
| 月間生成投稿数 | 3,000 | 15,000 | 50,000 |

---

## 差別化ポイント（競合対策）

| 競合 | 弱点 | SaaS-Aの優位性 |
|---|---|---|
| Buffer / Hootsuite | スケジュール特化、AI弱い | Claude APIによる高品質日本語生成 |
| Lately | 英語UI・英語コンテンツ前提 | 日本語X特化・日本語ペルソナ最適化 |
| ChatGPT直接利用 | 毎回プロンプト手入力、管理不可 | ペルソナ記憶・投稿管理・PDCA自動化 |
| 国産スケジューラー各種 | AI生成なし | 生成+管理+PDCA一体型 |
