---
name: native-real-seo-executor
model: claude-opus-4-6
description: |
  native-real.com のSEOレポートで提案されたアクションを実際に実行するスキル。
  seo_report.md を読み込み、優先順位を確認してコンテンツの新規作成・修正・
  titleタグ改善・Disavowファイル作成などを自動実行し、git commit/push まで行う。

  次のような依頼で必ず使用すること：
  - 「SEOアクションを実行して」「レポートのアクションをやって」
  - 「コンテンツを修正して」「タイトルタグを直して」
  - 「by-the-wayをリライトして」など特定ページへの言及
  - 「Disavowファイルを作って」
---

# native-real.com SEOアクション実行スキル

## 概要

このスキルは「実行者」として振る舞う。SEOレポートの提案を実際のファイル変更に落とし込み、
git push まで完結させる。変更は必ず日本語で内容を説明してからユーザーの確認を得て実施する。

- **対象リポジトリ**: `~/projects/claude/native-real`
- **ページ構造**: `{type}/{slug}/index.html`（例: `real-phrases/by-the-way/index.html`）
- **デプロイ**: git push → GitHub Pages 自動反映

---

## Step 0: レポートと実行対象の確認

### レポートの自動検出

```
ベースパス: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/
```

最新日付フォルダの `seo_report.md` を読み込む:
```bash
ls ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/ | sort | tail -1
```

### 実行対象の決定

ユーザーが実行対象を指定している場合 → その内容を優先
指定がない場合 → レポートの「Top 5 優先アクション」テーブルを読み込み、以下を表示する:

```
## 実行可能なアクション一覧

| # | アクション（要約） | 推定クリック増 | 工数 | タイプ |
|---|---|---|---|---|
| 1 | ... | +XXX回 | 中 | コンテンツリライト |
| 2 | ... | +XXX回 | 中 | コンテンツリライト |
| 3 | ... | +XX回  | 小 | タイトル/メタ改善 |
...

どのアクションを実行しますか？（例: "1を実行して" / "1と3" / "全部"）
```

ユーザーの回答を待ち、実行するアクションを確定させてから Step 1 へ進む。

---

## Step 1: アクションの実行

選択されたアクションを1件ずつ実行する。各アクションの前に「何をどう変更するか」を明示してから編集する。

### タイプA: タイトル/メタディスクリプション改善

**対象ファイル特定**:
URLパス `/articles/foo/` → `~/projects/claude/native-real/articles/foo/index.html`

**編集対象の箇所**:
```html
<title>現在のタイトル</title>
<meta name="description" content="現在のdescription">
<meta property="og:title" content="現在のOGタイトル">
<meta property="og:description" content="現在のOG description">
```

**改善指針**:
- `<title>`: 目安28〜35文字（Googleに公式規定なし。モバイル表示幅からの実用目安）。数字・メリット・年度・【】などで訴求力を上げる
- `<meta name="description">`: Googleに文字数制限なし。検索意図に直接応える質の高い内容を優先。目安80〜130文字（表示幅を考慮）
- `og:title` / `og:description` も必ず同時に更新する
- ブランド名「| 英語学習サービス比較ナビ」はtitleの末尾に維持する

**実行前の確認フォーマット**:
```
### タイトル/メタ改善: /articles/foo/

変更前:
  title: 「現在のタイトル」
  description: 「現在のdescription（先頭50文字）...」

変更後:
  title: 「提案タイトル」
  description: 「提案description」

この内容で編集しますか？
```

---

### タイプB: コンテンツリライト

**対象ファイル**: URLパスから `~/projects/claude/native-real/{type}/{slug}/index.html` を特定

**リライト方針**:
1. まず対象ファイルを全文読み込む
2. `<head>` セクション（title, meta, canonical, JSON-LD等）は構造を維持しつつ内容を改善
3. `<body>` のコンテンツ部分を大幅に強化する

**コンテンツ強化の基準**:
- 本文 3,000字以上（現状 ~300行のHTMLで不足している場合は増量）
- H2セクション構成の例（real-phrasesページ）:
  - 意味・ニュアンス（基本）
  - 語源・由来（検索ニーズあり）
  - 実際の使用例（例文 10〜15個）
  - 似た表現との違い（類語比較）
  - NG例・注意点
  - よくある質問（FAQ セクション）
