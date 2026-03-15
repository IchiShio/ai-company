---
name: native-real-seo-checker
description: |
  native-real.com SEOパイプラインの各スキルが
  求められるパフォーマンスを発揮しているか検査するスキル。
  手抜き・不完全実行・基準未達を検出し、NGなら即中断して報告する。

  通常は native-real-seo-pipeline の各ステップ後に自動呼び出しされる。
  単独実行も可能（最新の日付フォルダと git log を読んで全チェック）。
---

# native-real.com SEO チェッカー

## 出力フォーマット

チェック結果は以下の形式で出力する:

```
## ✅/❌ Check {N}: {スキル名}

| 項目 | 結果 | 詳細 |
|---|---|---|
| ... | ✅/❌/⚠️ | ... |

→ 判定: PASS / FAIL（理由）
```

- **✅ PASS**: 基準を満たしている
- **⚠️ WARNING**: 基準ギリギリ or 推奨事項あり（処理は継続）
- **❌ FAIL**: 基準未達 → パイプラインを**即中断**してユーザーに報告

---

## Check 0: テクニカルSEOベースラインチェック

**実行タイミング**: パイプライン実行前（Step 1 の前）。月1回、または新規ページ追加時。

**検査対象**: `~/projects/claude/native-real/` 内の全 index.html ファイル
- `articles/*/index.html`
- `real-phrases/*/index.html`
- `services/*/index.html`
- `index.html`（トップページ）

### 検査項目

**0-A. 必須メタタグの完全性（各ページ）**

| タグ | 必須 | 確認方法 |
|---|---|---|
| `<title>` | 必須 | 60文字以内（サフィックス含む） |
| `<meta name="description">` | 必須 | 70〜120文字 |
| `<meta name="author">` | 必須 | 存在するか |
| `<meta property="og:title">` | 必須 | 存在するか |
| `<meta property="og:description">` | 必須 | 存在するか |
| `<meta property="og:image">` | 必須 | 存在するか |
| `<meta property="og:url">` | 必須 | 存在するか |
| `<meta property="og:type">` | 必須 | 存在するか |
| `<meta property="og:locale">` | 必須 | `ja_JP` であるか |
| `<meta name="twitter:card">` | 必須 | 存在するか |
| `<meta name="twitter:title">` | 必須 | 存在するか |
| `<meta name="twitter:description">` | 必須 | 存在するか |

**0-B. 構造化データの完全性（各ページ）**

| スキーマ | 必須 | 確認方法 |
|---|---|---|
| datePublished | 必須 | JSON-LDに含まれるか |
| dateModified | 必須 | JSON-LDに含まれるか |
| author (Person) | 必須 | JSON-LDに `"@type": "Person"` が含まれるか |
| FAQPage | 推奨 | `articles/*/` と `services/*/` には推奨、`real-phrases/*/` は任意 |

**0-C. 判定ルール**

- 必須タグが欠落しているページが1つでもある → ⚠️ WARNING（リストを出力）
- 全ページ完備 → ✅ PASS
- Check 0 は ❌ FAIL にはしない（既存ページの基盤整備なので、パイプラインは止めない）
- ⚠️ WARNING が出たら、executorに修正リストを渡して一括修正させる

**0-D. 出力形式**

```
## ✅/⚠️ Check 0: テクニカルSEOベースライン

検査ページ数: XX件
完全準拠: XX件
要修正: XX件

要修正ページ一覧:
| ページ | 欠落タグ |
|---|---|
| /articles/xxx/ | og:locale, twitter:title, twitter:description |
| /services/xxx/ | author, datePublished, FAQPage |
...

→ 判定: WARNING（XX件のページに欠落あり）
```

---

## Check 1: native-real-data-collector の検査

**実行タイミング**: Step 1（データ収集）完了後

### 検査項目

**1-A. ファイル存在確認**

今日の日付フォルダ内に以下のファイルが存在するか確認する:

| ファイル | 必須/任意 |
|---|---|
| `queries.csv` | **必須** |
| `pages.csv` | **必須** |
| `dates.csv` | **必須** |
| `devices.csv` | 任意 |
| `countries.csv` | 任意 |
| `ga4_traffic.csv` | **必須** |
| `ga4_pages.csv` | **必須** |
| `ahrefs_metrics.csv` | 任意（MCP接続時は必須） |
| `ahrefs_keywords.csv` | 任意（MCP接続時は必須） |
| `ahrefs_backlinks.csv` | 任意（MCP接続時は必須） |
| `collection_log.txt` | **必須** |

