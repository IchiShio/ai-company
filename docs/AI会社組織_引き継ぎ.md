# AI会社組織 構築プロジェクト — 引き継ぎ

## ビジョン

川岸宏司さん（@OnebookofMAG）の「AI組織化メソッド」を自分の事業全体に適用し、Claude Code上にAI会社組織を構築する。コンテンツ事業に限らず、経理・確定申告・週次レポート・顧客管理など事業のあらゆる業務をスキルで自動化し、最終的に社長AIに一言指示するだけで組織が回る状態を目指す。

## 参考資料

- 川岸さんの記事①（組織化の全体像）: https://x.com/OnebookofMAG/status/2029497725260324976
- 川岸さんの記事②（スキル化の手順）: https://x.com/OnebookofMAG/status/2032303304328491136

### 川岸メソッドの要点

1. **業務プロセスを限界まで細分化する**
2. **末端の業務をAIワークフローでテストする**
3. **テスト結果が問題なければSkillsにする**
4. **①〜③が完了したらDBを作り、出力場所を1本化する**（Notion等）
5. **ここまでを組み合わせてエンドレスルーティンにする**

### 川岸さんの組織構造

- **社長AI（AIマグ / Opus）** — 判断・振り分け・品質チェック。トークン節約のため最上位のみOpus
- **部長AI × 5（Sonnet）** — 各部門の業務分解と監督
- **社員AI** — 末端の実行タスク

ポイント: 人間がやるのは「判断」と「分解」と「品質チェック」。これをAIに委譲するのが社長AI。

## Yusukeさんの事業構造（想定される部門）

```
社長AI（CLAUDE.md / Opus）
├── コンテンツ部門
│   ├── @ichi_eigo（英語学習）— X投稿、note記事、ListenUp連携
│   ├── @careermigaki（キャリア転職）— X投稿、スレッド
│   └── native-real.com — ブログ、SEO、アフィリエイト
├── コーチング部門
│   ├── 顧客管理
│   ├── 教材作成
│   └── レポート・分析
├── 管理・経理部門
│   ├── freee連携（MCP設定済み）
│   ├── 確定申告
│   └── 週次レポート（Gmail + Calendar + Slack集約）
└── 開発部門
    ├── Webアプリ（Word Orbit、日本語ゼロ瞬間英作文PWA等）
    ├── GAS自動化（Drive自動リネーム等）
    └── ツール開発
```

## 技術環境

- **Claude Code** — メイン開発環境。スキルのネイティブサポート
- **Claude.ai（Max plan）** — Claude in Chrome でブラウザ操作
- **Claude iOS app** — iPhone-firstのモバイル作業
- **GitHub** — リポジトリでスキル管理（LaunchAgentは2026-03-10削除済み、手動管理）
- **MCP接続済み** — Gmail, Google Calendar, Slack, freee

## 完成済みスキル

### 1. X予約投稿スキル（x-schedule-post）

**概要**: XのWeb UIをMCP経由のブラウザ操作（Claude in Chrome）で直接操作し、指定アカウントの次の空き枠（7:30 or 18:30 JST）に予約投稿する。

**対応アカウント**: @ichi_eigo, @careermigaki

**ファイル**:
- `~/.claude/skills/x-schedule-post/SKILL.md` — **正式配置場所（2026-03-14移動済み）**

**テスト結果（2026年3月14日実施）**:
- @ichi_eigo で 3月15日（日）午前7:30 に予約投稿成功
- @ichi_eigo で 3月15日（日）18:30 に予約投稿成功
- 予約一覧で確認済み

**テストで判明したXのUI仕様**:
- `/compose/scheduled` は404になる。正しいルート: 「ポストする」→「下書き」→「予約済み」タブ
- 予約済み一覧のURL: `x.com/compose/post/unsent/scheduled`（直接アクセス不可）
- 予約時刻は7:30/18:30ぴったりではなく数分ずれる → 前後30分以内なら同じ枠と判定
- 予約設定画面: 月/日/年 + 時/分のドロップダウン（24時間表記）、タイムゾーン「日本標準時」
- 予約確定は2段階: 「確認する」→ 投稿画面に戻る →「予約設定」ボタン
- ツールバー（左→右）: 画像, GIF, リンク, リスト, 絵文字, **スケジュール（6番目）**, 位置情報, 旗, 太字, 斜体
- `form_input` でドロップダウン設定が確実に動作する

