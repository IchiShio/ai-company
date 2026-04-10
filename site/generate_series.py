#!/usr/bin/env python3
"""
generate_series.py - ReadUp Graded Series 記事生成パイプライン
  VOA記事取得 → 4 VLレベルで書き直し → 語彙バリデーション → 和訳 → 理解度チェック2問 → stories.js追記

Usage:
  python3 generate_series.py                        # VOA最新記事1本 → 4レベル生成
  python3 generate_series.py --count 3              # 最新3本
  python3 generate_series.py --seed 8               # シード記事8週分(24本→96記事)
  python3 generate_series.py --url URL              # 指定VOA記事URL
  python3 generate_series.py --dry-run              # 生成のみ(stories.js更新なし)
"""
import argparse, json, os, re, sys, time, textwrap
from datetime import datetime, timedelta
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── 定数 ────────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).parent
DATA_DIR    = REPO_ROOT / "reading" / "series" / "data"
STORIES_JS  = REPO_ROOT / "reading" / "series" / "stories.js"
STAGING_JSON = REPO_ROOT / "reading" / "series" / "staging.json"

GEN_MODEL   = "claude-haiku-4-5-20251001"
CHECK_MODEL = "claude-sonnet-4-6"
MAX_TOKENS  = 4096

VL_LEVELS   = ["vl2000", "vl3000", "vl5000", "vl7000"]
VL_WORD_LIMITS = {
    "vl2000": (80, 100),
    "vl3000": (100, 120),
    "vl5000": (120, 140),
    "vl7000": (130, 150),
}

VOA_SECTIONS = [
    "https://learningenglish.voanews.com/z/3521",  # As It Is (ニュース)
    "https://learningenglish.voanews.com/z/1579",   # Health & Lifestyle
    "https://learningenglish.voanews.com/z/959",     # Science & Technology
]

# ─── 語彙リスト読み込み ──────────────────────────────────────────────────────

_vocab_cache = {}

def load_vocab(vl):
    """累積語彙セットを返す（例: vl3000 → 3000語のset）"""
    if vl in _vocab_cache:
        return _vocab_cache[vl]
    vocab_file = DATA_DIR / "vocab_levels.json"
    if not vocab_file.exists():
        print(f"ERROR: {vocab_file} not found. Run NGSL data setup first.")
        sys.exit(1)
    with open(vocab_file) as f:
        all_vocab = json.load(f)
    for level in VL_LEVELS:
        _vocab_cache[level] = set(all_vocab[level])
    return _vocab_cache[vl]


def tokenize(text):
    """テキストを単語リストに分割（固有名詞判定用に原形も保持）"""
    words = re.findall(r"[a-zA-Z]+(?:'[a-z]+)?", text)
    return words


# ─── 簡易lemmatizer ─────────────────────────────────────────────────────────

