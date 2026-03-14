# CLAUDE.md

## プロジェクト概要

AI会社組織構築プロジェクト。川岸宏司さんの「AI組織化メソッド」を適用し、
Claude Code上にスキルとドキュメントを集約して事業全体を自動化する。

## ディレクトリ構成

```
ai-company/
├── docs/
│   └── AI会社組織_引き継ぎ.md   # ビジョン・進捗・スキル仕様書
├── skills/
│   └── x-schedule-post/
│       └── SKILL.md              # X予約投稿スキル
└── CLAUDE.md
```

## スキル管理ルール

- `skills/` 以下がソース。`~/.claude/skills/スキル名` → シンボリックリンクでグローバル公開
- スキルを追加したら必ず `ln -s ~/projects/claude/ai-company/skills/スキル名 ~/.claude/skills/スキル名` を実行
- スキル変更後は即コミット＆プッシュ

## 開発ルール

- コード変更後は自動でコミット＆プッシュまで行う
- APIキーは `.env` に記載し、ソースコードに直接書かない