- ※ FAQPage JSON-LD schema はGoogle公式方針上「政府・医療機関サイト限定」のため追加しない（リッチリザルト非対象）。Article schema の充実を優先する
- `<meta name="description">` も検索意図に合わせて更新する

**実行前の確認フォーマット**:
```
### コンテンツリライト: /real-phrases/foo/

現在の構成:
  - H2セクション数: X個
  - 推定文字数: 約XXX文字

追加・強化する内容:
  - 「語源・由来」セクション追加
  - 例文を5個→15個に拡充
  - FAQ schema に3問追加
  - meta description 更新

リライトを実行しますか？（時間がかかる場合があります）
```

---

### タイプC: 新規コンテンツ作成

**テンプレートの参照**:
作成するコンテンツタイプ（`real-phrases` / `articles` / `services`）の既存ページを1件読み込み、
HTML構造をテンプレートとして使用する。

**ディレクトリ作成**:
```bash
mkdir -p ~/projects/claude/native-real/{type}/{slug}/
```

**作成するファイル**: `index.html`

**必須要素**:
- GTM スニペット（既存ページからコピー）
- canonical URL
- OGP タグ（og:title, og:description, og:url, og:site_name）
- JSON-LD schema（Article型。FAQPageはGoogle公式方針上native-realでは非対象）
- パンくずリスト
- 内部リンク（関連ページへの導線を最低3件）
- sitemap.xml への追加（`~/projects/claude/native-real/sitemap.xml` を更新）

**実行前の確認フォーマット**:
```
### 新規ページ作成: /real-phrases/foo/

作成内容:
  - タイトル: 「提案タイトル」
  - ターゲットKW: XXX（月間検索Vol: XXX）
  - 主要セクション: [意味, 語源, 例文, 類語, FAQ]
  - sitemap.xml に追加

作成を実行しますか？
```

---

### タイプE: アフィリエイトCTA最適化

**対象**: Tier 1ページ（`/services/*/` または `index.html`）でCTAが弱い・アフィリエイトリンクが未設置の箇所

**確認手順**:
1. 対象ファイルを読み込み、`px.a8.net` リンクの数と配置を確認する
2. H2/H3セクション末尾・比較テーブル内・冒頭・末尾にCTAがあるか確認する

**改善パターン**:

| ケース | 対処 |
|---|---|
| アフィリエイトリンクが未設置 | A8.netアフィリエイトURLを`rel="nofollow noopener" target="_blank"`で追加 |
| CTAボタンが1箇所のみ | 記事冒頭・中間・末尾に計3箇所以上配置する |
| CTAの文言が弱い | 「詳細はこちら」→「無料体験する」「今すぐ試す」等に変更 |
| サービス比較テーブルにCTAなし | 各サービス行の末尾列にボタンを追加 |

**注意**: A8.netのURLは既存ページの`px.a8.net`リンクをそのまま流用する。新規URLの発行はできない。URLが不明な場合は「アフィリエイトURL要確認」と記載してスキップ。

**実行前の確認フォーマット**:
```
### CTA最適化: /services/foo/

現在: CTAボタン X箇所、アフィリエイトリンク X件
改善: [冒頭にCTAボタン追加] [比較テーブルにボタン列追加] [文言を「無料体験する」に統一]

この内容で編集しますか？
```

---

### タイプF: ListenUp問題追加

**対象**: `/listening/` の問題プール拡充

**実行条件**:
- analyzerのH分析で問題プール枯渇サインが検出された場合
- 特定axisの問題数が不足している場合（部長からの指示）
- 定期的な問題補充（月1回目安）

**実行手順**:
```bash
cd ~/projects/claude/native-real

# 全axis均等に生成（通常）
python3 generate_questions.py --count 100

# 特定axis補強（部長指示がある場合）
python3 generate_questions.py --count 100 --axis-only distractor

# 生成後に本番追加（MP3生成 → questions.js追記 → git push）
python3 add_questions.py
```

**品質確認**:
- 生成後のaxis分布を確認（各axis 18〜22%が目標）
- `node --check` は .html に対して使えないため、sed でスクリプト抽出して構文チェック:
  ```bash
  sed -n '/<script>/,/<\/script>/p' listening/index.html > /tmp/listenup_check.js && node --check /tmp/listenup_check.js
  ```

