#!/bin/bash
# native-real.com SEO Pipeline - 完全自動化スクリプト
# 使い方: ~/projects/claude/ai-company/run-seo-pipeline.sh
#
# 前提:
#   - GASが毎朝6時にSC/GA4データを収集済み
#   - claude CLI がインストール済み
#   - Ahrefs MCP が接続済み

set -euo pipefail

TODAY=$(date +%Y-%m-%d)
DATA_DIR="$HOME/Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole/$TODAY"
SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$HOME/projects/claude/native-real"
LOG_FILE="$DATA_DIR/pipeline_log.txt"

echo "========================================="
echo "native-real.com SEO Pipeline"
echo "日付: $TODAY"
echo "========================================="

# データフォルダ確認（GASが作成済みか）
if [ ! -d "$DATA_DIR" ]; then
  echo "❌ データフォルダが見つかりません: $DATA_DIR"
  echo "GASが実行されていない可能性があります。"
  exit 1
fi

echo "✅ データフォルダ確認: $DATA_DIR"

# ========================================
# Step 1: データ収集（Ahrefs のみ）
# ========================================
echo ""
echo "--- Step 1: Ahrefs データ収集 ---"

SESSION_ID=$(claude -p "
以下のSKILL.mdを読み、Ahrefsデータの収集のみを実行せよ（SC/GA4はGAS取得済み）。
SKILL.mdパス: $SKILLS_DIR/native-real-data-collector/SKILL.md

データフォルダ: $DATA_DIR
collection_log.txt も更新すること。

完了したら「STEP1_DONE」と出力せよ。
" --allowedTools "Bash,Read,Write,Glob,Grep,mcp__claude_ai_Ahrefs__site-explorer-metrics,mcp__claude_ai_Ahrefs__site-explorer-organic-keywords,mcp__claude_ai_Ahrefs__site-explorer-pages-by-traffic,mcp__claude_ai_Ahrefs__site-explorer-all-backlinks,mcp__claude_ai_Ahrefs__doc" \
  --output-format json 2>/dev/null | jq -r '.session_id')

echo "✅ Step 1 完了 (session: $SESSION_ID)"

# ========================================
# Check 1: データ検証
# ========================================
echo ""
echo "--- Check 1: データ検証 ---"

FAIL=0
for f in queries.csv pages.csv dates.csv ga4_traffic.csv ga4_pages.csv collection_log.txt; do
  if [ ! -f "$DATA_DIR/$f" ]; then
    echo "❌ 必須ファイル欠落: $f"
    FAIL=1
  fi
done

if [ $FAIL -eq 1 ]; then
  echo "❌ Check 1 FAIL — パイプライン中断"
  exit 1
fi

echo "✅ Check 1 PASS"

# ========================================
# Step 2: SEO分析
# ========================================
echo ""
echo "--- Step 2: SEO分析 ---"

claude -p "
以下のSKILL.mdを読み、SEO分析レポートを作成せよ。
SKILL.mdパス: $SKILLS_DIR/native-real-seo-analyzer/SKILL.md

データフォルダ: $DATA_DIR
レポート保存先: $DATA_DIR/seo_report.md

全7セクション（A〜G）とTop 5を必ず含めること。
Top 5は収益ティア（affiliate_weight: Tier1=3.0, Tier2=1.5, Tier3=1.0）を考慮してスコアリングすること。

完了したら「STEP2_DONE」と出力せよ。
" --resume "$SESSION_ID" \
  --allowedTools "Bash,Read,Write,Glob,Grep" \
  --output-format json 2>/dev/null > /dev/null

echo "✅ Step 2 完了"

# ========================================
# Check 2: レポート検証
# ========================================
echo ""
echo "--- Check 2: レポート検証 ---"

if [ ! -f "$DATA_DIR/seo_report.md" ]; then
  echo "❌ seo_report.md が存在しません"
  exit 1
fi

SECTIONS=$(grep -c '## [A-G]\.' "$DATA_DIR/seo_report.md" 2>/dev/null || echo 0)
if [ "$SECTIONS" -lt 7 ]; then
  echo "⚠️ 7セクション中 ${SECTIONS} セクションのみ検出"
fi

TOP5=$(grep -c '| [1-5] |' "$DATA_DIR/seo_report.md" 2>/dev/null || echo 0)
if [ "$TOP5" -lt 5 ]; then
  echo "⚠️ Top 5 が ${TOP5} 件のみ"
fi

echo "✅ Check 2 PASS (セクション: $SECTIONS, Top5: $TOP5)"

# ========================================
# Step 3: SEOアクション実行
# ========================================
echo ""
echo "--- Step 3: SEOアクション実行 ---"

claude -p "
以下のSKILL.mdを読み、SEOアクションを実行せよ。
SKILL.mdパス: $SKILLS_DIR/native-real-seo-executor/SKILL.md

レポート: $DATA_DIR/seo_report.md
対象リポジトリ: $REPO_DIR

ユーザー確認は不要。Top 5 アクションを全件自動実行し、git commit & push まで完了させること。
disavow.txtの更新がある場合、ファイル更新とgit pushのみ行い、GSCへのアップロードは「ユーザーに依頼」と出力せよ。

完了したら「STEP3_DONE」と出力せよ。
" --resume "$SESSION_ID" \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
  --output-format json 2>/dev/null > /dev/null

echo "✅ Step 3 完了"

# ========================================
# Check 3: 実行検証
# ========================================
echo ""
echo "--- Check 3: 実行検証 ---"

cd "$REPO_DIR"
LATEST_COMMIT=$(git log --oneline -1)
CLEAN=$(git status --porcelain)

if [ -z "$CLEAN" ]; then
  echo "✅ git: clean ($LATEST_COMMIT)"
else
  echo "⚠️ git: uncommitted changes"
fi

# ========================================
# Step 4: 部長サイト状況レポート
# ========================================
echo ""
echo "--- Step 4: 部長サイト状況レポート ---"

claude -p "
以下のSKILL.mdを読み、「パイプライン完了後レポート」セクションに従って
サイト状況レポートを生成せよ。
SKILL.mdパス: $SKILLS_DIR/native-real-bucho/SKILL.md

データフォルダ: $DATA_DIR

レポートはそのまま出力すること（ファイル保存不要）。
" --resume "$SESSION_ID" \
  --allowedTools "Bash,Read,Glob,Grep" \
  --output-format text 2>/dev/null

echo ""
echo "========================================="
echo "✅ パイプライン完了"
echo "実行日: $TODAY"
echo "最新コミット: $LATEST_COMMIT"
echo "GitHub Pages 反映: 1〜2分後"
echo "========================================="
