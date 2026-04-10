# CLAUDE.md

## プロジェクト概要

AI会社組織構築プロジェクト。川岸宏司さんの「AI組織化メソッド」を適用し、
Claude Code上にスキルとドキュメントを集約して事業全体を自動化する。

**モノレポ構成**: 旧 `IchiShio/native-real` リポジトリを `site/` に統合済み。
サイト本体（native-real.com）とAI運用基盤が1リポジトリで完結する。

## ディレクトリ構成

```
ai-company/
├── site/                           # native-real.com 本体（GitHub Pages公開）
│   ├── index.html                  # トップページ
│   ├── articles/                   # SEO記事
│   ├── listening/                  # ListenUp クイズ（1,099問）
│   ├── services/                   # サービス比較ページ（Tier1）
│   ├── real-phrases/               # フレーズ集（Tier3）
│   ├── grammar/                    # GrammarUp
│   ├── CLAUDE.md                   # サイト固有の開発ルール・デザインシステム
│   ├── DESIGN.md                   # デザインシステム仕様
│   └── ...
├── skills/                         # AIスキル群（23個）
│   ├── ceo/ coo/ cso/              # 経営スキル
│   ├── native-real-*/              # SEOパイプライン（6スキル）
│   ├── x-*/                        # X運用（5スキル）
│   ├── kioku-shinai-*/             # 記憶しない英単語（3スキル）
│   └── ...
├── products/                       # デジタル商品（ガイド3種）
├── projects/                       # SaaS企画（4案）
├── scripts/                        # 運用スクリプト群
├── x-knowledge/                    # X投稿ナレッジベース
├── docs/                           # 戦略文書・引き継ぎ
├── .github/workflows/
│   ├── deploy-pages.yml            # site/ → GitHub Pages デプロイ
│   ├── ichi-eigo-post.yml          # X自動投稿
│   ├── fetch-metrics.yml           # メトリクス収集
│   └── oac-post.yml
└── CLAUDE.md
```

## サイト（site/）の編集ルール

- サイトのコード編集時は `site/CLAUDE.md` と `site/DESIGN.md` を必ず参照
- `site/` 配下の変更を main に push すると GitHub Pages に自動デプロイ
- SEO Executor スキルが `site/` を直接編集可能（クロスリポ不要）

## スキル管理ルール

- `skills/` 以下がソース。`~/.claude/skills/スキル名` → シンボリックリンクでグローバル公開
- スキルを追加したら必ず `ln -s ~/projects/claude/ai-company/skills/スキル名 ~/.claude/skills/スキル名` を実行
- スキル変更後は即コミット＆プッシュ

## 開発ルール

- コード変更後は自動でコミット＆プッシュまで行う
- APIキーは `.env` に記載し、ソースコードに直接書かない
