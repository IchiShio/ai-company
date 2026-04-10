#!/bin/bash
# NR-AutoAuditor cron wrapper
#
# cron 設定例:
#   0 3 * * * ~/native-real/nr-autoauditor/cron_audit.sh >> ~/nr-autoauditor.log 2>&1
#
# 動作:
#   - 毎日: 新規追加された問題のみ監査 + 修正 + デプロイ
#   - 3日ごと（日付 % 3 == 0）: 全問フル監査 + 修正 + デプロイ

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/.venv"
LOG_PREFIX="$(date '+%Y-%m-%d %H:%M:%S')"

echo "[$LOG_PREFIX] NR-AutoAuditor cron 開始"

# venv 有効化
source "$VENV_DIR/bin/activate"

# リポジトリを最新に（新問題を取得）
cd "$REPO_DIR"
git pull origin main --quiet 2>/dev/null || true

cd "$SCRIPT_DIR"

# 3日ごとに全問監査、それ以外は新規のみ
DAY_OF_YEAR=$(date '+%j' | sed 's/^0*//')
if [ $((DAY_OF_YEAR % 3)) -eq 0 ]; then
    echo "[$LOG_PREFIX] 全問フル監査（3日周期）"
    python3 main.py --auto-fix --auto-push
else
    echo "[$LOG_PREFIX] 新規問題のみ監査"
    python3 main.py --new-only --auto-fix --auto-push
fi

echo "[$LOG_PREFIX] NR-AutoAuditor cron 完了"
