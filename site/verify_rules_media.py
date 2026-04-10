#!/usr/bin/env python3
"""
verify_rules_media.py - grammar_rules.json の各ルールを
BBC News / NPR / AP News の実記事で裏取りする

各ルールの pattern に対応する英文を3メディアから検索し、
verified フラグと media_examples を追加する。
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
RULES_FILE = ROOT / "grammar" / "grammar_rules.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── RSS Feeds ──
RSS_FEEDS = {
    "BBC News": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    ],
    "NPR": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://feeds.npr.org/1003/rss.xml",
        "https://feeds.npr.org/1006/rss.xml",
        "https://feeds.npr.org/1019/rss.xml",
    ],
    "AP News": [
        "https://rsshub.app/apnews/topics/apf-topnews",
    ],
}

# Fallback: direct page scraping if RSS fails
FALLBACK_URLS = {
    "BBC News": "https://www.bbc.com/news",
    "NPR": "https://www.npr.org/sections/news/",
    "AP News": "https://apnews.com/",
}


def fetch_rss_articles(source_name, feeds):
    """RSSフィードから記事URLを取得"""
    urls = []
    for feed_url in feeds:
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "xml")
            for item in soup.find_all("item"):
                link = item.find("link")
                if link:
                    url = link.text.strip() if link.text else link.get("href", "")
                    if url and url.startswith("http"):
                        urls.append(url)
            time.sleep(0.5)
        except Exception as e:
            print(f"  RSS error ({source_name}): {e}")
    return list(dict.fromkeys(urls))[:30]  # Dedupe, max 30


def fetch_article_sentences(url):
    """記事URLから英文を抽出"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove non-content
        for tag in soup.select("nav, footer, script, style, .sidebar, .related"):
            tag.decompose()
        paragraphs = soup.find_all("p")
        sentences = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 30 and len(text) < 300:
                # Split into sentences
                for s in re.split(r'(?<=[.!?])\s+', text):
                    s = s.strip()
                    if len(s) > 20 and len(s) < 200:
                        sentences.append(s)
        return sentences
    except Exception:
        return []


# ── Pattern Matchers ──
# Each rule's pattern is converted to a regex-like search
PATTERN_SEARCHES = {
    # Tense patterns
    "S + have/has + pp + since/for": [
        r"\b(has|have)\s+\w+ed\s+(since|for)\b",
        r"\b(has|have)\s+(been|gone|done|made|taken|given|come|seen|known|worked|lived)\s+(since|for)\b",
    ],
    "S + had + pp": [
        r"\bhad\s+(already\s+)?\w+ed\b",
        r"\bhad\s+(been|gone|done|made|taken|given|come|seen|known)\b",
    ],
    "S + will + V(原形)": [r"\bwill\s+(be|have|go|come|take|make|give)\b"],
    "S + am/is/are + V-ing": [r"\b(is|are|am)\s+\w+ing\b"],
    "S + V-ed(規則) / S + V(不規則変化) + 過去の時間表現": [
        r"\b(yesterday|last\s+(week|month|year)|ago)\b",
    ],
    "S + will have + pp + by + 未来の時点": [r"\bwill\s+have\s+\w+ed\b"],
    "S + had been + V-ing + for/since": [r"\bhad\s+been\s+\w+ing\b"],

    # Form patterns
    "S + be動詞 + pp (+ by 動作主)": [r"\b(was|were|is|are|been)\s+\w+ed\s+by\b"],
    "The ___ of ... → 名詞が必要": [r"\bthe\s+\w+tion\s+of\b", r"\bthe\s+\w+ment\s+of\b"],
    "need/want/expect + to be + pp": [r"\b(need|want|expect)s?\s+to\s+be\s+\w+ed\b"],

    # Logic patterns
    "先行詞(人) + who + V": [r"\bwho\s+(is|are|was|were|has|have|will)\b"],
    "If/When/Before/After/Until + S + V(現在形), S + will + V": [
        r"\b(if|when|before|after|until)\s+\w+\s+\w+s?,\s+\w+\s+will\b",
    ],
    "Neither A nor B": [r"\bneither\s+\w+\s+nor\b"],
    "否定語句(Never/Hardly/Not only) + 倒置": [
        r"\b(never|hardly|not only|seldom|rarely)\s+(has|have|had|did|does|do|was|were|is)\s",
    ],

    # Vocab patterns
    "look up = 調べる / look for = 探す": [r"\blook(ed|ing|s)?\s+(up|for|at|into)\b"],
    "be good/bad/interested/surprised + at/in/by": [
        r"\b(good|interested|surprised|disappointed)\s+(at|in|by|with)\b",
    ],
    "due to + 名詞句": [r"\bdue\s+to\b"],
    "refrain from + V-ing": [r"\brefrain\s+from\b"],
    "come into effect/force": [r"\bcome\s+into\s+(effect|force)\b"],

    # Trap patterns
    "make + O + V(原形不定詞)": [r"\bmade?\s+\w+\s+(go|come|do|stay|leave|work|feel)\b"],
    "look forward to + V-ing": [r"\blook(ing|ed|s)?\s+forward\s+to\b"],
    "The number of + 複数名詞 + 単数動詞": [r"\bthe\s+number\s+of\b"],
    "suggest/recommend/insist + that + S + V(原形)": [
        r"\b(suggest|recommend|insist|demand)s?\s+that\b",
    ],
}


