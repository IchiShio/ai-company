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

**取得手順（browser-use CLI）:**

browser-use CLI（`bu`）の `ichi-eigo` セッションを使ってSearch Consoleにアクセスする。
事前条件: `bu -s ichi-eigo` セッションが起動済みで、ichieigo7@gmail.com でログイン済みであること。

セッション起動コマンド（未起動の場合）:
```bash
bu -s ichi-eigo open "https://accounts.google.com"
```

**ダウンロードフォルダ**: browser-use の Chromium はダウンロードを一時フォルダに保存する。
場所を特定するには:
```bash
find /var/folders -name "browser-use-downloads-*" -type d 2>/dev/null
```
日本語ファイル名が文字化けするため、ZIPの展開はPythonで行う:
```python
import zipfile, os
zf = zipfile.ZipFile('ダウンロードしたZIPパス')
for i, info in enumerate(zf.infolist()):
    data = zf.read(info.filename)
    header = data.decode('utf-8-sig', errors='replace').split('\n')[0]
    # ヘッダーでファイル種類を判定してリネーム
```

1. Search Console にアクセスする:
```bash
bu -s ichi-eigo open "https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fnative-real.com%2F&num_of_days=28"
```
   - ドメインプロパティ（sc-domain）ではなくURLプレフィックス（https://native-real.com/）で登録されている
2. ページ読み込み後、`bu -s ichi-eigo state` で日付フィルタが「28日間」になっていることを確認する
3. **一括エクスポート**:
   - `bu -s ichi-eigo state` で「エクスポート」ボタンのインデックスを特定する
   - `bu -s ichi-eigo click INDEX` でエクスポートボタンをクリックする
   - 表示されたメニューから「CSV をダウンロード」のインデックスを特定し `bu -s ichi-eigo click INDEX` でクリックする
   - ZIPファイルがダウンロードされる（中に複数CSVが格納されている）
4. **ZIPを展開して必要なファイルを取り出す**:
   - ダウンロードフォルダからZIPファイルを見つける:
     ```bash
     ls -lt ~/Downloads/*.zip | head -3
     ```
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

**カバレッジ（ページインデックス状況）データ:**

検索パフォーマンスに加え、Search Console の「ページ」レポートも取得する。
Googleが直接指摘する404・インデックス未登録等の問題であり、放置するとクロールバジェット浪費やサイト評価低下につながるため**毎回必ず取得する**。

1. Search Console カバレッジページにアクセスする:
```bash
bu -s ichi-eigo open "https://search.google.com/search-console/index?resource_id=https%3A%2F%2Fnative-real.com%2F"
```
2. `bu -s ichi-eigo state` で「ページのインデックス登録」レポートが表示されていることを確認する
3. `bu -s ichi-eigo state` で「エクスポート」ボタンのインデックスを特定 → `bu -s ichi-eigo click INDEX` → 「CSV をダウンロード」を選択する
4. ZIPファイルを展開すると以下が含まれる:
   - メタデータ.csv → `coverage_metadata.csv` にリネーム
   - 重大な問題.csv → `coverage_errors.csv` にリネーム
   - 重大ではない問題.csv → `coverage_warnings.csv` にリネーム
   - 平均読み込み時間のチャート.csv → `coverage_chart.csv` にリネーム
   - 日本語ファイル名が文字化けする場合は中身で判別する:
     - 「プロパティ,値」ヘッダー → メタデータ
     - 「理由,ソース,確認,ページ」ヘッダー → 問題ファイル（行数が多い方が重大な問題）
     - 「日付,未登録,登録済み」ヘッダー → チャート

**重要**: `coverage_errors.csv` に「見つかりませんでした（404）」等のデータ行がある場合、
`collection_log.txt` に `⚠️ カバレッジ問題あり: {問題内容} ({ページ数}件)` と警告を記録すること。

**browser-use セッションが使えない場合のフォールバック:**
- `bu -s ichi-eigo state` がエラーを返す場合、まず `bu -s ichi-eigo open "https://accounts.google.com"` でセッション再起動を試みる
- Googleログインが切れている場合（2段階認証が必要）は、ログに「GSC: Googleログイン切れのためスキップ（手動再ログイン必要）」と記録してスキップする
- Ahrefsが接続されている場合は `site-explorer-organic-keywords` と `site-explorer-pages-by-traffic` で代替データを取得する
- どちらも使えない場合はスキップし、ログに記録する
- カバレッジデータはブラウザ必須のためスキップし、ログに「カバレッジ: ブラウザ不可のためスキップ」と記録する

### 2. Google Analytics（GA4）

GA4からトラフィックデータを取得する。

**GA4プロパティ情報:**
- アカウント: skill-up-media
- プロパティ: native-real.com
- プロパティID: a382654252p525926980

**取得するレポート（過去28日間）:**
- トラフィック獲得: チャネル別（Direct / Organic Search / Organic Social / Referral）のセッション数、エンゲージメント率など
- ページとスクリーン: ページ別の表示回数、アクティブユーザー数、エンゲージメント時間など

**取得手順（browser-use CLI）:**

browser-use CLI（`bu`）の `ichi-eigo` セッションを使ってGA4にアクセスする。
事前条件: `bu -s ichi-eigo` セッションが起動済みで、ichieigo7@gmail.com でログイン済みであること。

