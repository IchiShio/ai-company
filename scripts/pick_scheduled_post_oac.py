#!/usr/bin/env python3
"""oac用: スケジュールされた投稿からJST現在時刻に合う投稿を選ぶ。"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "")

manual = os.environ.get("MANUAL_TEXT", "").strip()
if manual:
    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a") as fh:
            fh.write(f"post_text<<EOF\n{manual}\nEOF\n")
    else:
        print(f"post_text={manual}")
    sys.exit(0)

now_jst = datetime.now(JST)
current_hour = now_jst.hour
current_date = now_jst.strftime("%Y-%m-%d")

schedule_path = os.path.join(
    os.path.dirname(__file__), "..", "oac-knowledge", "posts", "schedule.json"
)
schedule_path = os.path.normpath(schedule_path)

if not os.path.exists(schedule_path):
    print("post_text=")
    print(f"::warning::schedule.json not found at {schedule_path}", file=sys.stderr)
    sys.exit(0)

with open(schedule_path) as f:
    schedule = json.load(f)

slot = "morning" if current_hour < 12 else "evening"

for entry in schedule:
    if entry["date"] == current_date and entry["slot"] == slot and not entry.get("posted"):
        text = entry["text"]
        if GITHUB_OUTPUT:
            with open(GITHUB_OUTPUT, "a") as fh:
                fh.write(f"post_text<<EOF\n{text}\nEOF\n")
        else:
            print(f"post_text={text}")
        sys.exit(0)

print("post_text=")
print(f"::notice::No scheduled post for {current_date} {slot}", file=sys.stderr)