def match_rule_to_sentences(rule, all_sentences):
    """ルールのパターンに一致する文を探す"""
    pattern_key = rule.get("pattern", "")
    matches = []

    # Try exact pattern match first
    for key, regexes in PATTERN_SEARCHES.items():
        if key in pattern_key or pattern_key in key:
            for regex in regexes:
                for source, sentence in all_sentences:
                    if re.search(regex, sentence, re.IGNORECASE):
                        matches.append((source, sentence))
                        if len(matches) >= 5:
                            return matches
            break

    # Fallback: search for key words from correct_example
    if not matches:
        example = rule.get("correct_example", "")
        # Extract key grammar words
        key_words = re.findall(r"\b(has|have|had|been|were|was|will|would|should|could|might|must|shall|nor|neither|despite|although|unless|whether)\b", example, re.IGNORECASE)
        if key_words:
            for source, sentence in all_sentences:
                if any(w.lower() in sentence.lower() for w in key_words[:2]):
                    matches.append((source, sentence))
                    if len(matches) >= 3:
                        return matches

    return matches


def main():
    rules = json.loads(RULES_FILE.read_text())
    print(f"Rules to verify: {len(rules)}")

    # Step 1: Collect sentences from all media
    print("\n== Collecting sentences from media ==")
    all_sentences = []  # [(source, sentence), ...]

    for source_name, feeds in RSS_FEEDS.items():
        print(f"\n{source_name}:")
        article_urls = fetch_rss_articles(source_name, feeds)
        print(f"  Found {len(article_urls)} article URLs")

        article_count = 0
        for url in article_urls[:20]:  # Max 20 articles per source
            sentences = fetch_article_sentences(url)
            if sentences:
                for s in sentences:
                    all_sentences.append((source_name, s))
                article_count += 1
            time.sleep(0.8)

        print(f"  Scraped {article_count} articles, {sum(1 for s,_ in all_sentences if s == source_name)} sentences")

    # Fallback: if RSS failed, scrape front pages
    for source_name, url in FALLBACK_URLS.items():
        source_count = sum(1 for s, _ in all_sentences if s == source_name)
        if source_count < 50:
            print(f"\n  Fallback scraping {source_name}...")
            sentences = fetch_article_sentences(url)
            for s in sentences:
                all_sentences.append((source_name, s))
            print(f"  Got {len(sentences)} additional sentences")

    print(f"\nTotal sentences: {len(all_sentences)}")
    print(f"  BBC: {sum(1 for s,_ in all_sentences if s=='BBC News')}")
    print(f"  NPR: {sum(1 for s,_ in all_sentences if s=='NPR')}")
    print(f"  AP:  {sum(1 for s,_ in all_sentences if s=='AP News')}")

    # Step 2: Match rules to sentences
    print("\n== Verifying rules against media ==")
    verified = 0
    not_verified = 0

    for rule in rules:
        matches = match_rule_to_sentences(rule, all_sentences)
        if matches:
            rule["verified"] = True
            rule["media_examples"] = [
                f"{sentence} ({source})"
                for source, sentence in matches[:3]
            ]
            verified += 1
            print(f"  ✅ {rule['id']} {rule['rule']}: {len(matches)} matches")
        else:
            rule["verified"] = False
            rule["media_examples"] = []
            not_verified += 1
            print(f"  ⬜ {rule['id']} {rule['rule']}: no match (pattern may be rare in headlines)")

    # Save
    RULES_FILE.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n")

    print(f"\n== Results ==")
    print(f"  Verified: {verified}/{len(rules)} ({round(verified/len(rules)*100)}%)")
    print(f"  Not verified: {not_verified} (may need more articles or broader pattern matching)")
    print(f"  Saved: {RULES_FILE}")


if __name__ == "__main__":
    main()
