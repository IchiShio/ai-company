# 付録B：ディレクトリ構成テンプレート

AI会社の推奨ディレクトリ構成と各ディレクトリの役割を解説します。

---

## 全体構成

```
ai-company/                          # AI会社のルートリポジトリ
├── CLAUDE.md                        # プロジェクト全体のルール・方針
│
├── skills/                          # 全スキルのソースコード
│   ├── {部門名}-bucho/              # 部長スキル
│   │   └── SKILL.md
│   ├── {部門名}-writer/             # ライタースキル
│   │   └── SKILL.md
│   ├── {部門名}-checker/            # チェッカースキル
│   │   └── SKILL.md
│   ├── {部門名}-data-collector/     # データ収集スキル
│   │   └── SKILL.md
│   ├── {部門名}-analyzer/           # 分析スキル
│   │   └── SKILL.md
│   ├── {部門名}-pipeline/           # パイプラインスキル
│   │   └── SKILL.md
│   └── coo/                         # COOスキル（全社横断）
│       └── SKILL.md
│
├── {部門名}-knowledge/              # 部門ごとの知識ベース
│   ├── INDEX.md                     # ナビゲーション（どのファイルを読むべきか）
│   ├── craft/                       # テンプレート・ルール・フック
│   │   ├── templates.md             # コンテンツテンプレート一覧
│   │   ├── rules.md                 # 文体・構造のルール
│   │   └── hooks.md                 # フックパターン（実績付き）
│   ├── voice/                       # トーン・口調の定義
│   │   └── tone.md
│   ├── facts/                       # 根拠データ・統計のストック
│   │   ├── INDEX.md                 # Fact一覧
│   │   └── {テーマ名}.md            # テーマ別のFactファイル
│   ├── themes/                      # テーマ管理
│   │   └── rotation.md              # ローテーションと使用実績
│   ├── hypotheses/                  # テスト中の仮説
│   │   └── active.md                # アクティブな仮説リスト
│   ├── learnings/                   # 確認済みのパターン
│   │   ├── patterns.md              # 勝ちパターン（検証済み）
│   │   └── false-beliefs.md         # 否定された信念（二度と繰り返さない）
│   ├── posts/                       # 出力ログ
│   │   ├── {account}-log.csv        # パフォーマンス記録
│   │   └── schedule.json            # 予約投稿キュー
│   └── kpi.md                       # 部門KPI定義・実績
│
├── scripts/                         # 自動化スクリプト
│   ├── fetch_metrics.py             # データ取得スクリプト
│   └── run_pipeline.sh              # パイプライン一括実行
│
├── .github/workflows/               # GitHub Actions
│   └── {部門名}-{用途}.yml          # 定時実行ワークフロー
│
├── docs/                            # ドキュメント
│   └── organization.md              # 組織図・スキル一覧
│
├── .env                             # APIキー（git管理外）
├── .env.example                     # .envのテンプレート
└── .gitignore                       # .env等を除外
```

---

## 各ディレクトリの詳細

### `skills/` — スキルのソースコード

AI社員の「職務記述書」を格納する場所。1スキル = 1フォルダ = 1つの `SKILL.md`。

**命名規則**: `{部門名}-{役割}`
- 例: `seo-writer`, `sns-bucho`, `blog-checker`

**シンボリックリンクで公開**:
```bash
ln -s ~/projects/claude/ai-company/skills/{スキル名} ~/.claude/skills/{スキル名}
```
これにより、Claude Codeがどのディレクトリからでもスキルを呼び出せるようになる。

### `{部門名}-knowledge/` — 知識ベース

スキルが参照・更新する「組織の記憶」。時間とともに育っていく。

| サブフォルダ | 役割 | 更新頻度 |
|-------------|------|---------|
| `craft/` | テンプレート・ルール・フック | 月次（レビュー時） |
| `voice/` | トーン・口調の定義 | 低頻度（方針変更時） |
| `facts/` | 根拠データ・統計 | 随時（新データ発見時） |
| `themes/` | テーマローテーション | 週次（投稿時） |
| `hypotheses/` | テスト中の仮説 | 週次（レビュー時） |
| `learnings/` | 確認済みパターン | 週次（検証完了時） |
| `posts/` | 出力ログ・スケジュール | 日次（投稿・収集時） |

**INDEX.md の重要性**: 知識ベースが大きくなると、AIが全ファイルを読む必要はなくなる。INDEX.md に「どのタスクのときにどのファイルを読むか」を書いておくことで、効率的に必要な知識だけを参照できる。

### `scripts/` — 自動化スクリプト

API呼び出しやデータ加工など、SKILL.md内で記述しきれない処理を外出しする場所。

### `.github/workflows/` — 定時実行

GitHub Actionsのワークフローファイル。cronで定時実行する自動投稿やデータ収集に使う。

---

## 新しい部門を追加するときの手順

```bash
# 1. スキルフォルダを作成
mkdir -p ~/projects/claude/ai-company/skills/{部門名}-writer
mkdir -p ~/projects/claude/ai-company/skills/{部門名}-checker
mkdir -p ~/projects/claude/ai-company/skills/{部門名}-bucho

# 2. 知識ベースを作成
mkdir -p ~/projects/claude/ai-company/{部門名}-knowledge/{craft,voice,facts,themes,hypotheses,learnings,posts}
touch ~/projects/claude/ai-company/{部門名}-knowledge/INDEX.md

# 3. SKILL.mdを作成（付録Aのテンプレートをコピー）
# → 各skills/{部門名}-*/SKILL.md にテンプレートを書き込む

# 4. シンボリックリンクを作成
ln -s ~/projects/claude/ai-company/skills/{部門名}-writer ~/.claude/skills/{部門名}-writer
ln -s ~/projects/claude/ai-company/skills/{部門名}-checker ~/.claude/skills/{部門名}-checker
ln -s ~/projects/claude/ai-company/skills/{部門名}-bucho ~/.claude/skills/{部門名}-bucho

# 5. コミット & プッシュ
cd ~/projects/claude/ai-company && git add -A && git commit -m "{部門名}部門を追加" && git push origin main
```

---

## メモリシステムとの住み分け

| | 知識ベース（knowledge/） | メモリ（~/.claude/memory/） |
|---|---|---|
| 所有者 | AI組織（スキルが読み書き） | 人間（社長の好み・方針） |
| 内容 | 業務で学んだパターン・データ | ユーザーの役割・フィードバック・プロジェクト情報 |
| 更新者 | 部長・分析スキル | Claude Code（会話から自動記録） |
| 対象範囲 | 1つの部門 | 全プロジェクト横断 |

知識ベースは「組織が学んだこと」、メモリは「社長の考え」。この2つは別物として管理する。