### 2. native-real.com SEOデータ収集スキル（native-real-data-collector）

**概要**: native-real.com（英語学習サービス比較サイト）のSEOデータを3つのソースから自動収集し、Google Drive同期フォルダに日付別CSVとして保存する。データ収集のみ。分析は別スキルが担当。

**データソース**:
- Google Search Console（ブラウザ自動操作 / ichieigo7@gmail.com）
- Google Analytics GA4（ブラウザ自動操作 / プロパティID: a382654252p525926980）
- Ahrefs MCP（4ツール: site-explorer-metrics, organic-keywords, pages-by-traffic, all-backlinks）

**保存先**: `~/マイドライブ/02_AI・ブログ・仕事/GoogleG4,SearchConsole/YYYY-MM-DD/`（Google Drive同期フォルダ）

**スケジュールタスク**: `native-real-seo-data-collection`（毎朝6:05 AM、cron: `0 6 * * *`）

**ファイル**:
- `~/projects/claude/ai-company/skills/native-real-data-collector/SKILL.md`

**テスト結果（2026年3月14日実施）**:
- Search Console: ZIPエクスポート → 展開 → CSV 5ファイル取得成功（クエリ300件、ページ109件等）
- GA4: トラフィック獲得・ページとスクリーンの2レポートCSV取得成功
- Ahrefs: 4ツール全て取得成功（APIユニット消費: 約386/回、月約12,000/25,000上限）
- Google Drive同期: ローカル保存 → Drive自動反映を確認

**テストで判明した注意点**:
- Search ConsoleのZIP内CSVは日本語ファイル名が文字化けする → ヘッダー行で識別
- GA4のCSVはBraveブラウザで `.com.brave.Browser.*` 一時ファイル名になることがある
- Ahrefsのカラム名: `best_position`（positionではない）、`sum_traffic`（trafficではない）
- 全ツールで `mode=subdomains` を指定（domainだとwwwが除外される）

**保存ファイル名（2026-03-15 統一済み）**:
- SC: `queries.csv`, `pages.csv`, `dates.csv`, `devices.csv`, `countries.csv`（`search_console_` プレフィックスなし）
- GA4: `ga4_traffic.csv`（旧: `ga4_traffic_acquisition.csv`）、`ga4_pages.csv`
- Ahrefs: `ahrefs_metrics.csv`（旧: `ahrefs_overview.csv`）、`ahrefs_keywords.csv`、`ahrefs_pages.csv`、`ahrefs_backlinks.csv`

### 4. native-real.com 週次SEOパイプライン（native-real-seo-pipeline）

**概要**: `native-real-data-collector` → `native-real-seo-analyzer` → `native-real-seo-executor` の3スキルをワンコマンドで連続実行するオーケストレータースキル。

**呼び出し**: `/native-real-seo-pipeline`

**設計方針**:
- シンオーケストレーター（各スキルの処理は個別スキルに委譲、重複なし）
- `model: claude-opus-4-6` 指定（executor と同じ Opus で動作）
- Step 3（executor）のアクション選択だけユーザー確認を挟む（git push を伴うため）
- Ahrefs MCP 4ツールは並列実行

**ファイル**:
- `~/projects/claude/ai-company/skills/native-real-seo-pipeline/SKILL.md`

**追加日**: 2026-03-15

---

### 3. native-real.com SEO分析スキル（native-real-seo-analyzer）

**概要**: native-real-data-collectorが収集したCSV12ファイルを読み込み、7つの分析フレームワークで評価し「次の1週間で何をすべきか」をTop 5優先アクションとして提案する。「分析者」ではなく「参謀」として振る舞う設計。

