#!/usr/bin/env python3
"""
scrape_grammar_sources.py - 権威ある文法ソースから文法項目一覧を取得
requests + BeautifulSoup で取得。grammar/raw_sources/ に保存。
"""

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = Path(__file__).parent / "grammar" / "raw_sources"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
    "Referer": "https://www.google.com/",
}


def save_json(filename, data):
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  Saved: {path} ({len(data)} items)")


def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# ─────────────────────────────────────────
# 1. British Council LearnEnglish Grammar
# ─────────────────────────────────────────
def scrape_british_council():
    print("\n[1/6] British Council LearnEnglish Grammar...")
    try:
        soup = fetch("https://learnenglish.britishcouncil.org/grammar")
        items = []
        for link in soup.select("a[href*='/grammar/']"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if text and "/grammar/" in href and text.lower() != "grammar" and len(text) > 3:
                full_url = href if href.startswith("http") else f"https://learnenglish.britishcouncil.org{href}"
                items.append({"title": text, "url": full_url, "source": "British Council"})

        seen = set()
        unique = [item for item in items if item["url"] not in seen and not seen.add(item["url"])]
        save_json("british_council.json", unique)
        return unique
    except Exception as e:
        print(f"  ERROR: {e}")
        save_json("british_council.json", [{"error": str(e)}])
        return []


# ─────────────────────────────────────────
# 2. Cambridge Dictionary Grammar (may fail with Cloudflare)
# ─────────────────────────────────────────
def scrape_cambridge():
    print("\n[2/6] Cambridge Dictionary Grammar...")
    try:
        soup = fetch("https://dictionary.cambridge.org/grammar/british-grammar/")
        items = []
        for link in soup.select("a[href*='/grammar/british-grammar/']"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if text and len(text) > 2:
                full_url = href if href.startswith("http") else f"https://dictionary.cambridge.org{href}"
                items.append({"title": text, "url": full_url, "source": "Cambridge Grammar"})

        seen = set()
        unique = [item for item in items if item["url"] not in seen and not seen.add(item["url"])]
        save_json("cambridge.json", unique)
        return unique
    except Exception as e:
        print(f"  ERROR: {e}")
        save_json("cambridge.json", [{"error": str(e)}])
        return []


# ─────────────────────────────────────────
# 3. Purdue OWL Grammar
# ─────────────────────────────────────────
def scrape_purdue_owl():
    print("\n[3/6] Purdue OWL Grammar...")
    try:
        soup = fetch("https://owl.purdue.edu/owl/general_writing/grammar/")
        items = []
        for link in soup.select("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if text and "/grammar/" in href and text.lower() != "grammar" and len(text) > 3:
                full_url = href if href.startswith("http") else f"https://owl.purdue.edu{href}"
                items.append({"title": text, "url": full_url, "source": "Purdue OWL"})

        seen = set()
        unique = [item for item in items if item["url"] not in seen and not seen.add(item["url"])]
        save_json("purdue_owl.json", unique)
        return unique
    except Exception as e:
        print(f"  ERROR: {e}")
        save_json("purdue_owl.json", [{"error": str(e)}])
        return []


# ─────────────────────────────────────────
# 4. BBC Learning English Grammar
# ─────────────────────────────────────────
def scrape_bbc():
    print("\n[4/6] BBC Learning English Grammar...")
    try:
        soup = fetch("https://www.bbc.co.uk/learningenglish/english/grammar-reference")
        items = []
        for link in soup.select("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if text and len(text) > 3 and ("grammar" in href.lower() or "course/intermediate" in href.lower()):
                full_url = href if href.startswith("http") else f"https://www.bbc.co.uk{href}"
                items.append({"title": text, "url": full_url, "source": "BBC Learning English"})

        seen = set()
        unique = [item for item in items if item["url"] not in seen and not seen.add(item["url"])]
        save_json("bbc.json", unique)
        return unique
    except Exception as e:
        print(f"  ERROR: {e}")
        save_json("bbc.json", [{"error": str(e)}])
        return []


# ─────────────────────────────────────────
# 5. 英検公式 各級の情報
# ─────────────────────────────────────────
def scrape_eiken():
    print("\n[5/6] 英検公式...")
    items = []
    grades = [
        ("4級", "https://www.eiken.or.jp/eiken/exam/grade_4/"),
        ("3級", "https://www.eiken.or.jp/eiken/exam/grade_3/"),
        ("準2級", "https://www.eiken.or.jp/eiken/exam/grade_p2/"),
        ("2級", "https://www.eiken.or.jp/eiken/exam/grade_2/"),
        ("準1級", "https://www.eiken.or.jp/eiken/exam/grade_p1/"),
    ]
    for grade_name, url in grades:
        try:
            soup = fetch(url)
            main = soup.find("main") or soup.find("div", id="content") or soup.find("body")
            text = main.get_text(separator="\n", strip=True)[:3000] if main else ""
            items.append({"grade": grade_name, "url": url, "content": text, "source": "英検公式"})
            print(f"  {grade_name}: {len(text)} chars")
            time.sleep(1)
        except Exception as e:
            print(f"  {grade_name} ERROR: {e}")
            items.append({"grade": grade_name, "url": url, "error": str(e), "source": "英検公式"})

    save_json("eiken.json", items)
    return items


# ─────────────────────────────────────────
# 6. CEFR English Grammar Profile
# ─────────────────────────────────────────
def scrape_cefr():
    print("\n[6/6] CEFR English Grammar Profile...")
    try:
        soup = fetch("https://www.englishprofile.org/english-grammar-profile/egp-online")
        items = []
        for row in soup.select("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                items.append({
                    "text": " | ".join(c.get_text(strip=True) for c in cells),
                    "source": "CEFR EGP"
                })
        if not items:
            text = soup.get_text(separator="\n", strip=True)[:5000]
            items = [{"content": text, "source": "CEFR EGP"}]

        save_json("cefr.json", items)
        return items
    except Exception as e:
        print(f"  ERROR: {e}")
        save_json("cefr.json", [{"error": str(e)}])
        return []


# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Grammar Sources Scraper")
    print("=" * 50)

    results = {}
    for name, func in [
        ("british_council", scrape_british_council),
        ("cambridge", scrape_cambridge),
        ("purdue_owl", scrape_purdue_owl),
        ("bbc", scrape_bbc),
        ("eiken", scrape_eiken),
        ("cefr", scrape_cefr),
    ]:
        try:
            result = func()
            results[name] = len(result) if result else 0
        except Exception as e:
            print(f"  FAILED: {name} - {e}")
            results[name] = 0
        time.sleep(2)

    print("\n" + "=" * 50)
    print("Summary:")
    for name, count in results.items():
        status = "OK" if count > 0 else "FAILED"
        print(f"  {name}: {count} items [{status}]")
    print(f"\nFiles saved to: {OUTPUT_DIR}")
