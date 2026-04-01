# 収入自動化・複数化バックログ

> **方针**: 全タスクは収入の自動化・複数化を目的とする。
> アイドル時間に自律実行する。完了したら次のタスクへ。

---

## Tier 1：即収益（最優先）

### [ ] note有料記事 - oac新作
- **収益**: note販売（¥980〜¥3,980）
- **パイプライン**: `/oac-bucho` → `/oac-writer` → `/note-publisher`
- **候補テーマ**: Claude Codeで月収を作る具体的な方法、AIエージェント組織の作り方
- **実行方法**: `/oac-bucho review` でネタ選定→執筆→公開

### [ ] note有料記事 - careermigaki新作
- **収益**: note販売（¥500〜¥1,980）
- **パイプライン**: `/cm-bucho` → `/cm-seo-writer` → `/note-publisher`
- **候補テーマ**: 転職成功事例、面接対策、年収交渉術
- **実行方法**: `/cm-bucho post` でネタ選定→執筆→公開

### [x] native-real アフィリ強化
- **収益**: アフィリエイトCVR改善
- **実行方法**: `/native-real-seo-pipeline` → アフィリCTA強化
- **対象**: /ranking/ ページのCTA最適化、個別サービスレビュー追加

---

## Tier 2：新収益柱

### [x] ニッチ比較サイト（native-realモデル複製）
- **収益**: アフィリエイト
- **ジャンル候補**: プログラミングスクール比較 / 副業ツール比較 / AI活用ツール比較
- **技術**: 静的HTML、GitHub Pages（native-realと同構成）
- **実行方法**: ジャンル選定→サイト構造設計→コンテンツ生成→デプロイ
- **完了**: 2026-04-01 プログラミングスクール比較サイト設計・コンテンツ生成（`projects/programming-school-comparison/`）。index.html・ranking/index.html・README.md・spec.md作成。デプロイはprog-school.net新規リポジトリ作成後に実施。

### [ ] メールリスト×ステップメール
- **収益**: 自社商品・アフィリへの誘導
- **対象**: native-real読者（英語学習者）
- **実行方法**: Beehiiv設定→ステップメール設計→CTAページ作成

---

## Tier 3：自社商品SaaS（優先度順）

### [x] D: 英語学習コンテンツ生成SaaS ⭐️最優先
- **収益**: B2B月額サブスク（英語教室・スクール向け）
- **コア機能**:
  - ListenUp/GrammarUp形式の問題を自動生成
  - Claude APIで問題生成 → 音声合成 → エクスポート
  - ターゲット: 英語教室運営者、教材制作者
- **技術候補**: Next.js + Stripe + Claude API
- **MVP**: 問題生成フォーム → JSON/CSV出力（無料トライアル付き）
- **実行方法**: MVP設計→実装→Vercelデプロイ→Gumroadで先行販売
- **完了**: 2026-03-30 MVP設計書作成（`projects/saas-d-content-generator/`）

### [x] B: Claude Code活用SaaS（ひとりAI会社モデル販売）
- **収益**: 月額サブスク or 初期費用
- **コア機能**:
  - AIエージェント組織のテンプレートセット販売
  - セットアップ支援ツール
- **実行方法**: oac-buchoと連携してコンテンツ設計
- **完了**: 2026-04-01 MVP設計書作成（`projects/saas-b-claude-code-saas/`）。README.md・spec.md作成。Gumroad販売・GitHub Pages LP・月額サポートプランを設計。

### [ ] A: X自動化SaaS
- **収益**: 月額サブスク
- **コア機能**: 複数アカウント管理・スケジュール投稿・パフォーマンス分析
- **注意**: 競合多い。差別化（AI生成+自動PDCA）が必須

### [ ] C: SEO自動化SaaS
- **収益**: 月額サブスク
- **実行方法**: native-realパイプラインのサービス化

---

## native-real MAU強化（M&A戦略）

### [x] GrammarUp 問題追加（目橐1000問）
- 1005問 → 2026-03-30: 20問追加（g1048-g1067）、誈1025問

### [x] NewsUp MVP実装
- VOA記事ベースのニュース英語読解クイズ
- **完了**: 2026-03-31: 10記事・3問/記事実装（`/newsup/`）

### [x] kioku-shinai 語根追加
- 無料600語完成を目指す
- **完了**: 2026-04-01: 30語根×20語=600語達成。index.htmlのcount表示を全語根20語に修正

---

## 完了済み
<!-- 完了したタスクをここに移動 -->

---

## メモ
- StarterForge: Stripe設定完了まで保留
- 英語学習系有料ツール → native-realで無料公開（MAU戦略）