**分析フレームワーク**:
- A. クイックウィン（順位4〜20 AND インプレ≥5のクエリ）
- B. 高インプレ低CTR（期待CTRとの乖離をスコア化）
- C. チャネル品質（GA4: エンゲージ率・時間・セッション数で総合スコア）
- D. コンテンツ品質（GA4: スター/要改善/潜在に3分類）
- E. キーワードギャップ（Ahrefs: volume × 順位割引）
- F. バックリンク品質（スパムリンク検出 → Disavow推奨）
- G. 28日間トレンド（前半14日/後半14日で変化率、急落時は原因調査を1位強制）

**出力**: Top 5優先アクション（「○○のtitleタグを△△に変更する」レベルの具体性）

**ファイル**:
- `~/projects/claude/ai-company/skills/native-real-seo-analyzer/SKILL.md`

**追加日**: 2026-03-14

---

## 未着手・構想中のスキル

以下は想定される候補。どの部門のどの末端業務から着手してもよい。

### コンテンツ部門
- **X投稿テンプレートスキル** — 「常識否定→解決策提示」等のフォーマットで投稿本文を生成
- **テーマローテーションスキル** — 17テーマのローテーション管理
- **@careermigaki スレッド作成スキル** — IODフレームワーク、STAR面接対策等
- **note.com記事スキル** — 5カテゴリテンプレート（Story, Problem-solving等）
- **Twitter分析スキル** — アナリティクスCSVを読み込んで改善ポイント抽出

### 管理・経理部門
- **freee連携スキル** — MCP経由での会計データ操作（設定途中）
- **確定申告スキル** — freeeデータからの申告書作成支援
- **週次レポートスキル** — Gmail + Calendar + Slack → Markdownレポート（設計済み、Slack接続待ち）

### 開発部門
- **native-real.comデプロイスキル** — Next.js SSG + Wiktextract
- **GAS自動化スキル** — Gemini APIでのDriveファイル自動リネーム等

## 構築の進め方

川岸メソッドに従い、以下のサイクルを繰り返す:

1. **業務を選ぶ** — 日常で繰り返している作業、毎回同じ指示をしている作業
2. **限界まで細分化する** — 手順を最小ステップに分解
3. **末端からテストする** — Claude Codeで実際に動かして確認
4. **スキル化する** — SKILL.md を作成、`~/.claude/skills/` に配置
5. **組み合わせる** — スキルが3〜4個揃ったら部長AIスキルで統括
6. **社長AIに統合する** — 全部門の部長AIをCLAUDE.mdで束ねる

## Claude Codeでのスキル管理

```bash
# スキルの配置場所
~/.claude/skills/スキル名/SKILL.md  # ユーザースキル（グローバル）
.claude/skills/スキル名/SKILL.md     # プロジェクトスキル（リポジトリ内）

# スキルの構造
スキル名/
├── SKILL.md        # 必須: 指示書（YAML frontmatter + Markdown）
├── scripts/        # 任意: 実行スクリプト
├── references/     # 任意: 参考資料
└── assets/         # 任意: テンプレート等

# 呼び出し方
/スキル名              # スラッシュコマンドで明示的に
（自動トリガー）        # descriptionに書いたフレーズに該当すれば自動で起動
```

## @ichi_eigo の投稿ルール（既に確立済み）

- 17テーマのローテーション
- 「常識否定 → 解決策提示」構造
- 130〜140文字（ハッシュタグなし、絵文字なし）
- Draft → ファクトチェック → Final の3ステップ
- 投稿枠: 毎日 7:30 と 18:30

## @careermigaki の投稿ルール（既に確立済み）

- IODフレームワーク（Phase 1: 情報提供重視）
- マルチパートスレッド形式
- STAR面接、レジュメ、報酬体系、求人市場データ
- 数値データは必ずファクトチェック

## 注意事項

- XのUIは頻繁に変更されるため、スキルの「UIのヒント」セクションは定期的に確認・更新する
- freee MCPの設定はClaude Code経由で進行中（認証フロー等）
- iPhone-first運用のため、Claude iOS appでの操作性も考慮する
