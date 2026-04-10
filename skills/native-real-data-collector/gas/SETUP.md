# GAS セットアップ手順

ichieigo7@gmail.com でログインした状態で作業してください。

## 1. GASプロジェクトを作成

https://script.google.com/home を開き「新しいプロジェクト」を作成。
プロジェクト名: `native-real-seo-data-collector`

## 2. コードを貼り付け

- エディタに表示されているデフォルトコードを全て削除
- `seo_data_collector.gs` の内容をすべてコピペ
- 保存（Ctrl+S）

## 3. マニフェストを編集

- 左メニュー「プロジェクトの設定」→「「appsscript.json」マニフェスト ファイルをエディタで表示する」をON
- エディタに `appsscript.json` が表示されるので内容を `appsscript.json` の内容で上書き
- 保存

## 4. 初回認証

- エディタ上部「実行」→「関数を選択」→ `collectSEOData` を選択
- ▶ 実行ボタンをクリック
- 「権限を確認」→ ichieigo7@gmail.com を選択 → 「詳細」→「安全でないページに移動」→「許可」
- 実行が完了するまで待つ（30秒〜1分）
- Google Drive の `GoogleG4,SearchConsole/YYYY-MM-DD/` にCSVが保存されていれば成功

## 5. 毎朝6時の自動実行トリガーを設定

- 左メニュー「トリガー」→「トリガーを追加」
- 設定:
  - 実行する関数: `collectSEOData`
  - イベントのソース: 時間主導型
  - 時間ベースのトリガーのタイプ: 日付ベースのタイマー
  - 時刻: 午前6時〜7時
- 保存

## 確認ポイント

- Drive の `GoogleG4,SearchConsole/` フォルダに日付フォルダが作られること
- フォルダ内に以下のファイルがあること:
  - `queries.csv` / `pages.csv` / `dates.csv` / `devices.csv` / `countries.csv`
  - `ga4_traffic.csv` / `ga4_pages.csv`
  - `collection_log.txt`

## トラブルシュート

| エラー | 原因と対処 |
|---|---|
| `Exception: You do not have permission to call...` | 認証スコープ不足 → appsscript.json の oauthScopes を確認 |
| SC `403 Forbidden` | Search Consoleのプロパティにアクセス権がない → ichieigo7 でSCにアクセスできるか確認 |
| GA4 `400 Bad Request` | プロパティIDが違う → CONFIG.GA4_PROPERTY_ID を確認（現在: 525926980） |
| Drive ファイル保存失敗 | DRIVE_FOLDER_ID が違う → `1LnafXdJFw1wW9ROg2ldtdOd1lWcqJfd_` を確認 |