1. **トラフィック獲得レポートの取得**:
   ```bash
   bu -s ichi-eigo open "https://analytics.google.com/analytics/web/#/a382654252p525926980/reports/explorer?r=lifecycle-traffic-acquisition-v2&ruid=lifecycle-traffic-acquisition-v2,business-objectives,generate-leads&collectionId=business-objectives"
   ```
   - `bu -s ichi-eigo state` で「トラフィック獲得」レポートが表示されていることを確認する
   - `bu -s ichi-eigo state` で共有アイコンのインデックスを特定 → `bu -s ichi-eigo click INDEX`
   - 「ファイルをダウンロード」→ 「CSV 形式でダウンロード」を順にクリックする
   - ダウンロードフォルダで最新ファイルを探す:
     ```bash
     ls -lt ~/Downloads/*.csv 2>/dev/null | head -3
     ```
   - このファイルを `ga4_traffic.csv` としてリネーム・保存する

2. **ページとスクリーンレポートの取得**:
   ```bash
   bu -s ichi-eigo open "https://analytics.google.com/analytics/web/#/a382654252p525926980/reports/explorer?r=all-pages-and-screens&ruid=all-pages-and-screens,business-objectives,examine-user-behavior&collectionId=business-objectives"
   ```
   - `bu -s ichi-eigo state` で「ページとスクリーン」レポートが表示されていることを確認する
   - 同様に共有 → ファイルをダウンロード → CSV 形式でダウンロードする
   - ヘッダー行に「ページとスクリーン」が含まれていることを確認し、`ga4_pages.csv` としてリネーム・保存する

**ダウンロードファイルの識別:**
browser-use CLI は Chromium を使うため、ダウンロードファイルは正規のファイル名で保存される。
`ls -lt ~/Downloads/*.csv | head -5` で最新ファイルを特定し、`head -3` でヘッダーコメントを確認する。

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

**browser-use セッションが使えない場合:**
スキップし、ログに「GA4データ: browser-useセッション不可のためスキップ」と記録する

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

5. `site-explorer-organic-keywords`（競合） → `ahrefs_competitor_keywords.csv`
   - **ベンチマーク競合のキーワードを取得する**
   - 競合URLは `~/projects/claude/native-real/docs/site-context.md` の「ベンチマーク競合」セクションから読み取る
   - 各競合に対して: `target={competitor_domain}`, `date=YYYY-MM-DD`, `mode=subdomains`, `limit=10`, `order_by=sum_traffic:desc`
   - `select=keyword,volume,best_position,sum_traffic,best_position_url`
   - 出力CSV列: `competitor,keyword,volume,best_position,sum_traffic,best_position_url`
   - 全競合のデータを1ファイルに結合する（`competitor` 列で区別）

6. `site-explorer-organic-competitors` → `ahrefs_competitors.csv`
   - パラメータ: `target=native-real.com`, `mode=subdomains`, `limit=10`
   - native-real.comと有機キーワードが重複する競合サイトを自動検出する

**共通ルール:**
- 全ツールで `mode=subdomains` を指定する（`mode=domain` だとwwwサブドメインが除外される）
- Liteプラン（¥19,900/月）の制限: 25,000 APIユニット/月、1リクエスト最大10行
- 6ツール合計の1回あたりAPIユニット消費: 約590ユニット（週次実行で月約2,400ユニット）

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
    ├── ahrefs_competitor_keywords.csv
    ├── ahrefs_competitors.csv
    ├── coverage_metadata.csv
    ├── coverage_errors.csv
    ├── coverage_warnings.csv
    ├── coverage_chart.csv
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
  - Ahrefs競合キーワード: [成功/スキップ/エラー] (行数: XX)
  - Ahrefs競合検出: [成功/スキップ/エラー] (行数: XX)
  - SCカバレッジ: [成功/スキップ/エラー] (登録済みXX/未登録XX/エラーXX件)
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
- ブラウザアクセスが必要なデータソース（GA4、Search Console直接アクセス）は、`bu -s ichi-eigo` セッションが使えない環境ではスキップする

---

## kioku-shinai データ収集（追加対象）

kioku-shinai（記憶しない英単語）はnative-real部門配下の新サービス。
パイプライン実行時、native-real.comのデータ収集後にkioku-shinaiのデータも収集する。

### データソース

#### 1. localStorage フィードバック（現フェーズ）

kioku-shinaiはまだGA4未設定のため、フィードバックデータはブラウザのlocalStorageに保存されている。
収集方法: browser-use CLI で対象URLを開き、JavaScript で取得する:
```bash
bu -s ichi-eigo open "http://localhost:3002/trial"
bu -s ichi-eigo eval "JSON.stringify(JSON.parse(localStorage.getItem('kioku_feedback') || '[]'))"
```
または `bu -s ichi-eigo eval` で以下を実行:

```javascript
JSON.parse(localStorage.getItem('kioku_feedback') || '[]')
```

取得したJSONを `kioku-shinai-feedback-YYYY-MM-DD.json` として保存する。

#### 2. GA4（将来：GA4設定後）

GA4のプロパティが設定されたら、以下のイベントを収集対象に追加:
- `trial_start`: 体験開始
- `trial_answer`: 回答（正誤・形式・単語）
- `trial_complete`: 体験完了
- `feedback_submit`: フィードバック送信

### 保存先

```
~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/YYYY-MM-DD/
└── kioku-shinai-feedback-YYYY-MM-DD.json
```

### collection_log.txt への追記

```
--- kioku-shinai ---
Feedback records: {N}件
Status: OK / SKIP（データなし） / ERROR（{理由}）
```
