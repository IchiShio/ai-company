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

TOTAL_HTML=$(find "$REPO_ROOT" -name "index.html" -not -path "*/.git/*" | wc -l)
echo "検査対象HTMLファイル数: $TOTAL_HTML"
echo ""

# --- Check 1: global-design.css の <link> がないHTML ---
echo "--- Check 1: global-design.css 未参照ページ ---"
MISSING_CSS=$(grep -rL 'global-design\.css' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' || true)
MISSING_CSS_COUNT=$(echo "$MISSING_CSS" | grep -c '.' 2>/dev/null || echo 0)
if [ "$MISSING_CSS_COUNT" -gt 0 ]; then
  echo "⚠️  $MISSING_CSS_COUNT 件のファイルに global-design.css の参照なし:"
  echo "$MISSING_CSS" | head -30
  [ "$MISSING_CSS_COUNT" -gt 30 ] && echo "  ... 他 $((MISSING_CSS_COUNT - 30)) 件"
else
  echo "✅ 全ページに global-design.css の参照あり"
fi
echo ""

# --- Check 2: ページ背景に #FFFFFF / #fff ---
echo "--- Check 2: 純白背景 #FFFFFF / #fff 混入 ---"
WHITE_BG=$(grep -rl '#[Ff][Ff][Ff][Ff][Ff][Ff]\|background.*#[Ff][Ff][Ff]\b' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' || true)
WHITE_BG_COUNT=$(echo "$WHITE_BG" | grep -c '.' 2>/dev/null || echo 0)
if [ "$WHITE_BG_COUNT" -gt 0 ]; then
  echo "⚠️  $WHITE_BG_COUNT 件のファイルに #FFFFFF / #fff が含まれる:"
  echo "$WHITE_BG" | head -30
  [ "$WHITE_BG_COUNT" -gt 30 ] && echo "  ... 他 $((WHITE_BG_COUNT - 30)) 件"
else
  echo "✅ 純白背景の混入なし"
fi
echo ""

# --- Check 3: rgba(0,0,0,...) 使用 ---
echo "--- Check 3: rgba(0,0,0,...) 混入（テキスト色違反） ---"
BLACK_RGBA=$(grep -rl 'rgba(0,0,0,' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' || true)
BLACK_RGBA_COUNT=$(echo "$BLACK_RGBA" | grep -c '.' 2>/dev/null || echo 0)
if [ "$BLACK_RGBA_COUNT" -gt 0 ]; then
  echo "⚠️  $BLACK_RGBA_COUNT 件のファイルに rgba(0,0,0,...) が含まれる:"
  echo "$BLACK_RGBA" | head -30
  [ "$BLACK_RGBA_COUNT" -gt 30 ] && echo "  ... 他 $((BLACK_RGBA_COUNT - 30)) 件"
else
  echo "✅ rgba(0,0,0,...) の混入なし"
fi
echo ""

# --- Check 4: ヘッダー背景 rgba(248,246,241,0.92) ---
echo "--- Check 4: ヘッダー背景 rgba(248,246,241,0.92) 未適用 ---"
# ヘッダーを含むページのうち、正しい背景色がないものを検出
HEADER_FILES=$(grep -rl '<header' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' || true)
HEADER_COUNT=$(echo "$HEADER_FILES" | grep -c '.' 2>/dev/null || echo 0)
if [ "$HEADER_COUNT" -gt 0 ]; then
  BAD_HEADER=$(echo "$HEADER_FILES" | while read -r f; do
    grep -qL 'rgba(248,246,241' "$f" 2>/dev/null && echo "$f"
  done || true)
  BAD_HEADER_COUNT=$(echo "$BAD_HEADER" | grep -c '.' 2>/dev/null || echo 0)
  echo "ヘッダーを含むページ: $HEADER_COUNT 件"
  if [ "$BAD_HEADER_COUNT" -gt 0 ]; then
    echo "⚠️  $BAD_HEADER_COUNT 件でヘッダー背景色が未設定/非準拠:"
    echo "$BAD_HEADER" | head -20
    [ "$BAD_HEADER_COUNT" -gt 20 ] && echo "  ... 他 $((BAD_HEADER_COUNT - 20)) 件"
  else
    echo "✅ 全ヘッダーの背景色が準拠"
  fi
else
  echo "ℹ️  <header> タグを含むページなし（global-design.css で一括適用の可能性）"
fi
echo ""

# --- Check 5: ハードコード色値（インラインstyle内） ---
echo "--- Check 5: インラインstyleのハードコード色値 ---"
HARDCODED=$(grep -rl 'style=.*\(background\|color\).*#[0-9a-fA-F]\{3,6\}' --include="*.html" "$REPO_ROOT" 2>/dev/null | grep -v '.git/' || true)
HARDCODED_COUNT=$(echo "$HARDCODED" | grep -c '.' 2>/dev/null || echo 0)
if [ "$HARDCODED_COUNT" -gt 0 ]; then
  echo "ℹ️  $HARDCODED_COUNT 件のファイルにインラインstyleのハードコード色値あり（要目視確認）:"
  echo "$HARDCODED" | head -20
  [ "$HARDCODED_COUNT" -gt 20 ] && echo "  ... 他 $((HARDCODED_COUNT - 20)) 件"
else
  echo "✅ インラインstyleのハードコード色値なし"
fi
echo ""

# --- サマリー ---
echo "=========================================="
echo "サマリー"
echo "=========================================="
echo "検査対象: $TOTAL_HTML ファイル"
echo "Check 1 (global-design.css参照): ${MISSING_CSS_COUNT:-0} 件の違反"
echo "Check 2 (純白 #FFFFFF):          ${WHITE_BG_COUNT:-0} 件の違反"
echo "Check 3 (rgba(0,0,0,...)):        ${BLACK_RGBA_COUNT:-0} 件の違反"
echo "Check 4 (ヘッダー背景):          確認要"
echo "Check 5 (ハードコード色値):      ${HARDCODED_COUNT:-0} 件（要目視）"
echo ""
echo "違反ファイルの修正は executor に指示してください。"