**1-B. 行数チェック**

| ファイル | 最低行数 | 基準 |
|---|---|---|
| `queries.csv` | 10行 | 少なすぎるとSCデータが不完全 |
| `pages.csv` | 5行 | 少なすぎるとSCデータが不完全 |
| `dates.csv` | 14行 | 28日分の半分以上 |
| `ga4_traffic.csv` | 2行 | チャネルが最低2種類 |
| `ga4_pages.csv` | 5行 | ページデータが少なすぎる |

**1-C. collection_log.txt の確認**

- 「エラー」が含まれていないか確認
- エラーがある場合は ⚠️ WARNING（必須ファイルが取得できなかった場合は ❌ FAIL）

**1-D. 判定ルール**

- 必須ファイルが1つでも欠落 → ❌ FAIL → パイプライン中断
- 行数基準未達 → ⚠️ WARNING（処理は継続、ただし分析の信頼性が低い旨を注記）
- 全項目OK → ✅ PASS

---

## Check 2: native-real-seo-analyzer の検査

**実行タイミング**: Step 2（分析）完了後

### 検査項目

**2-A. seo_report.md の存在確認**

今日の日付フォルダに `seo_report.md` が保存されているか確認する。
存在しない → ❌ FAIL → パイプライン中断

**2-B. 8分析セクションの完全性**

seo_report.md に以下のセクションが全て含まれているか確認する:

| セクション | 見出しキーワード |
|---|---|
| A. クイックウィン | `## A.` または `クイックウィン` |
| B. 高インプレ低CTR | `## B.` または `高インプレ` |
| C. チャネル品質 | `## C.` または `チャネル品質` |
| D. コンテンツ品質 | `## D.` または `コンテンツ品質` |
| E. キーワード機会 | `## E.` または `キーワード機会` |
| F. バックリンク品質 | `## F.` または `バックリンク` |
| G. 28日間トレンド | `## G.` または `28日間トレンド` |
| H. ListenUpエンゲージメント | `## H.` または `ListenUp` |

- データ不足でスキップされたセクションは「スキップ理由が明記されているか」を確認
- 理由なくスキップ → ⚠️ WARNING

**2-C. Top 5 アクションの具体性チェック**

Top 5 テーブルの各行を確認し、以下の基準を満たしているか採点する:

| 基準 | OK例 | NG例 |
|---|---|---|
| ページが特定されている | `/real-phrases/by-the-way/` | 「いくつかのページ」 |
| 変更内容が具体的 | `titleを「〜」に変更` | 「タイトルを改善する」 |
| 推定クリック増が数値 | `+120回` | 「多い」 |
| 工数が明記 | `小` / `中` / `大` | 空欄 |

- 5件中3件以上が具体性基準を満たさない → ❌ FAIL
- 1〜2件が曖昧 → ⚠️ WARNING

**2-D. 判定ルール**

- seo_report.md なし → ❌ FAIL
- Top 5 が5件未満 → ❌ FAIL
- 具体性不足が3件以上 → ❌ FAIL
- 理由なきセクションスキップあり → ⚠️ WARNING
- 全項目OK → ✅ PASS

---

## Check 3: native-real-seo-executor の検査

**実行タイミング**: Step 3（実行）完了後

### 検査項目

**3-A. git コミット確認**

```bash
cd ~/projects/claude/native-real && git log --oneline -1
```

- 今日の日付のコミットが存在するか確認
- コミットがない → ❌ FAIL

**3-B. 実行件数の確認**

- `git diff HEAD~1 --name-only` で変更されたファイル一覧を取得
- seo_report.md の Top 5 件数と変更ファイル数を照合
- 未実行のアクションがあれば ❌ FAIL

**3-C. コンテンツリライトの品質チェック**

リライト対象ファイルを読み込んで以下を確認する:

| 基準 | 最低ライン | 理想 |
|---|---|---|
| 本文文字数 | 2,000文字以上 | 3,000文字以上 |
| H2セクション数 | 4個以上 | 6個以上 |
| FAQPage JSON-LD | 2問以上 | 4問以上 |
| ファイルサイズ | 変更前より大きい | — |

