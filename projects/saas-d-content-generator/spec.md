# SaaS-D MVP機能仕様書

## MVPスコープ

「問題生成フォームに入力 → Claude APIで問題生成 → JSON/CSVダウンロード」のみ。
認証・課金は最小実装（Stripe Checkout）。

---

## 機能仕様

### 1. 問題生成フォーム

**入力パラメータ**:

| パラメータ | 型 | 説明 | デフォルト |
|---|---|---|---|
| 問題タイプ | select | grammar / vocabulary / reading | grammar |
| 難易度 | select | 初級 / 中級 / 上級 | 中級 |
| 文法項目 | multi-select | 時制・冠詞・前置詞・関係詞・仮定法など | 全項目 |
| 生成数 | number | 5〜50問 | 10 |
| 出力形式 | select | 4択 / 穴埋め / 並び替え | 4択 |
| 説明文言語 | select | 日本語 / 英語 | 日本語 |

**生成ボタン押下後**:
1. ローディング表示（生成中...）
2. Claude API呼び出し（Streaming対応）
3. 問題プレビュー表示
4. ダウンロードボタン表示（JSON / CSV）

### 2. 問題フォーマット（JSON）

```json
{
  "meta": {
    "generated_at": "2026-03-30T00:00:00Z",
    "type": "grammar",
    "level": "intermediate",
    "count": 10
  },
  "questions": [
    {
      "id": "g001",
      "question": "She ___ to school every day.",
      "options": [
        "A. go",
        "B. goes",
        "C. going",
        "D. gone"
      ],
      "answer": "B",
      "explanation": "三人称単数現在形では動詞にsを付けます。",
      "grammar_point": "三単現のs"
    }
  ]
}
```

### 3. CSVフォーマット

```
id,question,option_a,option_b,option_c,option_d,answer,explanation,grammar_point
g001,"She ___ to school every day.",go,goes,going,gone,B,三人称単数現在形では動詞にsを付けます。,三単現のs
```

### 4. 認証・プラン管理（MVP最小実装）

- メール/パスワード認証（NextAuth.js）
- Free Trialは登録なしで月50問まで使用可（IPベース制限）
- 有料プランはStripe Checkoutへリダイレクト
- 使用量カウント: Supabase（questions_usageテーブル）

---

## 技術スタック

### フロントエンド
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS + shadcn/ui
- **State**: Zustand（軽量）
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

### システムプロンプト

```
あなたは英語教育の専門家です。英語学習者向けの高品質な英文法問題を生成します。
- 問題文は自然な英語で書く
- 選択肢は紛らわしいが明確に正解が1つになるよう設計する
- 解説は日本語で簡潔に（2〜3文）
- 必ずJSON形式で返す
```

### ユーザープロンプトテンプレート

```
以下の条件で英語{type}問題を{count}問生成してください。

- 難易度: {level}
- 出力形式: {format}
- 文法項目: {grammar_points}
- 説明言語: {explanation_lang}

出力は以下のJSON形式で返してください:
[JSONスキーマ]
```

---

## データベース設計

```sql
-- ユーザーテーブル
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'free',  -- free / starter / professional / business
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 使用量テーブル
CREATE TABLE questions_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  ip_address TEXT,  -- 未ログインユーザー用
  count INTEGER NOT NULL,
  period TEXT NOT NULL,  -- '2026-03' 形式（月次リセット）
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 生成履歴テーブル（オプション）
CREATE TABLE generation_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  params JSONB NOT NULL,
  result JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 実装計画（2週間スプリント）

### Week 1: コア機能

| Day | タスク |
|---|---|
| 1 | Next.jsプロジェクト作成、Vercelデプロイ設定 |
| 2 | 問題生成フォームUI実装 |
| 3 | Claude API連携（問題生成API Route） |
| 4 | JSON/CSVエクスポート実装 |
| 5 | 問題プレビューUI、使用量制限（IP） |

### Week 2: 課金・公開準備

| Day | タスク |
|---|---|
| 6 | Supabase設定、ユーザー認証（NextAuth.js） |
| 7 | Stripe Checkout統合 |
| 8 | Stripeウェブフック、プラン別制限実装 |
| 9 | LP作成（料金表・CTA） |
| 10 | テスト・バグ修正・本番リリース |

---

## 先行販売戦略（Gumroad）

MVP完成前にGumroadで「アーリーアクセス」販売:
- 価格: ¥2,980（通常価格の30%割引）
- 対象: 先着20名
- 特典: 永久Professionalプラン相当
- 告知: native-realのメールリスト、note記事

これにより開発費を先行回収しつつ、フィードバックを収集する。

---

## KPI・成功指標

| 指標 | 1ヶ月目 | 3ヶ月目 | 6ヶ月目 |
|---|---|---|---|
| 無料登録数 | 50 | 200 | 500 |
| 有料転換率 | - | 10% | 15% |
| MRR | ¥20,000 | ¥100,000 | ¥300,000 |
| Churn率 | - | < 10% | < 7% |
