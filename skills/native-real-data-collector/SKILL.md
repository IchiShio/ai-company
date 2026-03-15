---
name: native-real-data-collector
description: |
  native-real.com（英語学習サービス比較サイト）のSEOデータを自動収集するスキル。
  Google Search Console・Google Analytics・Ahrefsから日次データを取得し、
  CSVファイルとしてGoogle Driveに保存する。分析は行わず、データ収集と保存のみを担当。

  次のような依頼で必ず使用すること：
  - 「SEOデータを取ってきて」「サーチコンソールのデータを取得して」
  - 「アナリティクスの数字を集めて」「Ahrefsのデータを確認して」
  - 「native-real.comの最新データを集めて」「アクセスデータを保存して」
  - 定時実行（スケジュールタスク）からの自動起動
---

# native-real.com SEOデータ収集スキル

## 概要

このスキルはデータの**収集と保存だけ**を行う。分析や改善提案は別のスキルが担当する。

対象サイト: https://native-real.com （英語学習サービス比較サイト）

## データソースと取得項目

### 1. Google Search Console

Search Console APIまたはブラウザから以下を取得する。

**検索パフォーマンスデータ（過去28日間）:**
- クエリ別: キーワード、表示回数、クリック数、CTR、平均掲載順位
- ページ別: URL、表示回数、クリック数、CTR、平均掲載順位
- デバイス別: デスクトップ/モバイル/タブレットの内訳

**取得手順（ブラウザ自動操作）:**

ブラウザツール（Claude in Chrome）を使ってSearch Consoleにアクセスする。
事前条件: PCが起動しており、Chromeが開いていること。Googleアカウント（ichieigo7@gmail.com）でログイン済みであること。別のアカウントでログインしている場合は、右上のアカウントアイコンからichieigo7@gmail.comに切り替える。

1. `https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fnative-real.com%2F&num_of_days=28` にアクセスする
   - ドメインプロパティ（sc-domain）ではなくURLプレフィックス（https://native-real.com/）で登録されている
2. ページが読み込まれたら、日付フィルタが「28日間」になっていることを確認する
3. **一括エクスポート**:
   - ページ右上の「エクスポート」ボタン（↓アイコン）をクリックする
   - 「CSV をダウンロード」を選択する
   - ZIPファイルがダウンロードされる（中に複数CSVが格納されている）
4. **ZIPを展開して必要なファイルを取り出す**:
   - ダウンロードフォルダからZIPファイルを見つける（ファイル名例: `https___native-real.com_-Performance-on-Search-YYYY-MM-DD.zip`）
   - ZIPを展開すると以下のCSVが入っている:
     - クエリ.csv → `queries.csv` にリネーム
     - ページ.csv → `pages.csv` にリネーム
     - デバイス.csv → `devices.csv` にリネーム
     - 国.csv → `countries.csv` にリネーム
     - 日付チャート.csv → `dates.csv` にリネーム
   - 日本語ファイル名は文字化けすることがあるので、中身のヘッダー行で判別する:
     - 「上位のクエリ」→ クエリデータ
     - 「上位のページ」→ ページデータ
     - 「デバイス」→ デバイスデータ
     - 「国」→ 国データ
     - 「日付」→ 日付チャートデータ

**ブラウザが使えない場合のフォールバック:**
- Ahrefsが接続されている場合は `site-explorer-organic-keywords` と `site-explorer-pages-by-traffic` で代替データを取得する
- どちらも使えない場合はスキップし、ログに記録する

### 2. Google Analytics（GA4）

GA4からトラフィックデータを取得する。

**GA4プロパティ情報:**
- アカウント: skill-up-media
- プロパティ: native-real.com
- プロパティID: a382654252p525926980

**取得するレポート（過去28日間）:**
- トラフィック獲得: チャネル別（Direct / Organic Search / Organic Social / Referral）のセッション数、エンゲージメント率など
- ページとスクリーン: ページ別の表示回数、アクティブユーザー数、エンゲージメント時間など

**取得手順（ブラウザ自動操作）:**