- ファイルサイズが変更前より小さい → ❌ FAIL（コンテンツ消失の危険）
- 文字数2,000未満 → ❌ FAIL
- 文字数2,000〜3,000 → ⚠️ WARNING
- 文字数3,000以上 → ✅

**3-D. タイトル・メタの品質チェック**

title / meta改善が行われたページに対して確認する:

| タグ | 最低 | 基準 | 上限 |
|---|---|---|---|
| `<title>` | 25文字 | 28〜32文字 | 35文字 |
| `<meta name="description">` | 80文字 | 100〜120文字 | 130文字 |
| `og:title` | — | titleと一致または近似 | — |
| `og:description` | — | descriptionと一致または近似 | — |
| JSON-LD `headline` | — | titleと一致 | — |

- 基準範囲外 → ⚠️ WARNING（アクセス改善効果が落ちる）
- og/JSON-LD の更新漏れ → ❌ FAIL

**3-E. git push 確認**

```bash
cd ~/projects/claude/native-real && git status
```

- `nothing to commit, working tree clean` かつリモートと同期済み → ✅
- push されていない → ❌ FAIL

**3-F. 判定ルール**

- コミットなし → ❌ FAIL
- 未実行アクションあり → ❌ FAIL
- ファイルサイズ縮小 → ❌ FAIL
- og/JSON-LD 更新漏れ → ❌ FAIL
- 文字数・title文字数が範囲外 → ⚠️ WARNING
- 全項目OK → ✅ PASS

---

## FAIL 時の対応（自動リカバリー）

❌ FAIL が発生した場合は**即中断せず、まず自動リカバリーを1回試みる**。

### リカバリー手順

**Check 1 FAIL（データ欠損）**
1. 欠損しているファイルのソース（SC / GA4 / Ahrefs）を特定する
2. そのソースだけ再取得を試みる（`native-real-data-collector` の該当手順のみ実行）
3. 再取得後、Check 1 を再実行する
4. 再チェックも FAIL → `native-real-bucho` にエスカレーション

**Check 2 FAIL（分析不完全 / Top5が曖昧）**
1. 失敗した項目を特定する（欠落セクション or 曖昧なアクション）
2. `native-real-seo-analyzer` に該当部分の再分析を指示する:
   - セクション欠落 → 該当セクション（例: E. キーワード機会）だけ再実行
   - Top5が曖昧 → Top5の生成ロジックを再実行し、ページ名・変更内容・数値を明示させる
3. seo_report.md を更新し、Check 2 を再実行する
4. 再チェックも FAIL → `native-real-bucho` にエスカレーション

**Check 3 FAIL（品質基準未達 / 実行漏れ）**
1. 失敗した項目を特定する（未実行アクション / 文字数不足 / title超過 / OGタグ漏れ / push漏れ）
2. 問題を修正する:
   - 未実行アクション → `native-real-seo-executor` で該当アクションを再実行
   - 文字数不足 → 該当セクションにコンテンツを追記
   - title文字数超過 → titleを基準範囲（28〜32字）に収まるよう修正
   - OGタグ / JSON-LD 更新漏れ → 該当箇所を修正
   - git push漏れ → `git push origin main` を再実行
3. 修正後、Check 3 を再実行する
4. 再チェックも FAIL → `native-real-bucho` にエスカレーション

### リトライ上限

- リカバリーは**各 Check につき1回まで**
- 2回目も FAIL の場合は `native-real-bucho` に以下のフォーマットでエスカレーションする:

```
エスカレーション元: Check {N} - {スキル名}

問題: {具体的な問題内容}
試みたリカバリー: {実施した対処内容}
結果: 解決できませんでした
```

⚠️ WARNING の場合はリカバリー不要。報告のみ行い処理を継続する。

---

## 単独実行時の動作

`/native-real-seo-checker` を単独で呼び出した場合:
1. まず Check 0（テクニカルSEOベースライン）を実行
2. 最新日付フォルダを自動検出
3. Check 1 → Check 2 → Check 3 の順に全て実行
4. 総合スコアを表示:
   ```
   ## 総合チェック結果
   Check 0 (baseline):  ✅ PASS
   Check 1 (collector): ✅ PASS
   Check 2 (analyzer):  ✅ PASS
   Check 3 (executor):  ⚠️ WARNING（title 33文字 - 基準超過）
   ```
