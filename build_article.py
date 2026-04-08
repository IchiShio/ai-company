#!/usr/bin/env python3
"""
API不要の記事ビルダー
テンプレートパーツ + コンテンツJSONから完全なHTMLを組み立てる

使い方:
  # コンテンツJSONから記事を生成
  python3 build_article.py articles/staging/my-article.json

  # ドライラン（ファイル書き込みなし）
  python3 build_article.py articles/staging/my-article.json --dry-run

  # staging/ 内の全JSONを一括処理
  python3 build_article.py --all

コンテンツJSON形式:
{
  "slug": "online-eikaiwa-how-long",
  "title": "オンライン英会話の効果が出るまでの期間",
  "description": "meta descriptionテキスト",
  "category_label": "英語学習コラム",
  "body_html": "<h2>...</h2><p>...</p>...",
  "related": [
    {"href": "/articles/xxx/", "text": "記事タイトル"},
    ...
  ]
}
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
ARTICLES_DIR = BASE_DIR / "articles"
STAGING_DIR = ARTICLES_DIR / "staging"
SITEMAP_PATH = BASE_DIR / "sitemap.xml"

TODAY = date.today().isoformat()


def load_template(name: str) -> str:
    p = TEMPLATES_DIR / name
    if not p.exists():
        sys.exit(f"テンプレート {p} が見つかりません")
    return p.read_text(encoding="utf-8")


def build_head(meta: dict) -> str:
    title = meta["title"]
    desc = meta["description"]
    slug = meta["slug"]
    canonical = f"https://native-real.com/articles/{slug}/"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','GTM-PS9R9844');</script>
  <!-- End Google Tag Manager -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>{title} | native-real</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="native-real">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="author" content="native-real編集部">
  <meta property="og:locale" content="ja_JP">
  <meta property="og:image" content="https://native-real.com/assets/ogp.png">
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{desc}",
  "datePublished": "{TODAY}",
  "dateModified": "{TODAY}",
  "publisher": {{
    "@type": "Organization",
    "name": "native-real"
  }}
}}
</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
"""


def build_breadcrumb(title: str) -> str:
    short = title[:40] + "..." if len(title) > 40 else title
    return f"""<div class="breadcrumb container">
  <a href="/">ホーム</a><span>›</span><a href="/articles/">学習コラム</a><span>›</span>{short}
</div>"""


def build_body(meta: dict) -> str:
    title = meta["title"]
    label = meta.get("category_label", "英語学習コラム")
    body_html = meta["body_html"]
    related = meta.get("related", [])

    related_html = ""
    if related:
        items = "\n".join(
            f'          <li><a href="{r["href"]}">{r["text"]}</a></li>'
            for r in related
        )
        related_html = f"""
      <div class="related-articles">
        <h3>関連記事</h3>
        <ul class="related-list">
{items}
        </ul>
      </div>"""

    return f"""<div class="container">
  <div class="article-layout">
    <main class="article-content">
      <span style="display:inline-block;background:var(--primary-pale);color:var(--primary);font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:6px;margin-bottom:16px;">{label}</span>
      <h1>{title}</h1>

{body_html}

      <div class="quiz-promo">
        <div class="quiz-promo-orb"></div>
        <div class="quiz-promo-inner">
          <div class="quiz-promo-icon">🎧</div>
          <div class="quiz-promo-body">
            <p class="quiz-promo-title">英語リスニング、今日の5問で実力チェック</p>
            <p class="quiz-promo-sub">1,099問・5段階レベル・完全無料 — 今すぐ聴き取りに挑戦できます</p>
          </div>
          <a href="/" class="quiz-promo-btn">無料で試す →</a>
        </div>
      </div>
      <div class="disclaimer">
        ※本記事はアフィリエイト広告を含みます。料金・サービス内容は変更される場合があります。最新情報は各公式サイトでご確認ください。
      </div>
{related_html}
    </main>
    <aside class="sidebar">
      <div class="sidebar-widget quiz-promo-widget">
        <div class="quiz-promo-orb"></div>
        <p class="quiz-promo-widget-label">🎧 英語力診断</p>
        <p class="quiz-promo-widget-title">リスニングクイズで<br>実力チェック</p>
        <p class="quiz-promo-widget-sub">1,099問・無料・5段階レベル</p>
        <a href="/" class="quiz-promo-btn">無料で試す →</a>
      </div>
      <div class="sidebar-widget">
        <h4>人気ランキング</h4>
        <div class="sidebar-service-list">
          <div class="sidebar-service-item"><a href="/services/dmm-eikaiwa/">DMM英会話</a></div>
          <div class="sidebar-service-item"><a href="/services/rarejob/">レアジョブ英会話</a></div>
          <div class="sidebar-service-item"><a href="/services/nativecamp/">ネイティブキャンプ</a></div>
        </div>
        <div style="margin-top:14px;">
          <a href="/ranking/" class="btn-primary" style="width:100%;display:block;text-align:center;">ランキングを見る</a>
        </div>
      </div>
    </aside>
  </div>
</div>
"""


def update_sitemap(slug: str):
    url = f"https://native-real.com/articles/{slug}/"
    content = SITEMAP_PATH.read_text(encoding="utf-8")
    if url in content:
        return False
    entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>"""
    content = content.replace("</urlset>", entry)
    SITEMAP_PATH.write_text(content, encoding="utf-8")
    return True


def build_article(json_path: Path, dry_run: bool = False) -> str:
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    slug = meta["slug"]

    head = build_head(meta)
    style = load_template("article-style.html")
    header = load_template("article-header.html")
    breadcrumb = build_breadcrumb(meta["title"])
    body = build_body(meta)
    footer = load_template("article-footer.html")

    html = head + style + header + "\n" + breadcrumb + "\n" + body + footer

    if dry_run:
        print(f"  [DRY-RUN] {slug}: {len(html)} bytes")
        return slug

    out_dir = ARTICLES_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    added = update_sitemap(slug)
    sm = " + sitemap更新" if added else ""
    print(f"  ✅ {slug}: {len(html):,} bytes{sm}")
    return slug


def main():
    parser = argparse.ArgumentParser(description="API不要の記事ビルダー")
    parser.add_argument("json_file", nargs="?", help="コンテンツJSONファイル")
    parser.add_argument("--all", action="store_true", help="staging/内の全JSONを処理")
    parser.add_argument("--dry-run", action="store_true", help="ファイル書き込みなし")
    args = parser.parse_args()

    if not args.json_file and not args.all:
        parser.print_help()
        sys.exit(1)

    files = []
    if args.all:
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(STAGING_DIR.glob("*.json"))
        if not files:
            print("staging/ にJSONファイルがありません")
            sys.exit(0)
    else:
        files = [Path(args.json_file)]

    print(f"=== 記事ビルド {'(dry-run) ' if args.dry_run else ''}===")
    built = []
    for f in files:
        slug = build_article(f, dry_run=args.dry_run)
        built.append(slug)

    print(f"\n完了: {len(built)} 記事をビルド")


if __name__ == "__main__":
    main()