# 不規則変化動詞・名詞のマッピング
_IRREGULAR = {
    # be
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be",
    # have
    "has": "have", "had": "have", "having": "have",
    # do
    "does": "do", "did": "do", "doing": "do", "done": "do",
    # say
    "said": "say", "says": "say", "saying": "say",
    # go
    "went": "go", "goes": "go", "going": "go", "gone": "go",
    # get
    "got": "get", "gets": "get", "getting": "get", "gotten": "get",
    # make
    "made": "make", "makes": "make", "making": "make",
    # know
    "knew": "know", "knows": "know", "known": "know", "knowing": "know",
    # think
    "thought": "think", "thinks": "think", "thinking": "think",
    # take
    "took": "take", "takes": "take", "taken": "take", "taking": "take",
    # come
    "came": "come", "comes": "come", "coming": "come",
    # see
    "saw": "see", "sees": "see", "seen": "see", "seeing": "see",
    # give
    "gave": "give", "gives": "give", "given": "give", "giving": "give",
    # find
    "found": "find", "finds": "find", "finding": "find",
    # tell
    "told": "tell", "tells": "tell", "telling": "tell",
    # become
    "became": "become", "becomes": "become", "becoming": "become",
    # keep
    "kept": "keep", "keeps": "keep", "keeping": "keep",
    # leave
    "left": "leave", "leaves": "leave", "leaving": "leave",
    # bring
    "brought": "bring", "brings": "bring", "bringing": "bring",
    # begin
    "began": "begin", "begins": "begin", "begun": "begin", "beginning": "begin",
    # run
    "ran": "run", "runs": "run", "running": "run",
    # write
    "wrote": "write", "writes": "write", "written": "write", "writing": "write",
    # set
    "sets": "set", "setting": "set",
    # sit
    "sat": "sit", "sits": "sit", "sitting": "sit",
    # stand
    "stood": "stand", "stands": "stand", "standing": "stand",
    # lose
    "lost": "lose", "loses": "lose", "losing": "lose",
    # pay
    "paid": "pay", "pays": "pay", "paying": "pay",
    # meet
    "met": "meet", "meets": "meet", "meeting": "meet",
    # feel
    "felt": "feel", "feels": "feel", "feeling": "feel",
    # put
    "puts": "put", "putting": "put",
    # read
    "reads": "read", "reading": "read",
    # mean
    "meant": "mean", "means": "mean", "meaning": "mean",
    # grow
    "grew": "grow", "grows": "grow", "grown": "grow", "growing": "grow",
    # let
    "lets": "let", "letting": "let",
    # show
    "showed": "show", "shows": "show", "shown": "show", "showing": "show",
    # send
    "sent": "send", "sends": "send", "sending": "send",
    # build
    "built": "build", "builds": "build", "building": "build",
    # spend
    "spent": "spend", "spends": "spend", "spending": "spend",
    # fall
    "fell": "fall", "falls": "fall", "fallen": "fall", "falling": "fall",
    # cut
    "cuts": "cut", "cutting": "cut",
    # hold
    "held": "hold", "holds": "hold", "holding": "hold",
    # speak
    "spoke": "speak", "speaks": "speak", "spoken": "speak", "speaking": "speak",
    # lead
    "led": "lead", "leads": "lead", "leading": "lead",
    # buy
    "bought": "buy", "buys": "buy", "buying": "buy",
    # sell
    "sold": "sell", "sells": "sell", "selling": "sell",
    # teach
    "taught": "teach", "teaches": "teach", "teaching": "teach",
    # catch
    "caught": "catch", "catches": "catch", "catching": "catch",
    # break
    "broke": "break", "breaks": "break", "broken": "break", "breaking": "break",
    # draw
    "drew": "draw", "draws": "draw", "drawn": "draw", "drawing": "draw",
    # drive
    "drove": "drive", "drives": "drive", "driven": "drive", "driving": "drive",
    # choose
    "chose": "choose", "chooses": "choose", "chosen": "choose", "choosing": "choose",
    # rise
    "rose": "rise", "rises": "rise", "risen": "rise", "rising": "rise",
    # win
    "won": "win", "wins": "win", "winning": "win",
    # wear
    "wore": "wear", "wears": "wear", "worn": "wear", "wearing": "wear",
    # fly
    "flew": "fly", "flies": "fly", "flown": "fly", "flying": "fly",
    # eat
    "ate": "eat", "eats": "eat", "eaten": "eat", "eating": "eat",
    # drink
    "drank": "drink", "drinks": "drink", "drunk": "drink", "drinking": "drink",
    # sleep
    "slept": "sleep", "sleeps": "sleep", "sleeping": "sleep",
    # die
    "died": "die", "dies": "die", "dying": "die",
    # lie
    "lay": "lie", "lies": "lie", "lain": "lie", "lying": "lie",
    # throw
    "threw": "throw", "throws": "throw", "thrown": "throw", "throwing": "throw",

    # 不規則名詞
    "children": "child", "men": "man", "women": "woman", "people": "person",
    "feet": "foot", "teeth": "tooth", "mice": "mouse", "lives": "life",
    "babies": "baby", "cities": "city", "countries": "country", "families": "family",
    "stories": "story", "studies": "study", "bodies": "body", "copies": "copy",
    "parties": "party", "armies": "army", "enemies": "enemy", "ladies": "lady",
    "policies": "policy", "economies": "economy", "opportunities": "opportunity",
    "activities": "activity", "communities": "community", "companies": "company",
    "industries": "industry", "centuries": "century", "categories": "category",

    # 代名詞の格変化
    "his": "he", "him": "he", "her": "she", "hers": "she",
    "its": "it", "them": "they", "their": "they", "theirs": "they",
    "us": "we", "our": "we", "ours": "we",
    "my": "i", "me": "i", "mine": "i", "myself": "i",
}


