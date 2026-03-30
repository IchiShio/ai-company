---
name: google-seo-updates
description: |
  Google公式SEO情報（コアアップデート・ガイドライン変更）を収集し、
  native-realのSEOスキルへの影響を評価するスキル。
  月1回または「Googleのアップデートを確認して」で使用。
effort: medium
allowed-tools: WebFetch, WebSearch, Read, Write
---

# Google SEO 公式情報収集スキル

**目的**: Googleの公式発表を追跡し、native-real SEOスキルの基準を常に最新の公式ガイドラインと一致させる。

---

## Step 1: 情報収集

以下のソースから最新情報を取得する:

### A. Google Search Central Blog（コアアップデート・公式発表）
```
URL: https://developers.google.com/search/updates/core-updates?hl=ja
URL: https://developers.google.com/search/blog?hl=ja
```

収集する情報:
- 直近のコアアップデート名・公開日・ロールアウト完了日
- スパムポリシーアップデートの内容
- 検索ランキングシステムの変更

### B. 構造化データ仕様（変更チェック）
```
URL: https://developers.google.com/search/docs/appearance/structured-data/article?hl=ja
URL: https://developers.google.com/search/docs/appearance/structured-data/faqpage?hl=ja
```

確認する項目:
- 必須/推奨プロパティの変更
- FAQPage対象サイトの条件変更
- 新しいschema typeの追加

### C. E-E-A-T・コンテンツ品質ガイドライン
```
URL: https://developers.google.com/search/docs/fundamentals/creating-helpful-content?hl=ja
```

確認する項目:
- E-E-A-T（経験・専門性・権威性・信頼性）評価基準の変更
- AI生成コンテンツに関する新方針
- 著者情報・開示に関する推奨事項の変更

---

## Step 2: 影響評価

取得した情報をもとに、以下のSEOスキルへの影響を評価する:

| スキル | 影響チェック対象 |
|---|---|
| `native-real-seo-pipeline` | Check 0のメタタグ・構造化データ基準 |
| `native-real-seo-analyzer` | FAQPage推奨基準、スコアリングロジック |
| `native-real-seo-executor` | title/description文字数目安、E-E-A-T対応指針 |

影響の判定基準:
- **要修正**: Googleの公式方針と現スキルの記述が矛盾する場合
- **要注記追加**: 公式が「推奨」と位置づけているのに「必須」と書いている場合
- **参考情報**: 直接的な矛盾はないが把握しておくべき変更

---

## Step 3: 知識ベース更新

収集した情報を以下のファイルに保存する:

```
~/projects/claude/native-real/docs/google-seo-updates.md
```

フォーマット:
```markdown
# Google SEO 公式アップデート記録

## {アップデート名}（{日付}）

**種別**: コアアップデート / スパムポリシー / ガイドライン変更
**公式発表URL**: {URL}
**ロールアウト**: {開始日} 〜 {完了日}

### 主な変更点
- {変更1}
- {変更2}

### native-real SEOスキルへの影響
- **影響あり**: {スキル名} → {修正内容}
- **影響なし**: {理由}

---
```

既存ファイルがある場合は**先頭に追記**する（古い記録を消さない）。

---

## Step 4: スキル修正が必要な場合

「要修正」と判定した項目がある場合、各スキルファイルを直接修正する:

1. 修正対象を列挙し、変更前/変更後を明示する
2. `Edit` ツールで修正を実施
3. 修正後に変更サマリーを出力する

---

## 出力フォーマット

```
## Google SEO 公式情報収集レポート（{日付}）

### 直近のアップデート
| アップデート名 | 種別 | 完了日 | native-realへの影響 |
|---|---|---|---|
| {名前} | コアアップデート | {日付} | 影響なし / 要修正: {スキル名} |

### スキル修正サマリー
- {スキル名}: {修正内容}
（修正なしの場合は「全スキル現在の公式ガイドラインと整合しています」）

### 次回確認推奨時期
{日付}（コアアップデートは年3〜4回程度のペース）
```

---

## 呼び出しタイミング

- **定期実行**: 月1回（native-real-bucho が管理）
- **随時呼び出し**: 「Googleのアップデートを確認して」「ガイドラインが変わった？」
- **パイプライン組み込み**: native-real-seo-pipeline の Step 0 前に月1回実行（bucho 判断）
