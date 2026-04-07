#!/bin/bash
# native-real デザインシステム準拠チェックスクリプト
# 実行方法: cd ~/projects/claude/native-real && bash ~/projects/claude/ai-company/scripts/design-system-audit.sh

set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
echo "=========================================="
echo "デザインシステム準拠チェック"
echo "対象: $REPO_ROOT"
echo "=========================================="
echo ""

# node_modules を除外した HTML ファイル一覧
TOTAL_HTML=$(find "$REPO_ROOT" -name "index.html" -not -path "*/.git/*" -not -path "*/node_modules/*" | wc -l)
echo "検査対象HTMLファイル数（node_modules除く）: $TOTAL_HTML"
echo ""

# --- Check 1: global-design.css の <link> がないHTML ---
echo "--- Check 1: global-design.css 未参照ページ ---"
MISSING_CSS=$(grep -rL 'global-design\.css' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules' || true)
MISSING_CSS_COUNT=$(echo "$MISSING_CSS" | grep -c '.' 2>/dev/null || echo 0)
if [ "$MISSING_CSS_COUNT" -gt 0 ]; then
  echo "⚠️  $MISSING_CSS_COUNT 件のファイルに global-design.css の参照なし:"
  echo "$MISSING_CSS" | head -30
  [ "$MISSING_CSS_COUNT" -gt 30 ] && echo "  ... 他 $((MISSING_CSS_COUNT - 30)) 件"
else
  echo "✅ 全ページに global-design.css の参照あり"
fi
echo ""

# --- Check 2: 実際の背景色に #FFFFFF / #fff を使用 ---
# 誤検出除外: color:#fff（白テキスト）, rgba(255,255,255,...) は対象外
# 対象: background:\s*#fff, background-color:\s*#fff, --bg:#fff など
echo "--- Check 2: 純白背景 #FFFFFF / #fff 混入（background指定のみ対象） ---"
WHITE_BG=$(grep -rn 'background:\s*#[Ff][Ff][Ff]\b\|background-color:\s*#[Ff][Ff][Ff]\b\|background:\s*#[Ff][Ff][Ff][Ff][Ff][Ff]\b\|background-color:\s*#[Ff][Ff][Ff][Ff][Ff][Ff]\b\|--bg:\s*#[Ff][Ff][Ff]\b\|--bg:\s*#[Ff][Ff][Ff][Ff][Ff][Ff]\b' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules' | grep -v 'background.*linear-gradient\|background.*url(' || true)
WHITE_BG_COUNT=$(echo "$WHITE_BG" | grep -c '.' 2>/dev/null || echo 0)
if [ "$WHITE_BG_COUNT" -gt 0 ]; then
  echo "⚠️  $WHITE_BG_COUNT 件の違反（白背景の直接指定）:"
  echo "$WHITE_BG" | head -30
  [ "$WHITE_BG_COUNT" -gt 30 ] && echo "  ... 他 $((WHITE_BG_COUNT - 30)) 件"
else
  echo "✅ 純白背景の混入なし"
fi
echo ""

# --- Check 3: rgba(0,0,0,...) 使用 ---
echo "--- Check 3: rgba(0,0,0,...) 混入（rgba(26,26,26,...) を使うこと） ---"
BLACK_RGBA=$(grep -rl 'rgba(0,0,0,' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules' || true)
BLACK_RGBA_COUNT=$(echo "$BLACK_RGBA" | grep -c '.' 2>/dev/null || echo 0)
if [ "$BLACK_RGBA_COUNT" -gt 0 ]; then
  echo "⚠️  $BLACK_RGBA_COUNT 件のファイルに rgba(0,0,0,...) が含まれる:"
  echo "$BLACK_RGBA" | head -30
  [ "$BLACK_RGBA_COUNT" -gt 30 ] && echo "  ... 他 $((BLACK_RGBA_COUNT - 30)) 件"
else
  echo "✅ rgba(0,0,0,...) の混入なし"
fi
echo ""

# --- Check 4: ヘッダー背景（global-design.css で一括管理済みのため参考情報）---
echo "--- Check 4: ヘッダー背景（global-design.css !important で一括適用済み・参考値） ---"
HEADER_FILES=$(grep -rl '<header' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules' || true)
HEADER_COUNT=$(echo "$HEADER_FILES" | grep -c '.' 2>/dev/null || echo 0)
echo "ℹ️  <header> を含むページ: $HEADER_COUNT 件（global-design.css で全て上書き済み）"
echo ""

# --- Check 5: インラインstyle の純白背景ハードコード ---
echo "--- Check 5: インラインstyle の純白背景 ---"
INLINE_WHITE=$(grep -rn 'style="[^"]*background:\s*#fff\b\|style="[^"]*background:\s*#ffffff\b\|style="[^"]*background:\s*#FFF\b\|style="[^"]*background:\s*#FFFFFF\b' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules' || true)
INLINE_WHITE_COUNT=$(echo "$INLINE_WHITE" | grep -c '.' 2>/dev/null || echo 0)
if [ "$INLINE_WHITE_COUNT" -gt 0 ]; then
  echo "⚠️  $INLINE_WHITE_COUNT 件のインライン純白背景:"
  echo "$INLINE_WHITE" | head -20
  [ "$INLINE_WHITE_COUNT" -gt 20 ] && echo "  ... 他 $((INLINE_WHITE_COUNT - 20)) 件"
else
  echo "✅ インラインstyle の純白背景なし"
fi
echo ""

# --- サマリー ---
echo "=========================================="
echo "サマリー"
echo "=========================================="
echo "検査対象: $TOTAL_HTML ファイル（node_modules除く）"
echo "Check 1 (global-design.css参照): ${MISSING_CSS_COUNT:-0} 件の違反"
echo "Check 2 (純白 background指定):   ${WHITE_BG_COUNT:-0} 件の違反"
echo "Check 3 (rgba(0,0,0,...)):        ${BLACK_RGBA_COUNT:-0} 件の違反"
echo "Check 4 (ヘッダー):              global-design.css で一括管理"
echo "Check 5 (インライン純白):        ${INLINE_WHITE_COUNT:-0} 件の違反"
echo ""
echo "違反ファイルの修正は executor に指示してください。"