def lemmatize(word):
    """簡易lemmatizer: 不規則変化→接尾辞除去"""
    w = word.lower()

    # 不規則変化辞書
    if w in _IRREGULAR:
        return _IRREGULAR[w]

    # 規則的な接尾辞除去（順序重要）
    # -ies → -y (carries → carry, but not "series")
    if w.endswith("ies") and len(w) > 4:
        candidate = w[:-3] + "y"
        return candidate
    # -es → base (watches → watch, goes → go)
    if w.endswith("es") and len(w) > 3:
        # -shes, -ches, -xes, -zes, -sses
        if w[-3] in "shxz" or w.endswith("sses"):
            return w[:-2]
    # -s → base (runs → run)
    if w.endswith("s") and not w.endswith("ss") and len(w) > 2:
        candidate = w[:-1]
        return candidate
    # -ed → base (started → start, tried → try)
    if w.endswith("ied") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ed") and len(w) > 3:
        # doubled consonant (stopped → stop)
        if len(w) > 4 and w[-3] == w[-4] and w[-3] not in "aeiou":
            return w[:-3]
        return w[:-2] if not w.endswith("eed") else w
    # -ing → base
    if w.endswith("ing") and len(w) > 4:
        # doubled consonant (running → run)
        if len(w) > 5 and w[-4] == w[-5] and w[-4] not in "aeiou":
            return w[:-4]
        # -ting → -te (creating → create) - heuristic
        if w.endswith("ting") and len(w) > 5:
            candidate = w[:-3] + "e"
            return candidate
        return w[:-3]
    # -er → base (higher → high)
    if w.endswith("er") and len(w) > 3:
        return w[:-2]
    # -est → base (highest → high)
    if w.endswith("est") and len(w) > 4:
        return w[:-3]
    # -ly → base (quickly → quick)
    if w.endswith("ly") and len(w) > 3:
        return w[:-2]

    return w


def is_proper_noun(word):
    """固有名詞判定（大文字始まり、かつ文頭でない可能性が高い）"""
    # 簡易判定：全大文字（NATO, US）、大文字始まり（Japan, Musk）
    if word.isupper() and len(word) >= 2:
        return True
    if word[0].isupper() and len(word) > 1:
        return True
    return False


# 基本語の許容リスト（NGSLのlemmaにないが英語として基本的な語）
_ALLOWLIST = {
    # 数字
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "million", "billion",
    "first", "second", "third",
    # 冠詞・基本語（NGSLから漏れているもの）
    "an", "the",
    # 基本形容詞・副詞
    "born", "tired", "dirty", "earlier", "later", "largest", "lowest",
    # 基本動詞派生
    "cannot", "gonna", "wanna",
}


def validate_vocab(text, vl):
    """語彙バリデーション。VL外単語のリストと割合を返す"""
    vocab = load_vocab(vl) | _ALLOWLIST
    words = tokenize(text)
    total = 0
    outside = []
    for w in words:
        lower = w.lower()
        # 固有名詞・数字はスキップ
        if is_proper_noun(w):
            continue
        # 短縮形の処理 (don't → do, n't)
        base = re.sub(r"'[a-z]+$", "", lower)
        total += 1
        # lemmatize して照合
        lemma = lemmatize(lower)
        lemma_base = lemmatize(base)
        if base in vocab or lower in vocab or lemma in vocab or lemma_base in vocab:
            continue
        outside.append(lower)
    unique_outside = list(dict.fromkeys(outside))  # 重複除去（順序保持）
    coverage = (total - len(outside)) / total * 100 if total > 0 else 100
    return unique_outside, coverage, total


# ─── VOA記事取得 ─────────────────────────────────────────────────────────────

