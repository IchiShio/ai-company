---
name: native-real-seo-pipeline
model: claude-opus-4-6
description: |
  native-real.com の週次SEOパイプラインスキル。
  データ収集 → 分析 → 実行 の3ステップを自動で連続実行する。

  次のような依頼で必ず使用すること：
  - 「SEOパイプラインを実行して」「週次SEOをやって」
  - 「データ収集から実行まで全部やって」
  - 「native-real の週次ルーティンをやって」
  - 「SEO一連の流れをやって」
---

# native-real.com 週次SEOパイプライン

`native-real-data-collector` → `native-real-seo-analyzer` → `native-real-seo-executor`
の3スキルをこの順番で実行する。各スキルの詳細手順はそれぞれのスキル定義に従う。

---

## Step 1: データ収集

`native-real-data-collector` スキルの手順を全て実行する。
Ahrefs MCP の4ツールは並列で実行すること（依存関係なし）。

完了したら「✅ Step 1 完了 → Step 2 へ」と表示して次へ進む。

---

## Step 2: SEO分析

`native-real-seo-analyzer` スキルの手順を全て実行する。

分析結果を以下のパスに `seo_report.md` として保存してから次へ進む:
```
~/マイドライブ/02_AI・ブログ・仕事/GoogleG4,SearchConsole/YYYY-MM-DD/seo_report.md
```

完了したら「✅ Step 2 完了 → Step 3 へ」と表示して次へ進む。

---

## Step 3: SEO実行

`native-real-seo-executor` スキルの手順を全て実行する。
**ユーザーへの確認は不要。Top 5 アクションを全件自動実行して git push まで完了させる。**

---

## エラーハンドリング

| ケース | 対処 |
|---|---|
| Step 1 でブラウザ操作失敗（SC/GA4） | 継続（Ahrefsデータのみで分析） |
| Step 1 で全データ取得失敗 | ユーザーに報告して終了 |
| Step 2 で必須CSV（queries/pages）なし | Ahrefsデータのみで分析を試みる。不可ならユーザーに報告 |
