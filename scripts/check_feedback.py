#!/usr/bin/env python3
"""
フィードバック確認スクリプト
Firestoreのfeedbackコレクションを取得し、対応方針付きで整理して表示する。

使い方:
  python3 scripts/check_feedback.py           # 未対応のみ表示
  python3 scripts/check_feedback.py --all     # すべて表示
  python3 scripts/check_feedback.py --mark ID # 指定IDを対応済みにする
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトルートを基準にサービスアカウントキーを参照
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
KEY_PATH = os.path.join(PROJECT_ROOT, "service-account-key.json")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(KEY_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

CATEGORY_LABELS = {
    "bug": "不具合・エラー",
    "content": "コンテンツの誤り",
    "suggestion": "機能の提案",
    "other": "その他",
}

CATEGORY_PRIORITY = {
    "bug": 1,
    "content": 2,
    "suggestion": 3,
    "other": 4,
}

ACTION_HINTS = {
    "bug": "調査 → 再現確認 → 修正 → デプロイ",
    "content": "該当コンテンツを確認 → 修正 → デプロイ",
    "suggestion": "検討 → 採用/保留/見送りを判断",
    "other": "内容を確認して分類",
}


def fetch_feedback(show_all=False):
    ref = db.collection("feedback").order_by("createdAt", direction=firestore.Query.DESCENDING)
    docs = ref.stream()
    items = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        if not show_all and d.get("resolved"):
            continue
        items.append(d)
    return items


def mark_resolved(doc_id):
    db.collection("feedback").document(doc_id).update({
        "resolved": True,
        "resolvedAt": firestore.SERVER_TIMESTAMP,
    })
    print(f"  [{doc_id}] を対応済みにしました。")


def display(items):
    if not items:
        print("\n  報告はありません。\n")
        return

    # カテゴリ別にグループ化
    grouped = {}
    for item in items:
        cat = item.get("category", "other")
        grouped.setdefault(cat, []).append(item)

    # 優先度順に表示
    sorted_cats = sorted(grouped.keys(), key=lambda c: CATEGORY_PRIORITY.get(c, 99))

    total = len(items)
    print(f"\n{'='*60}")
    print(f"  フィードバック一覧  ({total}件)")
    print(f"{'='*60}")

    for cat in sorted_cats:
        cat_items = grouped[cat]
        label = CATEGORY_LABELS.get(cat, cat)
        action = ACTION_HINTS.get(cat, "確認")
        print(f"\n  [{label}] — {len(cat_items)}件")
        print(f"  対応方針: {action}")
        print(f"  {'-'*50}")

        for i, item in enumerate(cat_items, 1):
            created = item.get("createdAt")
            if created:
                ts = created.strftime("%Y-%m-%d %H:%M") if hasattr(created, "strftime") else str(created)
            else:
                ts = "日時不明"

            resolved = " [対応済]" if item.get("resolved") else ""
            page = item.get("page", "")
            detail = item.get("detail", "")
            email = item.get("email", "")
            ua = item.get("userAgent", "")
            doc_id = item.get("id", "")

            # UA から簡易デバイス情報を抽出
            device = "不明"
            if "iPhone" in ua:
                device = "iPhone"
            elif "Android" in ua:
                device = "Android"
            elif "Mac" in ua:
                device = "Mac"
            elif "Windows" in ua:
                device = "Windows"

            print(f"\n  {i}. {ts}{resolved}")
            print(f"     ID: {doc_id}")
            if page:
                print(f"     ページ: {page}")
            print(f"     内容: {detail}")
            print(f"     デバイス: {device}")
            if email:
                print(f"     連絡先: {email}")

    print(f"\n{'='*60}")
    print(f"  対応済みにする: python3 scripts/check_feedback.py --mark <ID>")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--mark" in args:
        idx = args.index("--mark")
        if idx + 1 < len(args):
            mark_resolved(args[idx + 1])
        else:
            print("  エラー: --mark の後にドキュメントIDを指定してください")
        sys.exit(0)

    show_all = "--all" in args
    items = fetch_feedback(show_all=show_all)
    display(items)