def fetch_voa_articles(count=1):
    """VOA Learning English セクションページから記事を取得しスクレイプ"""
    import urllib.request

    print(f"Fetching VOA articles ({count} needed)...")
    article_urls = []

    # セクションページから記事URLを収集
    for section_url in VOA_SECTIONS:
        try:
            req = urllib.request.Request(section_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8")
            links = re.findall(r'href="(/a/[^"]+\.html)"', html)
            unique = list(dict.fromkeys(links))
            for l in unique:
                full_url = f"https://learningenglish.voanews.com{l}"
                if full_url not in article_urls:
                    article_urls.append(full_url)
        except Exception as e:
            print(f"  Section {section_url} failed: {e}")
            continue

    print(f"  Found {len(article_urls)} article URLs")

    # 各記事の本文を取得
    articles = []
    for url in article_urls:
        if len(articles) >= count:
            break
        article = _scrape_voa_article(url)
        if article:
            articles.append(article)
            print(f"  ✓ {article['title'][:60]} ({len(article['text'].split())} words)")

    print(f"  Got {len(articles)} articles with content")
    return articles


def _scrape_voa_article(url):
    """VOA記事ページから本文を抽出"""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except Exception:
        return None

    title_match = re.search(r"<title>([^<]+)</title>", html)
    title = title_match.group(1).strip().rstrip(" | VOA Learning English") if title_match else ""
    if not title:
        return None

    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    clean = []
    for p in paragraphs:
        text = re.sub(r"<[^>]+>", "", p).strip()
        text = re.sub(r"&#\d+;", "'", text)
        skip_words = ["browser", "javascript", "comment", "download", "subscribe", "click here"]
        if len(text) > 30 and not any(sw in text.lower() for sw in skip_words):
            clean.append(text)

    full_text = " ".join(clean)
    if len(full_text) < 200:
        return None

    return {"title": title, "url": url, "text": full_text[:3000]}


def fetch_voa_article_by_url(url):
    """指定URLからVOA記事テキストを取得"""
    print(f"Fetching {url}...")
    article = _scrape_voa_article(url)
    if not article:
        print("  Could not extract article text")
    return article


# ─── プロンプト ───────────────────────────────────────────────────────────────

def build_gen_prompt(article_text, article_title, vl):
    min_w, max_w = VL_WORD_LIMITS[vl]
    vocab_num = int(vl.replace("vl", ""))

    return f"""あなたは英語教育の専門家です。以下のニュース記事を、英語学習者向けに書き直してください。

=== 元記事 ===
タイトル: {article_title}
本文: {article_text[:2000]}

=== 書き直し条件 ===
語彙レベル: {vl.upper()}（上位{vocab_num}語の範囲内で書く）
語数: {min_w}〜{max_w}語（厳守）
VL外の一般単語: 最大2語まで（固有名詞は制限なし）

=== VLレベルの書き方ガイド ===
- VL2000: 極めてシンプルな英語。短い文（SVO基本）。接続詞は and/but/because のみ。
- VL3000: やや複雑な文構造OK。関係代名詞・受動態OK。
- VL5000: 新聞記事に近い自然な英語。分詞構文・仮定法OK。
- VL7000: ほぼネイティブ向けニュース英語。高度な表現OK。

=== 重要ルール ===
- 記事は一般的に知られた事実のみ。架空の統計・数値は絶対禁止。
- 元記事の事実を正確に反映すること。
- 固有名詞（人名・地名・組織名）はそのまま使ってよい。
- タイトルも{vl.upper()}レベルの語彙で書く。

=== 出力形式（JSONのみ、コードブロック不要） ===
{{
  "title": "英語タイトル",
  "body": "英語本文（1段落。改行なし）",
  "vocab_notes": [
    {{"word": "VL外単語", "vl": 推定VLレベル(数値), "definition": "easy English definition"}}
  ]
}}"""


def build_ja_prompt(title, body):
    return f"""以下の英文の自然な日本語訳を作成してください。

タイトル: {title}
本文: {body}

=== ルール ===
- 直訳ではなく、日本語として自然な訳にする
- 固有名詞はカタカナ表記
- 簡潔に（原文と同程度の長さ）

=== 出力形式（JSONのみ） ===
{{
  "title_ja": "日本語タイトル",
  "body_ja": "日本語訳本文"
}}"""


def build_quiz_prompt(title, body):
    return f"""以下の英文パッセージについて、理解度チェック問題を2問作成してください。

タイトル: {title}
本文: {body}

=== ルール ===
- 設問・選択肢・解説はすべて日本語
- 4択（正解1つ＋誤答3つ）
- 正解を先頭に置かない
- 1問目: detail（具体的な事実を問う）
- 2問目: main_idea or inference（主旨または推論）

=== 出力形式（JSON配列のみ） ===
[
  {{
    "axis": "detail",
    "q": "設問文（日本語）",
    "choices": ["誤答A", "正解", "誤答B", "誤答C"],
    "answer": 1,
    "expl": "解説（日本語、パッセージの根拠箇所を引用）"
  }},
  {{
    "axis": "main_idea",
    "q": "設問文（日本語）",
    "choices": ["誤答A", "誤答B", "正解", "誤答C"],
    "answer": 2,
    "expl": "解説（日本語）"
  }}
]"""


def build_annotated(body, vl):
    """body_annotated を構築（単語ごとにVLレベルを付与）"""
    words = re.findall(r"[a-zA-Z]+(?:'[a-z]+)?|[^a-zA-Z\s]+|\s+", body)
    vocab = load_vocab(vl) | _ALLOWLIST
    annotated = []
    for token in words:
        if re.match(r"^[a-zA-Z]", token):
            lower = token.lower()
            base = re.sub(r"'[a-z]+$", "", lower)
            lemma = lemmatize(lower)
            lemma_base = lemmatize(base)
            if is_proper_noun(token):
                annotated.append({"w": token, "vl": None})
            elif base in vocab or lower in vocab or lemma in vocab or lemma_base in vocab:
                # VLレベル特定
                level = None
                for lvl in VL_LEVELS:
                    if base in load_vocab(lvl) or lower in load_vocab(lvl):
                        level = int(lvl.replace("vl", ""))
                        break
                annotated.append({"w": token, "vl": level})
            else:
                annotated.append({"w": token, "vl": None, "outside": True})
        else:
            annotated.append({"w": token})
    return annotated


# ─── JSON パース ─────────────────────────────────────────────────────────────

def parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Raw (first 300): {raw[:300]}")
        return None


# ─── メイン生成フロー ─────────────────────────────────────────────────────────

def generate_article(client, article, week_id, pub_date, article_idx):
    """1つのVOA記事から4レベル分のstoryを生成"""
    stories = []

    for vl in VL_LEVELS:
        min_w, max_w = VL_WORD_LIMITS[vl]
        story_id = f"{week_id}_{article_idx:02d}_{vl}"
        print(f"\n  [{vl.upper()}] Generating {story_id}...")

        # Step 1: 記事を書き直し（最大3回リトライ）
        success = False
        for attempt in range(3):
            resp = client.messages.create(
                model=GEN_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": build_gen_prompt(
                    article["text"], article["title"], vl
                )}]
            )
            data = parse_json(resp.content[0].text)
            if not data or "body" not in data:
                print(f"    Attempt {attempt+1}: parse failed, retrying...")
                continue

            body = data["body"]
            title = data.get("title", article["title"])
            vocab_notes = data.get("vocab_notes", [])

            # 語数チェック
            word_count = len(tokenize(body))
            if word_count < min_w - 10 or word_count > max_w + 20:
                print(f"    Attempt {attempt+1}: word count {word_count} out of range ({min_w}-{max_w}), retrying...")
                continue

            # 語彙バリデーション
            outside, coverage, total = validate_vocab(body, vl)
            if len(outside) > 2:
                print(f"    Attempt {attempt+1}: {len(outside)} VL-outside words ({outside[:5]}), retrying...")
                continue

            success = True
            print(f"    ✓ {word_count} words, coverage {coverage:.1f}%, VL-outside: {outside}")
            break

        if not success:
            print(f"    ✗ Failed after 3 attempts, skipping {vl}")
            continue

        # Step 2: 和訳生成
        print(f"    Generating Japanese translation...")
        resp_ja = client.messages.create(
            model=GEN_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": build_ja_prompt(title, body)}]
        )
        ja_data = parse_json(resp_ja.content[0].text)
        title_ja = ja_data.get("title_ja", "") if ja_data else ""
        body_ja = ja_data.get("body_ja", "") if ja_data else ""

        # Step 3: 理解度チェック2問
        print(f"    Generating quiz questions...")
        resp_q = client.messages.create(
            model=GEN_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": build_quiz_prompt(title, body)}]
        )
        questions = parse_json(resp_q.content[0].text)
        if not isinstance(questions, list):
            questions = []
        # バリデーション
        valid_qs = []
        for q in questions[:2]:
            if isinstance(q, dict) and "q" in q and "choices" in q and isinstance(q["choices"], list) and len(q["choices"]) == 4:
                valid_qs.append(q)
        questions = valid_qs

        # Step 4: body_annotated 構築
        annotated = build_annotated(body, vl)

        # vocab_notes の補完（VL外単語が vocab_notes にない場合追加）
        noted_words = {n["word"].lower() for n in vocab_notes}
        for w in outside:
            if w not in noted_words:
                vocab_notes.append({"word": w, "vl": None, "definition": ""})

        story = {
            "id": story_id,
            "vl": vl,
            "week": week_id,
            "pub_date": pub_date,
            "source_url": article.get("url", ""),
            "source_title": article["title"],
            "title": title,
            "title_ja": title_ja,
            "word_count": word_count,
            "body": body,
            "body_ja": body_ja,
            "body_annotated": annotated,
            "vocab_notes": vocab_notes,
            "questions": questions,
        }
        stories.append(story)
        time.sleep(0.5)  # rate limit

    return stories


