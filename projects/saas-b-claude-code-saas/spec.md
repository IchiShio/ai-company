# SaaS-B: MVP機能仕様・技術スタック・実装計画

## MVP定義

**スコープ**: Gumroadでデジタル商品として販売できる「ひとりAI会社テンプレートパック」の完成とランディングページの公開。

---

## MVP機能仕様

### 商品パッケージ構成

```
saas-b-starter-pack-v1.zip
├── README.md                    # セットアップガイド（日本語）
├── QUICKSTART.md                # 5分で動かすガイド
├── skills/
│   ├── oac-bucho/SKILL.md
│   ├── oac-writer/SKILL.md
│   ├── backlog-executor/SKILL.md
│   ├── x-schedule-post/SKILL.md
│   └── native-real-seo-pipeline/SKILL.md
├── templates/
│   ├── backlog-template.md      # バックログテンプレート
│   ├── CLAUDE.md.example        # AI会社CLAUDE.mdサンプル
│   └── project-structure.md    # プロジェクト構成ガイド
└── examples/
    ├── ai-company-example/      # ai-companyの匿名化サンプル
    └── native-real-example/     # アフィリサイトの匿名化サンプル
```

### ランディングページ（GitHub Pages）

**URL**: `https://ichishio.github.io/ai-company/saas-b/`

**ページ構成**:
- ヒーローセクション: 「Claude Codeで月収を作る仕組みをコピペで実装」
- 実績セクション: IchiShio自身の数字（MAU・収益・自動化率）
- 同梱コンテンツ一覧
- 料金表（スターター・プロ）
- FAQ
- Gumroad購入ボタン（CTA）

---

## 技術スタック

### 商品（テンプレートパック）
- **形式**: ZIPファイル（Markdownベース）
- **配布**: Gumroad（デジタルダウンロード）
- **バージョン管理**: ai-company GitHub リポジトリ内で管理

### ランディングページ
- **フレームワーク**: 静的HTML/CSS（native-realと同構成）
- **ホスティング**: GitHub Pages
- **アナリティクス**: Google Analytics 4（GA4）
- **決済**: Gumroadのオーバーレイウィジェット埋め込み

### 月額サポート管理
- **Phase 3以降**: Stripe Billing（月額サブスク）
- **MVP**: Gumroadのサブスクプラン機能を活用

---

## 実装計画

### Sprint 1（Day 1-3）: 商品パッケージ作成

| タスク | 担当エージェント | 工数 |
|---|---|---|
| スターターパック用スキルMD整備 | backlog-executor | 2h |
| QUICKSTART.md執筆 | oac-writer | 1h |
| テンプレートファイル作成 | backlog-executor | 1h |
| ZIPパッケージング | backlog-executor | 0.5h |

**完了条件**: Gumroadにアップロードして購入フローが動作すること

### Sprint 2（Day 4-7）: ランディングページ公開

| タスク | 担当エージェント | 工数 |
|---|---|---|
| LP HTML/CSS作成 | backlog-executor | 3h |
| 実績データ整理・掲載 | oac-bucho | 1h |
| Gumroad購入ボタン設置 | backlog-executor | 0.5h |
| GitHub Pages公開 | backlog-executor | 0.5h |

**完了条件**: LPからGumroadで購入できること

### Sprint 3（Day 8-14）: 集客開始

| タスク | 担当エージェント | 工数 |
|---|---|---|
| note記事「ひとりAI会社の作り方」執筆 | oac-writer | 3h |
| X（Twitter）告知ツイート作成・投稿 | x-schedule-post | 1h |
| 購入者フィードバック収集（Googleフォーム） | backlog-executor | 0.5h |

**完了条件**: 初売上（1件以上）達成

---

## KPI

| 指標 | MVP目標（30日） | 3ヶ月目標 |
|---|---|---|
| LP訪問者数 | 500 UV | 2,000 UV |
| LP→Gumroad CTR | 10% | 15% |
| Gumroad CVR | 3% | 5% |
| 売上 | ¥50,000 | ¥200,000 |
| 月額サポート加入者 | 0 | 10名 |

---

## リスクと対策

| リスク | 対策 |
|---|---|
| 購入者がスキルをセットアップできない | QUICKSTART.mdを徹底的に簡潔化。Loom動画補完 |
| 競合（AI副業系情報商材）との差別化困難 | 実績数字の透明開示。オープンソース姿勢でブランド構築 |
| Gumroad手数料（10%） | 月額プランへの移行促進。Stripeへ段階的移行 |
| スキルのメンテナンスコスト | スキルをOSS化し、コミュニティに一部委譲 |

---

## 次フェーズへの移行条件

- **Phase 2移行**: 月間売上 ¥50,000 超
- **Phase 3移行**: 月額サポート加入者 10名 超
- **Phase 4移行**: セットアップ支援で ¥100,000/月 安定
