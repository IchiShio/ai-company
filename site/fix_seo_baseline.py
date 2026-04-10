#!/usr/bin/env python3
"""
fix_seo_baseline.py
Bulk-fix two critical SEO issues across all HTML files:
1. Add og:image if missing
2. Add datePublished / dateModified to JSON-LD if missing
"""

import glob
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OG_IMAGE_TAG = '  <meta property="og:image" content="https://native-real.com/assets/ogp.png">'

DIRS = ["articles", "real-phrases", "services"]


def find_html_files():
    files = []
    for d in DIRS:
        pattern = os.path.join(REPO_ROOT, d, "*", "index.html")
        files.extend(sorted(glob.glob(pattern)))
    return files


def git_date_first_commit(filepath):
    """Get the date of the first commit that added this file."""
    rel = os.path.relpath(filepath, REPO_ROOT)
    # Try --diff-filter=A first (file addition)
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%Y-%m-%d", "--", rel],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    date = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else ""
    if not date:
        # Fallback: earliest commit
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%Y-%m-%d", "--", rel],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        lines = result.stdout.strip().split("\n")
        date = lines[0] if lines and lines[0] else ""
    return date


def git_date_last_commit(filepath):
    """Get the date of the most recent commit touching this file."""
    rel = os.path.relpath(filepath, REPO_ROOT)
    result = subprocess.run(
        ["git", "log", "-1", "--format=%Y-%m-%d", "--", rel],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    return result.stdout.strip()


def add_og_image(content):
    """Add og:image after the last og: meta tag if missing. Returns (new_content, changed)."""
    if 'og:image' in content:
        return content, False

    # Find all og: meta tag positions
    og_pattern = re.compile(r'^(  <meta property="og:[^"]*"[^>]*>)', re.MULTILINE)
    matches = list(og_pattern.finditer(content))
    if not matches:
        return content, False

    last_match = matches[-1]
    insert_pos = last_match.end()
    new_content = content[:insert_pos] + "\n" + OG_IMAGE_TAG + content[insert_pos:]
    return new_content, True


def add_dates_to_jsonld(content, filepath):
    """Add datePublished and/or dateModified to JSON-LD Article block if missing.
    Returns (new_content, added_published, added_modified)."""
    added_published = False
    added_modified = False

    if 'application/ld+json' not in content:
        return content, False, False

    # Find all JSON-LD blocks
    jsonld_pattern = re.compile(
        r'(<script type="application/ld\+json">)\s*(\{.*?\})\s*(</script>)',
        re.DOTALL
    )

    def process_block(match):
        nonlocal added_published, added_modified
        open_tag = match.group(1)
        json_str = match.group(2)
        close_tag = match.group(3)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return match.group(0)

        # Only process Article type
        if data.get("@type") != "Article":
            return match.group(0)

        changed = False

        if "datePublished" not in data:
            date_pub = git_date_first_commit(filepath)
            if date_pub:
                data["datePublished"] = date_pub
                added_published = True
                changed = True

        if "dateModified" not in data:
            date_mod = git_date_last_commit(filepath)
            if date_mod:
                data["dateModified"] = date_mod
                added_modified = True
                changed = True

        if not changed:
            return match.group(0)

        # Rebuild JSON-LD preserving key order with datePublished/dateModified
        # placed after description (or at a logical position)
        ordered = {}
        for key in data:
            ordered[key] = data[key]
            if key == "datePublished" and "dateModified" in data:
                # Ensure dateModified comes right after datePublished
                pass

        new_json = json.dumps(data, ensure_ascii=False, indent=2)
        return f"{open_tag}\n{new_json}\n{close_tag}"

    new_content = jsonld_pattern.sub(process_block, content)
    return new_content, added_published, added_modified


def main():
    files = find_html_files()
    print(f"Found {len(files)} HTML files to process\n")

    total_modified = 0
    total_og_added = 0
    total_published_added = 0
    total_modified_added = 0

    for filepath in files:
        rel = os.path.relpath(filepath, REPO_ROOT)
        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        content = original
        file_changed = False

        # 1. Add og:image if missing
        content, og_changed = add_og_image(content)
        if og_changed:
            file_changed = True
            total_og_added += 1

        # 2-3. Add datePublished / dateModified to JSON-LD
        content, pub_added, mod_added = add_dates_to_jsonld(content, filepath)
        if pub_added:
            file_changed = True
            total_published_added += 1
        if mod_added:
            file_changed = True
            total_modified_added += 1

        if file_changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            total_modified += 1
            changes = []
            if og_changed:
                changes.append("og:image")
            if pub_added:
                changes.append("datePublished")
            if mod_added:
                changes.append("dateModified")
            print(f"  FIXED: {rel} [{', '.join(changes)}]")

    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Files scanned:        {len(files)}")
    print(f"  Files modified:       {total_modified}")
    print(f"  og:image added:       {total_og_added}")
    print(f"  datePublished added:  {total_published_added}")
    print(f"  dateModified added:   {total_modified_added}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