ブラウザツール（Claude in Chrome）を使ってGA4にアクセスする。
事前条件: PCが起動しており、Chromeが開いていること。Googleアカウント（ichieigo7@gmail.com）でログイン済みであること。

1. **トラフィック獲得レポートの取得**:
   - `https://analytics.google.com/analytics/web/#/a382654252p525926980/reports/explorer?r=lifecycle-traffic-acquisition-v2&ruid=lifecycle-traffic-acquisition-v2,business-objectives,generate-leads&collectionId=business-objectives` にアクセスする
   - ページが読み込まれたら「トラフィック獲得」レポートが表示されていることを確認する
   - 右上の共有アイコン（↗）をクリック → 「ファイルをダウンロード」→ 「CSV 形式でダウンロード」を選択する
   - **重要**: Braveブラウザではダウンロードファイルが `.com.brave.Browser.XXXXXX` という一時ファイル名で保存されることがある。ダウンロードフォルダで最新の `.com.brave.Browser.*` ファイルを探し、中身のヘッダー行に「トラフィック獲得」が含まれていれば該当ファイル
   - このファイルを `ga4_traffic.csv` としてリネーム・保存する

2. **ページとスクリーンレポートの取得**:
   - `https://analytics.google.com/analytics/web/#/a382654252p525926980/reports/explorer?r=all-pages-and-screens&ruid=all-pages-and-screens,business-objectives,examine-user-behavior&collectionId=business-objectives` にアクセスする
   - ページが読み込まれたら「ページとスクリーン」レポートが表示されていることを確認する
   - 同様に共有 → ファイルをダウンロード → CSV 形式でダウンロードする
   - ヘッダー行に「ページとスクリーン」が含まれていることを確認し、`ga4_pages.csv` としてリネーム・保存する

**一時ファイルの識別方法:**
GA4からのCSVダウンロードはBraveブラウザで正規のファイル名にリネームされないことがある。以下の手順で識別する:
1. ダウンロードフォルダで `ls -lat .com.brave.Browser.*` を実行し、タイムスタンプが最新のファイルを見つける
2. `head -3 <ファイル>` でヘッダーコメントを確認する（レポート名が記載されている）
3. 該当ファイルを正しいファイル名にコピーする

**CSVの構造:**
GA4のCSVは先頭にコメント行（`#` で始まる）があり、その後にヘッダー行とデータ行が続く:
```
# ----------------------------------------
# トラフィック獲得: セッションのメインのチャネル グループ（デフォルト チャネル グループ）
# アカウント: skill-up-media
# プロパティ: native-real.com
# ----------------------------------------
#
# すべてのユーザー
# 開始日: YYYYMMDD
# 終了日: YYYYMMDD
セッションのメインのチャネル グループ（デフォルト チャネル グループ）,セッション,エンゲージのあったセッション数,...
Direct,114,36,...
```

**ブラウザが使えない場合:**
スキップし、ログに「GA4データ: ブラウザアクセス不可のためスキップ」と記録する

### 3. Ahrefs（MCP接続時のみ）

Ahrefs MCPが接続されている場合のみ実行する。接続されていなければスキップ。

**取得するデータ（4ツール）:**

1. `site-explorer-metrics` → `ahrefs_metrics.csv`
   - パラメータ: `target=native-real.com`, `date=YYYY-MM-DD`, `mode=subdomains`
   - 取得項目: org_keywords, org_traffic, org_cost, paid_keywords, paid_traffic 等

2. `site-explorer-organic-keywords` → `ahrefs_keywords.csv`
   - パラメータ: `target=native-real.com`, `date=YYYY-MM-DD`, `mode=subdomains`, `limit=10`, `order_by=sum_traffic:desc`
   - `select=keyword,volume,best_position,sum_traffic,best_position_url`
   - **注意**: カラム名は `position` ではなく `best_position`、`traffic` ではなく `sum_traffic`、`url` ではなく `best_position_url`

