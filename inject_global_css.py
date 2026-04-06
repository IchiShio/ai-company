#!/usr/bin/env python3
"""
inject_global_css.py
Injects <link rel="stylesheet" href="/assets/global-design.css"> before </head>
in every HTML file under the native-real repo, skipping files that already have it.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LINK_TAG = '<link rel="stylesheet" href="/assets/global-design.css">'
SKIP_PATHS = {
    os.path.join(ROOT, "assets", "global-design.css"),
}

def process(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Already injected?
    if "global-design.css" in content:
        return False

    # Inject just before </head>
    new_content, n = re.subn(
        r"(</head>)",
        LINK_TAG + "\n\\1",
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    if n == 0:
        print(f"  SKIP (no </head>): {path}")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


updated = 0
skipped = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip hidden dirs and node_modules
    dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
    for fname in filenames:
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(dirpath, fname)
        if fpath in SKIP_PATHS:
            continue
        if process(fpath):
            updated += 1
        else:
            skipped += 1

print(f"\nDone: {updated} files updated, {skipped} files skipped.")
