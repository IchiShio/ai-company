#!/usr/bin/env python3
import os
import subprocess
import re

repo_root = os.path.expanduser("~/projects/claude/native-real")
fixed = 0

for dirpath, _, files in os.walk(repo_root):
    for fname in files:
        if fname != "index.html":
            continue
        fpath = os.path.join(dirpath, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        if '"%Y->-"' not in content:
            continue
        # Get last modified date from git log
        rel = os.path.relpath(fpath, repo_root)
        result = subprocess.run(
            ["git", "log", "-1", "--format=%Y-%m-%d", "--", rel],
            capture_output=True, text=True, cwd=repo_root
        )
        date = result.stdout.strip() or "2026-01-01"
        new_content = content.replace('"%Y->-"', f'"{date}"')
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        fixed += 1

print(f"Fixed: {fixed} files")