3. `site-explorer-pages-by-traffic` → `ahrefs_pages.csv`
   - パラメータ: `target=native-real.com`, `mode=subdomains`
   - トラフィック帯域別ページ数の分布データ

4. `site-explorer-all-backlinks` → `ahrefs_backlinks.csv`
   - パラメータ: `target=native-real.com`, `mode=subdomains`, `limit=10`, `order_by=first_seen:desc`
   - `select=url_from,url_to,anchor,domain_rating_source,first_seen`

**共通ルール:**
- 全ツールで `mode=subdomains` を指定する（`mode=domain` だとwwwサブドメインが除外される）
- Liteプラン（¥19,900/月）の制限: 25,000 APIユニット/月、1リクエスト最大10行
- 4ツール合計の1回あたりAPIユニット消費: 約386ユニット（日次実行で月約12,000ユニット）

---

## 保存フォーマット

全データをCSVファイルとしてGoogle Drive同期フォルダに保存する。ローカルに保存するだけでGoogle Driveに自動反映される。

### 保存先パス

**ローカルパス（Google Drive同期フォルダ）:**
```
/Users/yusuke/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/
```

**Google Drive上の場所:**
- マイドライブ → GoogleG4,SearchConsole
- フォルダID: `1UsvXavXHcvX8W95iAu0p-jJnrRyyZ-0l`

### フォルダ構造

```
GoogleG4,SearchConsole/
└── YYYY-MM-DD/
    ├── queries.csv
    ├── pages.csv
    ├── devices.csv
    ├── countries.csv
    ├── dates.csv
    ├── ga4_traffic.csv
    ├── ga4_pages.csv
    ├── ahrefs_metrics.csv
    ├── ahrefs_keywords.csv
    ├── ahrefs_pages.csv
    ├── ahrefs_backlinks.csv
    └── collection_log.txt
```

### CSVのルール
- 文字コード: UTF-8（BOM付き、Excelで文字化けしないように）
- 1行目は必ずヘッダー行
- 日本語のキーワードやページタイトルはそのまま保存（エンコードしない）
- 数値はカンマ区切りにしない（1000を「1,000」にしない）

### collection_log.txt

毎回の実行結果を記録するログファイル。以下の情報を含める：

```
実行日時: YYYY-MM-DD HH:MM
取得結果:
  - Search Console: [成功/スキップ/エラー] (行数: XX)
  - GA4: [成功/スキップ/エラー] (行数: XX)
  - Ahrefs概要: [成功/スキップ/エラー]
  - Ahrefsキーワード: [成功/スキップ/エラー] (行数: XX)
  - Ahrefsページ: [成功/スキップ/エラー] (行数: XX)
  - Ahrefsバックリンク: [成功/スキップ/エラー] (行数: XX)
備考: [エラー内容やスキップ理由があれば記載]
```

---

## 保存手順

1. Google Drive同期フォルダ `/Users/yusuke/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/` にアクセスする
   - Coworkセッションでは `request_cowork_directory` で `~/マイドライブ` をマウントする
   - マウント後のVMパスは `/sessions/.../mnt/マイドライブ/GoogleG4,SearchConsole/`
2. 日付フォルダ（`YYYY-MM-DD`）を `mkdir -p` で作成する
3. 各CSVファイルをコピーまたは直接書き込みする
4. collection_log.txt を作成する
5. Google Driveデスクトップアプリが自動的にクラウドに同期する

**注意**: Google Drive同期フォルダにアクセスできない場合（スケジュールタスクなどでCoworkセッションでない場合）は、ローカルの作業ディレクトリにCSVを保存し、次回Coworkセッション時にユーザーに移動を依頼する。

---

## エラー時の動作

- 各データソースは独立して取得を試みる。1つが失敗しても他は続行する
- エラーが発生した場合は collection_log.txt にエラー内容を記録する
- 全データソースが失敗した場合でも、空のログファイルだけは保存する（「今日は取得できなかった」という記録自体に価値がある）
- ブラウザアクセスが必要なデータソース（GA4、Search Console直接アクセス）は、ブラウザが使えない環境ではスキップする
