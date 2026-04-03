#!/usr/bin/env python3
"""投稿成功後にschedule.jsonのpostedフラグをtrueに更新し、tweet_idとposted_atを保存する。"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

now_jst = datetime.now(JST)
current_hour = now_jst.hour
current_date = now_jst.strftime("%Y-%m-%d")
posted_at = now_jst.isoformat()

if current_hour < 12:
    slot = "morning"
elif current_hour < 18:
    slot = "noon"
elif current_hour < 20:
    slot = "evening"
else:
    slot = "night"

tweet_id = os.environ.get("TWEET_ID", "").strip()

schedule_path = os.path.join(
    os.path.dirname(__file__), "..", "x-knowledge", "posts", "schedule.json"
)
schedule_path = os.path.normpath(schedule_path)

if not os.path.exists(schedule_path):
    print(f"::warning::schedule.json not found", file=sys.stderr)
    sys.exit(0)

with open(schedule_path) as f:
    schedule = json.load(f)

updated = False
for entry in schedule:
    if entry["date"] == current_date and entry["slot"] == slot and not entry.get("posted"):
        entry["posted"] = True
        entry["posted_at"] = posted_at
        if tweet_id:
            entry["tweet_id"] = tweet_id
        updated = True
        print(f"Marked {current_date} {slot} as posted (tweet_id={tweet_id or 'N/A'})", file=sys.stderr)
        break

if updated:
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"schedule.json updated")
else:
    print(f"No matching entry to mark for {current_date} {slot}", file=sys.stderr)
