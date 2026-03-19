#!/usr/bin/env python3
"""スケジュールされた投稿からJST現在時刻に合う投稿を選ぶ。"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

# 手動テキストが指定されていればそのまま使う
manual = os.environ.get("MANUAL_TEXT", "").strip()
if manual:
    # GitHub Actions output format
    print(f"post_text={manual}")
    sys.exit(0)

now_jst = datetime.now(JST)
current_hour = now_jst.hour
current_date = now_jst.strftime("%Y-%m-%d")

# スケジュールファイルを読む
schedule_path = os.path.join(
    os.path.dirname(__file__), "..", "x-knowledge", "posts", "schedule.json"
)
schedule_path = os.path.normpath(schedule_path)

if not os.path.exists(schedule_path):
    print("post_text=")
    print(f"::warning::schedule.json not found at {schedule_path}", file=sys.stderr)
    sys.exit(0)

with open(schedule_path) as f:
    schedule = json.load(f)

# 現在の日付+時間帯に合う投稿を探す
slot = "morning" if current_hour < 12 else "evening"

for entry in schedule:
    if entry["date"] == current_date and entry["slot"] == slot and not entry.get("posted"):
        text = entry["text"]
        # 改行をエスケープしてGitHub Actionsに渡す
        escaped = text.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
        print(f"post_text={escaped}")
        sys.exit(0)

# 該当なし
print("post_text=")
print(f"::notice::No scheduled post for {current_date} {slot}", file=sys.stderr)
