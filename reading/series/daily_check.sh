#!/bin/bash
# ReadUp 日次チェックスクリプト
# cron: 毎日 9:00 に実行
# 設定: crontab -e → 0 9 * * * /Users/yusuke/projects/claude/native-real/reading/series/daily_check.sh

set -e
cd /Users/yusuke/projects/claude/native-real

LOG=/tmp/readup_daily_check.log
echo "=== $(date '+%Y-%m-%d %H:%M') ===" > "$LOG"

# ── チェック1: 品質チェック ──────────────────────────────
echo "--- check_stories.py ---" >> "$LOG"
python3 reading/series/check_stories.py --errors-only 2>&1 >> "$LOG"
QUALITY_EXIT=$?

# ── チェック2: vocab_notes 欠けチェック ──────────────────
echo "" >> "$LOG"
echo "--- vocab_notes 欠け ---" >> "$LOG"
MISSING_COUNT=$(python3 reading/series/add_vocab_notes.py --dry-run 2>&1 | grep "vocab_note 欠け:" | grep -oE '[0-9]+')
echo "欠け: ${MISSING_COUNT:-0} 件" >> "$LOG"

# vocab_notes が欠けていれば missing_vocab.json を自動生成
if [ "${MISSING_COUNT:-0}" -gt 0 ]; then
    python3 reading/series/add_vocab_notes.py --export-missing >> "$LOG" 2>&1
fi

cat "$LOG"

# ── 通知が必要な場合 ─────────────────────────────────────
NEED_NOTIFY=0
MSG=""

if [ "$QUALITY_EXIT" -ne 0 ]; then
    MSG="${MSG}🔴 ReadUp check_stories.py でERRORが検出されました。\n"
    NEED_NOTIFY=1
fi

if [ "${MISSING_COUNT:-0}" -gt 0 ]; then
    MSG="${MSG}📝 vocab_notes 不足: ${MISSING_COUNT}件。missing_vocab.json を生成済み。\nClaude Codeで「missing_vocab.jsonを読んでvocab_notesを追加して」と依頼してください。\n"
    NEED_NOTIFY=1
fi

if [ "$NEED_NOTIFY" -eq 1 ]; then
    # macOS 通知
    osascript -e "display notification \"$(echo -e $MSG | head -c 200)\" with title \"ReadUp 日次チェック\" sound name \"Glass\""
fi
