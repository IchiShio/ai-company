# SaaS-D MVP仕様書

## MVPスコープ（v0.1）

最小限の機能で3ヶ月以内にリリースできるスコープを定義する。

## MVP機能一覧

### コア機能（必須）

1. **問題生成**
   - 4択文法問題（TOEIC・英検・一般）
   - 穴埋め問題（単語・熟語）
   - レベル指定（初級/中級/上級）
   - カテゴリ指定（時制/冠詞/前置詞/関係詞/助動詞など）

2. **エクスポート**
   - JSON形式（native-realのquestions.js互換）
   - CSV形式（Excel・Googleスプレッドシート対応）

3. **認証・課金**
   - メール＋パスワード認証（Supabase Auth）
   - Stripeによる月額課金
   - 生成数カウンター（プランごとの上限管理）

4. **ダッシュボード**
   - 生成履歴一覧
   - 問題の編集・削除
   - 月間使用量の確認

### MVP外（v0.2以降）

- QTI形式エクスポート（Moodle連携）
- 長文読解問題生成
- チーム機能・複数アカウント管理
- カスタムプロンプトテンプレート
- API提供

## 技術スタック

### フロントエンド
- **フレームワーク**: Next.js 14（App Router）
- **スタイリング**: Tailwind CSS
- **UIコンポーネント**: shadcn/ui
- **状態管理**: Zustand

### バックエンド
- **サーバー**: Next.js API Routes（サーバーレス）
- **AIエンジン**: Claude API（claude-haiku-4-5 でコスト最適化）
- **DB**: Supabase（PostgreSQL）
- **認証**: Supabase Auth
- **決済**: Stripe

### インフラ
- **ホスティング**: Vercel
- **モニタリング**: Vercel Analytics

## データモデル（主要テーブル）

```sql
-- ユーザー
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'free',
  monthly_usage INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 生成セッション
CREATE TABLE generation_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  category TEXT,
  level TEXT,
  count INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 生成問題
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES generation_sessions(id),
  question_text TEXT NOT NULL,
  options JSONB NOT NULL,
  correct_answer TEXT NOT NULL,
  explanation TEXT,
  tags TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Claude API プロンプト設計

```
あなたは英語教育のプロフェッショナルです。
以下の条件で英語4択問題を{count}問生成してください。

条件:
- レベル: {level}（初級/中級/上級）
- カテゴリ: {category}
- 対象: {target}（TOEIC/英検/一般英会話）

出力形式（JSON配列）:
[
  {
    "question": "問題文",
    "options": {"a": "選択肢A", "b": "選択肢B", "c": "選択肢C", "d": "選択肢D"},
    "correct": "a",
    "explanation": "解説文（50字以内の日本語）"
  }
]

注意:
- 問題は自然な英語を使うこと
- 誤答選択肢は紛らわしいが明確に誤りであること
```

## 実装計画（12週）

### Phase 1: 基盤構築（Week 1-3）
- [ ] プロジェクトセットアップ（Next.js + Supabase + Stripe）
- [ ] 認証フロー実装（登録・ログイン・パスワードリセット）
- [ ] Stripeサブスク設定（Free/Starter/Pro/School）
- [ ] DBスキーマ作成・マイグレーション

### Phase 2: コア機能（Week 4-7）
- [ ] Claude API連携・問題生成API実装
- [ ] 生成UI（パラメータ設定フォーム）
- [ ] 生成結果の表示・編集UI
- [ ] 使用量カウンター・プラン上限制御

### Phase 3: エクスポート・仕上げ（Week 8-10）
- [ ] JSON/CSVエクスポート機能
- [ ] ダッシュボード・履歴管理
- [ ] レスポンシブ対応
- [ ] エラーハンドリング・ローディングUI

### Phase 4: リリース準備（Week 11-12）
- [ ] ランディングページ作成
- [ ] セキュリティレビュー（Rate limiting, Input validation）
- [ ] Vercelデプロイ・カスタムドメイン設定
- [ ] βテストユーザー獲得（英語教室5〜10社）

## コスト試算

| 項目 | 月額コスト |
|------|-----------|
| Claude API（Haiku）| ¥5,000〜15,000（利用量による） |
| Supabase Pro | $25（約¥3,750） |
| Vercel Pro | $20（約¥3,000） |
| Stripe手数料 | 売上の3.6% |
| **合計（固定）** | **約¥22,000/月** |

## 競合分析

| サービス | 強み | 弱み |
|---------|------|------|
| Quizlet | 知名度・コミュニティ | 問題自動生成が弱い |
| Kahoot | エンゲージメント | 英文法に特化していない |
| Wordwall | 使いやすさ | AI生成機能なし |
| **本SaaS** | AI生成+日本の英語教育特化 | 新規参入 |
