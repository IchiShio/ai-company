---
name: native-real-seo-pipeline
model: claude-opus-4-6
description: |
  native-real.com の週次SEOパイプラインスキル。
  データ収集 → 分析 → 実行 の3ステップを自動で連続実行し、
  各ステップ後に native-real-seo-checker で品質検査を行う。

  次のような依頼で必ず使用すること：
  - 「SEOパイプラインを実行して」「週次SEOをやって」
  - 「データ収集から実行まで全部やって」
  - 「native-real の週次ルーティンをやって」
  - 「SEO一連の流れをやって」
---

# native-real.com 週次SEOパイプライン

各スキルをこの順番で実行し、ステップごとに `native-real-seo-checker` で品質検査する。
❌ FAIL が出たら**即中断**してユーザーに報告する。

---

## Step 1: データ収集

`native-real-data-collector` スキルの手順を全て実行する。
Ahrefs MCP の4ツールは並列で実行すること（依存関係なし）。

### Check 1
`native-real-seo-checker` の **Check 1** を実行する。
- ✅ PASS → Step 2 へ進む
- ⚠️ WARNING → 警告を表示して Step 2 へ進む
- ❌ FAIL → **パイプライン中断**・ユーザーに報告

---

## Step 2: SEO分析

`native-real-seo-analyzer` スキルの手順を全て実行する。

分析結果を以下のパスに `seo_report.md` として保存する:
```
~/マイドライブ/02_AI・ブログ・仕事/GoogleG4,SearchConsole/YYYY-MM-DD/seo_report.md
```

### Check 2
`native-real-seo-checker` の **Check 2** を実行する。
- ✅ PASS → Step 3 へ進む
- ⚠️ WARNING → 警告を表示して Step 3 へ進む
- ❌ FAIL → **パイプライン中断**・ユーザーに報告

---

## Step 3: SEO実行

`native-real-seo-executor` スキルの手順を全て実行する。
**ユーザーへの確認は不要。Top 5 アクションを全件自動実行して git push まで完了させる。**

### Check 3
`native-real-seo-checker` の **Check 3** を実行する。
- ✅ PASS → 完了レポートを表示
- ⚠️ WARNING → 警告つきで完了レポートを表示
- ❌ FAIL → **パイプライン中断**・ユーザーに報告

---

## 完了レポート

全 Check が PASS/WARNING で通過した場合、以下の形式で報告する:

```
✅ パイプライン完了

実行日: YYYY-MM-DD
実行アクション:
  1. /real-phrases/xxx/ コンテンツリライト（3,200文字）
  2. /articles/xxx/ タイトル改善
  ...

Check 結果:
  Check 1 (collector): ✅ PASS
  Check 2 (analyzer):  ✅ PASS
  Check 3 (executor):  ✅ PASS

GitHub Pages 反映: 1〜2分後
```

---

## エラーハンドリング

| ケース | 対処 |
|---|---|
| Step 1 でブラウザ操作失敗（SC/GA4） | GASで取得済みのCSVがあれば継続、なければ FAIL |
| Step 1 で全データ取得失敗 | Check 1 が FAIL → 中断 |
| Step 2 で必須CSV（queries/pages）なし | Ahrefsデータのみで分析を試みる |
| Check で FAIL | 即中断・ユーザーに問題箇所と対処を報告 |