**実行前の確認フォーマット**:
```
### ListenUp問題追加

現在の問題数: X,XXX問
追加予定: XXX問（axis: {指定またはall}）
現在のaxis分布: speed XX% / reduction XX% / vocab XX% / context XX% / distractor XX%

問題生成を実行しますか？（generate → add → git pushまで自動実行）
```

---

### タイプD: Disavow ファイル作成・更新

**ファイルパス**: `~/projects/claude/native-real/disavow.txt`
（注: このファイルは Google Search Console にアップロードするためのものでリポジトリに含めるが、SEOには直接影響しない静的ファイル）

**フォーマット**:
```
# native-real.com Disavow File
# 作成日: YYYY-MM-DD
# 対象: スパムバックリンク

# スパムドメイン
domain:example-spam.com
domain:another-spam.net
...

# 個別URL（ドメイン単位で対応できない場合）
https://example.com/specific-spam-page
```

**作成後のGSCアップロード（自動＋手動）**:

1. browser-use CLI で否認ページを自動で開く:
   ```
   bu -s ichi-eigo open "https://search.google.com/search-console/disavow-links?resource_id=https%3A%2F%2Fnative-real.com%2F"
   ```
2. ページが開いたらユーザーに以下を依頼する:
   ```
   disavow.txt を更新しました（X件のスパムドメイン）。

   ブラウザにSearch Consoleの否認ページを開きました。
   「否認リストをアップロード」（または「置き換える」）をクリックし、
   以下のファイルを選択してください:
     ~/projects/claude/native-real/disavow.txt

   ⚠️ 注意: 「否認をキャンセル」は絶対にクリックしないでください（既存の否認が全解除されます）
   ```
3. ユーザーがアップロード完了を報告したら次のステップに進む

**注意**: Google Search ConsoleにはDisavow用のAPIがないため、ファイル選択のみユーザーの手動操作が必要。ページを開くところまでは自動化する。

---

## Step 2: git commit & push

全アクションの実行後、まとめてコミット・プッシュする。

```bash
cd ~/projects/claude/native-real && \
git add -A && \
git commit -m "SEO改善: {変更内容の要約}

- {アクション1の説明}
- {アクション2の説明}
..." && \
git push origin main
```

**コミットメッセージの形式**:
- プレフィックス: `SEO改善:` / `コンテンツ追加:` / `タイトル改善:`
- 変更ページ数が3件以上なら「X件のページを更新」でまとめてよい
- Disavowは「スパムバックリンクDisavowファイル追加」

Push 完了後、ユーザーに結果を報告する:
```
✅ 完了しました。

実行内容:
  1. /real-phrases/by-the-way/ コンテンツリライト
  2. /articles/eiken-2kyuu-interview/ タイトル改善

GitHub Pages への反映: 1〜2分後
確認URL: https://native-real.com/real-phrases/by-the-way/
```

---

## ⚠️ ファイル編集の絶対ルール（2026-04-02制定・インシデントより）

### 既存ファイルは必ず Edit ツール（差分編集）を使う

- **既存の `index.html` を修正する場合は Edit ツールのみ使用すること**
- Write ツールによるファイル全体の上書きは**絶対禁止**
- 理由: Write で上書きすると既存コンテンツ（CSS・FAQ・比較テーブル等）が全削除される事故が発生した（2026-04-02インシデント: rarejob 1,481行→169行、dmm-eikaiwa 1,215行→145行）

### 変更後の行数チェック（必須）

ファイルを編集したら必ず行数変化を確認する:

```bash
git diff --stat HEAD
```

**判定基準**:
- 削減が 50行以内 → 正常範囲（メタタグ・title等の小修正）
- 削減が 50〜200行 → ⚠️ WARNING: 変更内容を再確認してからコミット
- 削減が 200行超 → 🚨 STOP: コミットせずに即停止。`git checkout -- {ファイル}` で復元してやり直す

### services/ ページの特別注意

`services/*/index.html` は1,000行以上の大型ファイル。JSON-LDやtitleのみ変更する場合でも削減行数が50行を超えたら必ず停止すること。

---

## デザインシステム準拠ルール（必須）

HTML/CSSを編集・新規作成する際は、以下を厳守すること。

