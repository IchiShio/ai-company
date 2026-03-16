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

## Step 0: テクニカルSEOベースラインチェック

**実行タイミング**: パイプライン開始時（月1回、または新規ページ追加時）

Step 1 の前に、サイト全体のテクニカルSEOベースラインを検査する。
**Check 0 を自分で直接実行する**（Agent不要）:

### Check 0（直接実行）

`~/projects/claude/native-real/` 内の全 index.html ファイルを検査する:
- `articles/*/index.html`
- `real-phrases/*/index.html`
- `services/*/index.html`
- `index.html`（トップページ）

各ページで以下を確認する:

**メタタグ検査**:
1. `<title>` が60文字以内か
2. `<meta name="description">` が70〜120文字か
3. `<meta name="author">` が存在するか
4. `<meta property="og:title">` が存在するか
5. `<meta property="og:description">` が存在するか
6. `<meta property="og:image">` が存在するか
7. `<meta property="og:url">` が存在するか
8. `<meta property="og:type">` が存在するか
9. `<meta property="og:locale">` が `ja_JP` であるか
10. `<meta name="twitter:card">` が存在するか
11. `<meta name="twitter:title">` が存在するか
12. `<meta name="twitter:description">` が存在するか

**構造化データ検査**:
1. JSON-LDに `datePublished` が含まれるか
2. JSON-LDに `dateModified` が含まれるか
3. JSON-LDに `author` (`"@type": "Person"`) が含まれるか
4. `articles/*/` と `services/*/` に FAQPage スキーマがあるか（推奨）

**判定**:
- ⚠️ WARNING → 欠落リストを表示し、Step 1 へ進む（パイプラインは止めない）
  - WARNING の場合、Step 3 の executor に修正リストを追加で渡し、Top 5 アクションに加えてベースライン修正も実行させる
- ✅ PASS → Step 1 へ進む

---

## Step 1: データ収集

**Agent tool** で以下のサブエージェントを生成する:

```
description: "SEO data collection"
prompt: |
  以下のSKILL.mdを読み、その指示に従ってデータ収集を実行せよ。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-data-collector/SKILL.md

  まず ~/projects/claude/native-real/docs/site-context.md を読み込み、
  競合サイト情報（ベンチマーク競合のドメイン）を取得すること。

  SC/GA4データはGASが毎朝自動取得済み。Ahrefsデータ（自サイト+競合）を取得すること。
  データフォルダ: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/
  collection_log.txt も更新すること。
mode: bypassPermissions
```

サブエージェント完了後、**Check 1 を自分で実行する**（Agent不要、直接ファイル確認）:

### Check 1（直接実行）
以下を確認する:
1. データフォルダに必須ファイルが存在するか: queries.csv, pages.csv, dates.csv, ga4_traffic.csv, ga4_pages.csv, collection_log.txt（ahrefs_competitor_keywords.csv, ahrefs_competitors.csv は任意）
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

  まず ~/projects/claude/native-real/docs/site-context.md を読み込み、
  ビジネスコンテキスト・競合情報・ターゲットキーワードを把握すること。

  データフォルダ: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/
  レポート保存先: 同フォルダの seo_report.md

  全9セクション（A〜I）とTop 5（フェーズタグ付き）を必ず含めること。
  Top 5は収益ティア（affiliate_weight）を考慮してスコアリングすること。
mode: bypassPermissions
```

サブエージェント完了後、**Check 2 を自分で実行する**:

### Check 2（直接実行）
1. seo_report.md が存在するか
2. 9セクション（A〜I）が全て含まれるか: `## A.`, `## B.`, `## C.`, `## D.`, `## E.`, `## F.`, `## G.`, `## H.`, `## I.` を検索（H/Iはデータなしによるスキップ注記もPASS扱い）
3. Top 5 テーブルが5行あり、各行にフェーズタグが含まれるか
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
  Check 0 (baseline):  ✅/⚠️
  Check 1 (collector): ✅/⚠️
  Check 2 (analyzer):  ✅/⚠️
  Check 3 (executor):  ✅/⚠️

GitHub Pages 反映: 1〜2分後
```

### Step 4: 部長サイト状況レポート

全Checkが完了した後、**Agent tool** で部長サブエージェントを生成してサイト状況レポートを出力させる:

```
description: "SEO bucho site report"
prompt: |
  以下のSKILL.mdを読み、「パイプライン完了後レポート」セクションに従って
  サイト状況レポートを生成せよ。
  SKILL.mdパス: /Users/yusuke/.claude/skills/native-real-bucho/SKILL.md

  データフォルダ: ~/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/{今日の日付}/

  レポートはターミナルに出力すること（ファイル保存不要）。
mode: bypassPermissions
```

このレポートがパイプラインの最終出力となる。
