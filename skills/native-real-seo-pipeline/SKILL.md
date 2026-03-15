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

**部門目標: アフィリエイト収入の増加。** 検索順位改善はその手段。
Tier 1ページ（`/`・`/services/*/`）への施策を最優先とすること。

---

## 実行方法

このスキルは **Agent tool でサブエージェントを生成**して各ステップを実行する。
各サブエージェントに対応するSKILL.mdのパスを渡し、その指示に従わせる。

**共有データフォルダ**:
```
~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/YYYY-MM-DD/
```
（YYYY-MM-DD は今日の日付）

---

## Step 1: データ収集

**Agent tool** で以下のサブエージェントを生成する:

```
description: "SEO data collection"
prompt: |
  以下のSKILL.mdを読み、その指示に従ってデータ収集を実行せよ。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-data-collector/SKILL.md

  SC/GA4データはGASが毎朝自動取得済み。Ahrefsデータのみ取得すること。
  データフォルダ: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/
  collection_log.txt も更新すること。
mode: bypassPermissions
```

サブエージェント完了後、**Check 1 を自分で実行する**（Agent不要、直接ファイル確認）:

### Check 1（直接実行）
以下を確認する:
1. データフォルダに必須ファイルが存在するか: queries.csv, pages.csv, dates.csv, ga4_traffic.csv, ga4_pages.csv, collection_log.txt
2. 各ファイルの行数が最低基準を満たすか: queries≥10, pages≥5, dates≥14, ga4_traffic≥2, ga4_pages≥5
3. collection_log.txt にエラーがないか

- ✅ PASS → Step 2 へ
- ⚠️ WARNING → 警告表示して Step 2 へ
- ❌ FAIL → リカバリー1回試行 → 再FAIL → 部長エスカレーション（Agent tool で native-real-bucho の SKILL.md を渡す）

---

## Step 2: SEO分析

**Agent tool** で以下のサブエージェントを生成する:

```
description: "SEO analysis and report"
prompt: |
  以下のSKILL.mdを読み、その指示に従ってSEO分析レポートを作成せよ。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-seo-analyzer/SKILL.md

  データフォルダ: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/
  レポート保存先: 同フォルダの seo_report.md

  全7セクション（A〜G）とTop 5を必ず含めること。
  Top 5は収益ティア（affiliate_weight）を考慮してスコアリングすること。
mode: bypassPermissions
```

サブエージェント完了後、**Check 2 を自分で実行する**:

### Check 2（直接実行）
1. seo_report.md が存在するか
2. 7セクション（A〜G）が全て含まれるか: `## A.`, `## B.`, `## C.`, `## D.`, `## E.`, `## F.`, `## G.` を検索
3. Top 5 テーブルが5行あるか
4. 各アクションにページ名・変更内容・数値が含まれるか

- ✅ PASS → Step 3 へ
- ❌ FAIL → リカバリー（不足セクションの再生成を指示）→ 再FAIL → 部長エスカレーション

---

## Step 3: SEO実行

**Agent tool** で以下のサブエージェントを生成する:

```
description: "SEO action execution"
prompt: |
  以下のSKILL.mdを読み、その指示に従ってSEOアクションを実行せよ。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-seo-executor/SKILL.md

  レポート: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/seo_report.md
  対象リポジトリ: ~/projects/claude/native-real

  ユーザー確認は不要。Top 5 アクションを全件自動実行し、git commit & push まで完了させること。
mode: bypassPermissions
```

サブエージェント完了後、**Check 3 を自分で実行する**:

### Check 3（直接実行）
1. 今日のgitコミットが存在するか
2. Top 5 全件が実行されたか（変更ファイルとレポートを照合）
3. title が25〜35文字か
4. meta description が80〜130文字か
5. og:title / JSON-LD headline が更新されているか
6. git push 済みか（working tree clean）

- ✅ PASS → 完了レポート表示
- ❌ FAIL → リカバリー → 再FAIL → 部長エスカレーション

---

## 部長エスカレーション

いずれかの Check でリカバリー失敗した場合、**Agent tool** で部長サブエージェントを生成する:

```
description: "SEO bucho escalation"
prompt: |
  以下のSKILL.mdを読み、エスカレーション対応を行え。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-bucho/SKILL.md

  エスカレーション元: Check {N}
  問題: {具体的な問題内容}
  試みたリカバリー: {実施した対処内容}
  結果: 解決できなかった
mode: bypassPermissions
```

---

## 完了レポート

全 Check が PASS/WARNING で通過した場合:

```
✅ パイプライン完了

実行日: YYYY-MM-DD
実行アクション:
  1. {アクション1}
  2. {アクション2}
  ...

Check 結果:
  Check 1 (collector): ✅/⚠️
  Check 2 (analyzer):  ✅/⚠️
  Check 3 (executor):  ✅/⚠️

GitHub Pages 反映: 1〜2分後
```