# ─── stories.js 管理 ──────────────────────────────────────────────────────────

def load_stories():
    """既存のstories.jsを読み込み"""
    if not STORIES_JS.exists():
        return []
    text = STORIES_JS.read_text(encoding="utf-8")
    # "const STORIES = [...];" 形式をパース
    match = re.search(r'const\s+STORIES\s*=\s*(\[.*\])\s*;', text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return []


def save_stories(stories):
    """stories.jsに書き出し"""
    STORIES_JS.parent.mkdir(parents=True, exist_ok=True)
    data_str = json.dumps(stories, ensure_ascii=False, indent=2)
    STORIES_JS.write_text(f"const STORIES = {data_str};\n", encoding="utf-8")
    print(f"\nWrote {len(stories)} stories to {STORIES_JS}")


def save_staging(new_stories):
    """staging.jsonに保存（ファクトチェック前の一時保存）"""
    STAGING_JSON.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if STAGING_JSON.exists():
        try:
            existing = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    existing.extend(new_stories)
    STAGING_JSON.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(new_stories)} stories to staging ({len(existing)} total)")


# ─── ファクトチェック ─────────────────────────────────────────────────────────

def factcheck_stories(client, stories):
    """Sonnetでファクトチェック"""
    if not stories:
        return stories

    print(f"\nFact-checking {len(stories)} stories with {CHECK_MODEL}...")
    summaries = []
    for s in stories:
        summaries.append({
            "id": s["id"],
            "vl": s["vl"],
            "source_title": s.get("source_title", ""),
            "title": s["title"],
            "body": s["body"],
            "body_ja": s.get("body_ja", ""),
            "questions": s.get("questions", []),
        })

    prompt = f"""以下のReadUp Graded Series記事をファクトチェックしてください。

チェック項目:
1. bodyの内容が事実として正確か（元記事タイトルから判断）
2. body_jaがbodyの正確な訳か
3. questionsのanswer(インデックス)が正しいか
4. 架空の統計・数値がないか

各記事についてok: true/falseを返す。
falseの場合は reason と、可能なら修正を含める。

出力形式（JSONのみ、コードブロック不要）:
[
  {{"id": "...", "ok": true}},
  {{"id": "...", "ok": false, "reason": "理由", "fix": {{"body": "修正後", "body_ja": "修正後"}}}}
]

対象データ:
{json.dumps(summaries, ensure_ascii=False, indent=2)}"""

    resp = client.messages.create(
        model=CHECK_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    results = parse_json(resp.content[0].text)
    if not isinstance(results, list):
        print("  WARNING: factcheck parse failed, accepting all")
        return stories

    result_map = {r["id"]: r for r in results if isinstance(r, dict)}
    checked = []
    for s in stories:
        r = result_map.get(s["id"])
        if r is None or r.get("ok", True):
            checked.append(s)
            print(f"  ✓ {s['id']}")
        else:
            reason = r.get("reason", "unknown")
            fix = r.get("fix")
            if fix:
                if "body" in fix:
                    s["body"] = fix["body"]
                    s["body_annotated"] = build_annotated(fix["body"], s["vl"])
                    s["word_count"] = len(tokenize(fix["body"]))
                if "body_ja" in fix:
                    s["body_ja"] = fix["body_ja"]
                checked.append(s)
                print(f"  ⚠ {s['id']}: fixed ({reason})")
            else:
                print(f"  ✗ {s['id']}: rejected ({reason})")

    return checked


# ─── メイン ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ReadUp Graded Series generator")
    parser.add_argument("--count", type=int, default=1, help="Number of VOA articles to process")
    parser.add_argument("--seed", type=int, default=0, help="Generate seed articles for N weeks (3 per week)")
    parser.add_argument("--url", type=str, help="Specific VOA article URL")
    parser.add_argument("--dry-run", action="store_true", help="Don't update stories.js")
    parser.add_argument("--no-check", action="store_true", help="Skip fact-checking")
    parser.add_argument("--resume", action="store_true", help="Resume from staging.json")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env or environment")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if args.resume:
        if not STAGING_JSON.exists():
            print("No staging.json found")
            sys.exit(1)
        new_stories = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
        print(f"Resuming with {len(new_stories)} stories from staging")
    else:
        # VOA記事取得
        if args.url:
            article = fetch_voa_article_by_url(args.url)
            if not article:
                sys.exit(1)
            articles = [article]
        elif args.seed > 0:
            total_articles = args.seed * 3
            articles = fetch_voa_articles(total_articles)
            if len(articles) < total_articles:
                print(f"WARNING: Only got {len(articles)} articles (needed {total_articles})")
        else:
            articles = fetch_voa_articles(args.count)

        if not articles:
            print("No articles to process")
            sys.exit(1)

        # 生成
        today = datetime.now()
        new_stories = []
        for idx, article in enumerate(articles):
            if args.seed > 0:
                # シード: 週3記事 × N週
                week_num = idx // 3
                day_in_week = idx % 3  # 0=月, 1=水, 2=金
                pub_date_dt = today - timedelta(weeks=args.seed - 1 - week_num) + timedelta(days=[0, 2, 4][day_in_week])
                week_id = pub_date_dt.strftime("%YW%W")
            else:
                pub_date_dt = today + timedelta(days=idx)
                week_id = pub_date_dt.strftime("%YW%W")

            pub_date = pub_date_dt.strftime("%Y-%m-%d")
            article_idx = (idx % 3) + 1

            print(f"\n{'='*60}")
            print(f"Article {idx+1}/{len(articles)}: {article['title'][:60]}")
            print(f"Week: {week_id}, Date: {pub_date}")
            print(f"{'='*60}")

            stories = generate_article(client, article, week_id, pub_date, article_idx)
            new_stories.extend(stories)

            # 中間保存
            save_staging(stories)
            time.sleep(1)

    # ファクトチェック
    if not args.no_check and new_stories:
        new_stories = factcheck_stories(client, new_stories)

    # stories.js 更新
    if not args.dry_run and new_stories:
        existing = load_stories()
        existing_ids = {s["id"] for s in existing}
        added = [s for s in new_stories if s["id"] not in existing_ids]
        if added:
            existing.extend(added)
            save_stories(existing)
            print(f"\nAdded {len(added)} new stories (total: {len(existing)})")
        else:
            print("\nNo new stories to add (all duplicates)")

    # サマリー
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    for vl in VL_LEVELS:
        count = sum(1 for s in new_stories if s["vl"] == vl)
        print(f"  {vl.upper()}: {count} stories")
    print(f"  Total: {len(new_stories)} stories")
    if args.dry_run:
        print("  (dry-run: stories.js not updated)")


if __name__ == "__main__":
    main()
