# X Knowledge Base — ルーター

タスクに応じて必要なファイルだけを読み込むこと（Progressive Disclosure）。

## タスク別ガイド

| やりたいこと | 読むファイル |
|---|---|
| 投稿を作成する | `craft/templates.md` → `craft/hooks.md` → `voice/{account}.md` → `themes/rotation.md` |
| 投稿を分析する | `posts/{account}-log.csv` → `learnings/patterns.md` → `hypotheses/active.md` |
| 仮説を検証する | `hypotheses/active.md` → `posts/{account}-log.csv` → `learnings/patterns.md` |
| 週次レビューする | 全ファイルを順に確認（posts → learnings → hypotheses → craft → themes） |
| 新しいパターンを発見した | `learnings/patterns.md` に追記 |
| 「効かなかった」を記録する | `learnings/false-beliefs.md` に追記 |
| テーマを決める | `themes/rotation.md` → `posts/{account}-log.csv`（テーマ別実績） |

## ファイル一覧

```
x-knowledge/
├── INDEX.md                 ← このファイル（ルーター）
├── craft/
│   ├── hooks.md             ← フック（1行目）のパターン集
│   ├── templates.md         ← 投稿テンプレート（データで進化する）
│   └── copywriting-rules.md ← 文体・文字数・構造のルール
├── voice/
│   ├── ichi-eigo.md         ← @ichi_eigo のトーン・ペルソナ定義
│   └── careermigaki.md      ← @careermigaki のトーン・ペルソナ定義
├── posts/
│   ├── ichi-eigo-log.csv    ← 投稿ログ＋パフォーマンスデータ
│   └── careermigaki-log.csv ← 投稿ログ＋パフォーマンスデータ
├── hypotheses/
│   └── active.md            ← テスト中の仮説（データで検証・淘汰）
├── learnings/
│   ├── patterns.md          ← データから発見した勝ちパターン
│   └── false-beliefs.md     ← 「効くと思ったが効かなかった」記録
└── themes/
    └── rotation.md          ← テーマローテーション＋実績追跡
```
