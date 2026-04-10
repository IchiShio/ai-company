# Google SEO 公式アップデート記録

## March 2026 Core Update（2026-03-27〜ロールアウト中）

**種別**: コアアップデート
**公式発表URL**: https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history
**ロールアウト**: 2026-03-27 開始、完了日未定（本記録時点で進行中）

### 主な変更点
- 詳細な変更内容は公開されていない（Googleの通例通り）
- ロールアウト中のため、順位変動が続く可能性あり

### native-real SEOスキルへの影響
- **影響なし（監視中）**: 新しいサイトのため現時点で顕著な順位変動は検知されていない
- **推奨アクション**: 4月上旬にSCデータで順位変動を確認する

---

## March 2026 Spam Update（2026-03-24、完了）

**種別**: スパムポリシーアップデート
**公式発表URL**: https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history
**ロールアウト**: 2026-03-24 開始〜約19.5時間で完了

### 主な変更点
- スパムポリシー違反コンテンツの検出精度向上
- 詳細は非公開

### native-real SEOスキルへの影響
- **影響なし**: native-real.comは全コンテンツ人間監修+ファクトチェック済み
- スパムフィルター回避目的のAI生成は一切なし（kioku-shinai-fact-checkerで品質管理済み）

---

## FAQPage リッチリザルト対象変更（確認日: 2026-03-31）

**種別**: ガイドライン変更（構造化データ）
**公式発表URL**: https://developers.google.com/search/docs/appearance/structured-data/faqpage?hl=ja
**変更内容**: FAQPageリッチリザルトの表示対象が「政府機関・医療機関のみ」に限定

### 主な変更点
- **以前**: 一般サイトもFAQPage schema でリッチリザルト獲得可能
- **現在**: 政府機関・保健衛生関連サイトのみがリッチリザルト対象

### native-real SEOスキルへの影響
- **影響あり（低優先）**: real-phrases/（105ページ）・articles/（49ページ）計154ページにFAQPage schemaを使用中
- **リッチリザルト**: 今後も表示されない（もともと新規サイトでは表示実績なし）
- **SEOペナルティ**: なし（schema自体は有効なマークアップ、ペナルティ対象外）
- **推奨アクション**: 新規ページへのFAQPage schema追加を停止。既存154ページの削除は低優先（rankingに悪影響なし）。将来的にArticle schemaへの移行を検討。

### スキル修正内容
- `native-real-seo-executor`: 新規ページ作成時のFAQPage schema追加を停止する旨を注記（次回executor実行前に確認）

---

## E-E-A-T・AI生成コンテンツ方針（確認日: 2026-03-31）

**種別**: コンテンツ品質ガイドライン（変更なし・確認済み）

### 現行ガイドラインの主要ポイント
- **信頼性が最重要**: E-E-A-Tの中でTrustworthinessが最優先
- **AI生成コンテンツの開示**: 自動化使用時はユーザーへの開示が推奨
- **著者情報**: バイライン・専門分野の記載を推奨
- **スパム違反**: ランキング操作目的のAI生成は明確にスパム認定

### native-real SEOスキルへの影響
- **影響なし**: 現在の運用はガイドラインと整合
- **参考情報**: 著者情報の追記をTier 1ページに将来的に検討（E-E-A-T向上）

---