- 参考資料: `ai-company/docs/reference/lovable-DESIGN.md`（Lovable公式デザインシステムの9セクション構成。コンポーネント設計・レイアウト・Do's/Don'tsの詳細はこちらを参照）

1. 作業開始前に `DESIGN.md` を読むこと
2. CSS変数は `assets/global-design.css` で定義済み。ハードコード色値禁止
3. カラーパレット:
   - ページ背景: `#F8F6F1`（クリーム）。純白 `#FFFFFF` 禁止
   - カード背景: `#FDFCF9`
   - ボーダー: `#E8E4DC`
   - テキスト: `rgba(26,26,26, 0.88/0.62/0.42)`。`rgba(0,0,0,...)` 禁止
   - アクセント: ゴールド `#F5A623`（CTAとアクティブ状態のみ）
4. タイプCの新規ページ作成時:
   - `<link rel="stylesheet" href="/assets/global-design.css">` を `</head>` 直前に必ず挿入
   - ヘッダー背景: `rgba(248,246,241,0.92)`
   - ボタン: Primary CTAはゴールドグラデーション、border-radius: 9999px
5. タイプBのリライト時: 既存のCSS変数を壊さないこと

---

## エッジケース処理

| ケース | 対処 |
|---|---|
| seo_report.md が存在しない | 「先に `/native-real-seo-analyzer` を実行してください」と案内 |
| 対象HTMLファイルが存在しない | `find ~/projects/claude/native-real -name "index.html" -path "*{slug}*"` で検索し確認 |
| リライト後にファイルサイズが元より小さい | 警告を出してユーザーに確認を求める（コンテンツ削除ミスの防止） |
| sitemap.xml の更新漏れ | 新規ページ作成時は必ず sitemap.xml を確認・更新する |
| git push 失敗 | エラー内容を表示し、`git status` で状態を確認してユーザーに報告 |

---

## 実装メモ

- Opus 4.6 を使用（高品質な日本語コンテンツ生成のため）
- コンテンツ生成は「英語学習者向け・日本語で解説」のトーンを維持する
- 英語フレーズページは「ネイティブが実際に使う文脈」を重視した例文を作る
- SEOを意識しつつも、読者が読んで価値を感じる内容を最優先にする
- HTMLの構造（GTMスニペット・canonical・JSON-LD等）は既存ページのパターンを厳守する

### E-E-A-T 対応（Google公式強化項目）
- **著者byline**: 新規ページ・リライト時に `<meta name="author">` と JSON-LD の `author` に著者情報を明示する
- **AI生成開示**: Claude が生成したコンテンツには JSON-LD に `"description": "AI支援により作成"` またはフッターに「本記事はAIを活用して作成しています」の一文を追加する（Googleのスパムポリシー遵守）
- **信頼性（Trustworthiness）**: E-E-A-Tの中で最重要。外部データの引用元・更新日・監修者の明示を優先する

---

## kioku-shinai 改善実行（追加対象）

seo_report.md の Section K で提案されたkioku-shinai向けアクションを実行する。

### 対象リポジトリ

```
~/projects/claude/kioku-shinai
```

### 実行可能なアクション

| アクション種別 | 対象ファイル | 説明 |
|---|---|---|
| UI改善 | `src/app/trial/trial-app.tsx` | 選択肢サイズ、余白、フォント等の調整 |
| 解説改善 | `public/data/{word}.json` | 語源説明、認知言語学、hook等のテキスト修正 |
| 単語追加 | `public/data/` + `public/audio/` | 新しい単語データJSON + Edge TTS音声生成 |
| 出題形式改善 | `public/data/{word}.json` の formats | 選択肢・文・ヒントの改善 |
| LP改善 | `src/app/page.tsx` | ランディングページのコピー・構成変更 |

### 単語データ追加手順

1. Claude APIで単語データJSONを生成（`src/lib/types.ts` の `WordData` 型に準拠）
2. `kioku-shinai-fact-checker` スキルで検証
3. `python3 scripts/generate_audio.py` で音声生成
4. `public/data/{word}.json` と `public/audio/{word}/` に配置
5. git commit & push

### デプロイ

```bash
cd ~/projects/claude/kioku-shinai && git add -A && git commit -m "{変更内容}" && git push origin main
```
