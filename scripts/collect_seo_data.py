#!/usr/bin/env python3
"""
native-real.com SEOデータ収集スクリプト
Google Search Console API + GA4 Data API でデータを取得する。
ブラウザ不要・OAuth refresh token で完全自動化。

使い方:
  初回認証:  python3 collect_seo_data.py --auth
  通常実行:  python3 collect_seo_data.py
  日付指定:  python3 collect_seo_data.py --date 2026-03-29
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime, timedelta, date
from pathlib import Path

# Google API
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric
)
from google.oauth2.credentials import Credentials as OAuth2Credentials

# ─────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]

CREDENTIALS_FILE = Path.home() / ".config/ichishio/google_seo_credentials.json"
TOKEN_FILE       = Path.home() / ".config/ichishio/google_seo_token.json"

SITE_URL     = "https://native-real.com/"
GA4_PROPERTY = "properties/525926980"
DAYS         = 28

DRIVE_BASE = Path.home() / "Library/CloudStorage/GoogleDrive-ichieigo7@gmail.com/マイドライブ/GoogleG4,SearchConsole"


# ─────────────────────────────────────────────
# 認証
# ─────────────────────────────────────────────

def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
        return creds
    raise RuntimeError(
        f"認証が必要です。先に以下を実行してください:\n"
        f"  python3 {__file__} --auth"
    )


def run_auth_flow():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: credentials.json が見つかりません: {CREDENTIALS_FILE}")
        print()
        print("Google Cloud Console で以下の手順を実行してください:")
        print("1. https://console.cloud.google.com/apis/library を開く")
        print("2. 'Google Search Console API' を有効化")
        print("3. 'Google Analytics Data API' を有効化")
        print("4. 認証情報 → OAuth 2.0 クライアントID → デスクトップアプリ で作成")
        print(f"5. JSONをダウンロードして {CREDENTIALS_FILE} に保存")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    print(f"✅ 認証完了。トークンを {TOKEN_FILE} に保存しました。")
    print("次回以降は自動的にリフレッシュされます。")
    return creds


def _save_token(creds):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


# ─────────────────────────────────────────────
# Search Console データ取得
# ─────────────────────────────────────────────

def fetch_gsc(creds, end_date: date):
    start_date = end_date - timedelta(days=DAYS - 1)
    svc = build("searchconsole", "v1", credentials=creds)

    def query(dimensions, row_limit=1000):
        body = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "dimensions": dimensions,
            "rowLimit": row_limit,
        }
        res = svc.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
        return res.get("rows", [])

    results = {}

    # クエリ別
    rows = query(["query"])
    results["queries"] = [
        ["上位のクエリ", "クリック数", "表示回数", "CTR", "掲載順位"]
    ] + [
        [r["keys"][0], r["clicks"], r["impressions"],
         f"{r['ctr']*100:.2f}%", f"{r['position']:.1f}"]
        for r in rows
    ]

    # ページ別
    rows = query(["page"])
    results["pages"] = [
        ["上位のページ", "クリック数", "表示回数", "CTR", "掲載順位"]
    ] + [
        [r["keys"][0], r["clicks"], r["impressions"],
         f"{r['ctr']*100:.2f}%", f"{r['position']:.1f}"]
        for r in rows
    ]

    # デバイス別
    rows = query(["device"])
    results["devices"] = [
        ["デバイス", "クリック数", "表示回数", "CTR", "掲載順位"]
    ] + [
        [r["keys"][0], r["clicks"], r["impressions"],
         f"{r['ctr']*100:.2f}%", f"{r['position']:.1f}"]
        for r in rows
    ]

    # 国別
    rows = query(["country"])
    results["countries"] = [
        ["国", "クリック数", "表示回数", "CTR", "掲載順位"]
    ] + [
        [r["keys"][0], r["clicks"], r["impressions"],
         f"{r['ctr']*100:.2f}%", f"{r['position']:.1f}"]
        for r in rows
    ]

    # 日付別
    rows = query(["date"])
    results["dates"] = [
        ["日付", "クリック数", "表示回数", "CTR", "掲載順位"]
    ] + [
        [r["keys"][0], r["clicks"], r["impressions"],
         f"{r['ctr']*100:.2f}%", f"{r['position']:.1f}"]
        for r in rows
    ]

    return results


# ─────────────────────────────────────────────
# GA4 データ取得
# ─────────────────────────────────────────────

def fetch_ga4(creds, end_date: date):
    start_date = end_date - timedelta(days=DAYS - 1)
    start_str = str(start_date)
    end_str   = str(end_date)

    client = BetaAnalyticsDataClient(credentials=creds)

    results = {}

    # トラフィック獲得（チャネル別）
    req = RunReportRequest(
        property=GA4_PROPERTY,
        date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="eventCount"),
            Metric(name="conversions"),
            Metric(name="sessionConversionRate"),
            Metric(name="totalRevenue"),
        ],
        limit=100,
    )
    resp = client.run_report(req)

    header_comment = (
        "# ----------------------------------------\n"
        "# トラフィック獲得: セッションのメインのチャネル グループ（デフォルト チャネル グループ）\n"
        f"# 開始日: {start_str.replace('-','')}\n"
        f"# 終了日: {end_str.replace('-','')}\n"
        "# ----------------------------------------\n"
        "#\n"
        "# すべてのユーザー\n"
    )
    header = "セッションのメインのチャネル グループ（デフォルト チャネル グループ）,セッション,エンゲージのあったセッション数,エンゲージメント率,セッションあたりの平均エンゲージメント時間,イベント数,キーイベント,セッション キーイベント率,合計収益"
    rows = []
    for row in resp.rows:
        rows.append(",".join([row.dimension_values[0].value] +
                              [m.value for m in row.metric_values]))
    results["ga4_traffic"] = header_comment + header + "\n" + "\n".join(rows) + "\n"

    # ページとスクリーン
    req2 = RunReportRequest(
        property=GA4_PROPERTY,
        date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="activeUsers"),
            Metric(name="screenPageViewsPerUser"),
            Metric(name="userEngagementDuration"),
            Metric(name="eventCount"),
            Metric(name="conversions"),
            Metric(name="totalRevenue"),
        ],
        order_bys=[{"metric": {"metric_name": "screenPageViews"}, "desc": True}],
        limit=200,
    )
    resp2 = client.run_report(req2)

    header_comment2 = (
        "# ----------------------------------------\n"
        "# ページとスクリーン: ページパスとスクリーン クラス\n"
        f"# 開始日: {start_str.replace('-','')}\n"
        f"# 終了日: {end_str.replace('-','')}\n"
        "# ----------------------------------------\n"
        "#\n"
        "# すべてのユーザー\n"
    )
    header2 = "ページパスとスクリーン クラス,表示回数,アクティブ ユーザー,アクティブ ユーザーあたりのビュー,アクティブ ユーザーあたりの平均エンゲージメント時間,イベント数,キーイベント,合計収益"
    rows2 = []
    for row in resp2.rows:
        path = row.dimension_values[0].value
        metrics = [m.value for m in row.metric_values]
        rows2.append(",".join([path] + metrics))
    results["ga4_pages"] = header_comment2 + header2 + "\n" + "\n".join(rows2) + "\n"

    return results


# ─────────────────────────────────────────────
# CSV書き込み
# ─────────────────────────────────────────────

def write_csv(dest_dir: Path, filename: str, rows: list):
    path = dest_dir / filename
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return len(rows) - 1  # ヘッダー除くデータ行数


def write_text(dest_dir: Path, filename: str, content: str):
    path = dest_dir / filename
    path.write_text(content, encoding="utf-8-sig")


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true", help="初回OAuth認証フロー")
    parser.add_argument("--date", help="取得終了日 (YYYY-MM-DD)。省略時は昨日")
    args = parser.parse_args()

    if args.auth:
        run_auth_flow()
        return

    creds = get_credentials()

    end_date = date.today() - timedelta(days=1)
    if args.date:
        end_date = date.fromisoformat(args.date)

    today_str = str(date.today())
    dest_dir = DRIVE_BASE / today_str
    dest_dir.mkdir(parents=True, exist_ok=True)

    log_lines = [f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    log_lines.append(f"データ期間: {end_date - timedelta(days=DAYS-1)} 〜 {end_date}")
    log_lines.append("取得結果:")

    # ── GSC ──
    try:
        gsc = fetch_gsc(creds, end_date)
        n_q = write_csv(dest_dir, "queries.csv",  gsc["queries"])
        n_p = write_csv(dest_dir, "pages.csv",    gsc["pages"])
        write_csv(dest_dir, "devices.csv",   gsc["devices"])
        write_csv(dest_dir, "countries.csv", gsc["countries"])
        write_csv(dest_dir, "dates.csv",     gsc["dates"])
        log_lines.append(f"  - Search Console: 成功 (queries: {n_q}行, pages: {n_p}行)")
    except Exception as e:
        log_lines.append(f"  - Search Console: エラー ({e})")

    # ── GA4 ──
    try:
        ga4 = fetch_ga4(creds, end_date)
        write_text(dest_dir, "ga4_traffic.csv", ga4["ga4_traffic"])
        write_text(dest_dir, "ga4_pages.csv",   ga4["ga4_pages"])
        log_lines.append("  - GA4トラフィック: 成功")
        log_lines.append("  - GA4ページ: 成功")
    except Exception as e:
        log_lines.append(f"  - GA4: エラー ({e})")

    log_lines.append("  - SCカバレッジ: スキップ（API未対応のため省略）")
    log_lines.append("  - Ahrefs: Claude MCP経由（別途取得）")

    log_text = "\n".join(log_lines) + "\n"
    (dest_dir / "collection_log.txt").write_text(log_text, encoding="utf-8")

    print(log_text)
    print(f"✅ 保存完了: {dest_dir}")


if __name__ == "__main__":
    main()
