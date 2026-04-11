#!/usr/bin/env python3
"""
フィードバック自動対応スクリプト
Ollama Gemma4で新着フィードバックを分析し、対応方針を生成して記録する。

使い方:
  python3 scripts/auto_feedback.py           # 新着を自動分析・記録
  python3 scripts/auto_feedback.py --dry-run # 分析のみ（Firestoreに書き込まない）

フロー:
  1. Firestoreから未対応フィードバックを取得
  2. Gemma4で各フィードバックを分析（緊急度・対応方針・推奨アクション）
  3. 分析結果をFirestoreに書き込み（analysisフィールド）
  4. macOS通知でサマリーを送信
"""
import sys
import os
import json
import subprocess
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
KEY_PATH = os.path.join(PROJECT_ROOT, "service-account-key.json")
REPORT_DIR = os.path.join(PROJECT_ROOT, "feedback-reports")

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

OLLAMA_MODEL = "gemma4:latest"


def fetch_unprocessed():
    """未分析のフィードバックを取得"""
    ref = db.collection("feedback").order_by("createdAt", direction=firestore.Query.DESCENDING)
    items = []
    for doc in ref.stream():
        d = doc.to_dict()
        d["id"] = doc.id
        # resolved済み or 既に分析済みならスキップ
        if d.get("resolved") or d.get("analysis"):
            continue
        items.append(d)
    return items


def analyze_with_gemma(item):
    """Gemma4でフィードバックを分析"""
    cat = CATEGORY_LABELS.get(item.get("category", "other"), "その他")
    page = item.get("page", "不明")
    detail = item.get("detail", "")
    ua = item.get("userAgent", "")

    device = "不明"
    if "iPhone" in ua:
        device = "iPhone"
    elif "Android" in ua:
        device = "Android"
    elif "Mac" in ua:
        device = "Mac"
    elif "Windows" in ua:
        device = "Windows"

    prompt = f"""あなたはnative-real.comの運営チームのサポートAIです。
ユーザーから以下のフィードバックが届きました。分析して対応方針を日本語で出してください。

【カテゴリ】{cat}
【該当ページ】{page}
【デバイス】{device}
【報告内容】{detail}

以下のJSON形式のみ回答してください。"""

    import urllib.request
    req_body = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": {
            "type": "object",
            "properties": {
                "urgency": {"type": "string", "enum": ["high", "medium", "low"]},
                "summary": {"type": "string"},
                "root_cause": {"type": "string"},
                "action": {"type": "string"},
                "affected_file": {"type": "string"},
                "auto_resolvable": {"type": "boolean"}
            },
            "required": ["urgency", "summary", "root_cause", "action", "affected_file", "auto_resolvable"]
        },
        "stream": False
    })
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=req_body.encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            output = result.get("response", "")
            return json.loads(output)
    except Exception:
        pass

    return {
        "urgency": "medium",
        "summary": detail[:80],
        "root_cause": "自動分析失敗 — 手動確認が必要",
        "action": "手動で確認してください",
        "affected_file": "",
        "auto_resolvable": False
    }


def save_analysis(doc_id, analysis):
    """分析結果をFirestoreに保存"""
    db.collection("feedback").document(doc_id).update({
        "analysis": analysis,
        "analyzedAt": firestore.SERVER_TIMESTAMP,
    })


def mark_resolved(doc_id):
    db.collection("feedback").document(doc_id).update({
        "resolved": True,
        "resolvedAt": firestore.SERVER_TIMESTAMP,
    })


def generate_report(items_with_analysis):
    """分析結果をMarkdownレポートとして保存"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(REPORT_DIR, f"report_{now}.md")

    lines = [
        f"# フィードバックレポート {now}",
        f"",
        f"件数: {len(items_with_analysis)}",
        f"",
    ]

    urgency_order = {"high": 0, "medium": 1, "low": 2}
    sorted_items = sorted(
        items_with_analysis,
        key=lambda x: urgency_order.get(x["analysis"].get("urgency", "medium"), 1)
    )

    for i, item in enumerate(sorted_items, 1):
        a = item["analysis"]
        cat = CATEGORY_LABELS.get(item.get("category", "other"), "その他")
        urgency = a.get("urgency", "medium")
        urgency_label = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}.get(urgency, urgency)

        lines.append(f"## {i}. [{urgency_label}] {a.get('summary', '不明')}")
        lines.append(f"")
        lines.append(f"- **ID**: `{item['id']}`")
        lines.append(f"- **カテゴリ**: {cat}")
        if item.get("page"):
            lines.append(f"- **ページ**: {item['page']}")
        lines.append(f"- **推定原因**: {a.get('root_cause', '不明')}")
        lines.append(f"- **推奨アクション**: {a.get('action', '手動確認')}")
        if a.get("affected_file"):
            lines.append(f"- **対象ファイル**: `{a['affected_file']}`")
        lines.append(f"- **自動対応可能**: {'はい' if a.get('auto_resolvable') else 'いいえ'}")
        lines.append(f"")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    return path


def notify(title, body):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{body}" with title "{title}" sound name "Glass"'
    ])


def main():
    dry_run = "--dry-run" in sys.argv

    items = fetch_unprocessed()
    if not items:
        print("  新着フィードバックはありません。")
        return

    print(f"  {len(items)}件の未分析フィードバックを処理します...\n")

    processed = []
    for item in items:
        doc_id = item["id"]
        cat = CATEGORY_LABELS.get(item.get("category", "other"), "その他")
        print(f"  分析中: [{cat}] {item.get('detail', '')[:50]}...")

        analysis = analyze_with_gemma(item)
        item["analysis"] = analysis

        urgency = analysis.get("urgency", "medium")
        print(f"    → 緊急度: {urgency}")
        print(f"    → 要約: {analysis.get('summary', '')}")
        print(f"    → 対応: {analysis.get('action', '')}")
        print()

        if not dry_run:
            save_analysis(doc_id, analysis)

            # lowかつ自動対応不可なら自動でresolved（ノイズ削減）
            # high/mediumは手動対応のため残す
            if urgency == "low" and not analysis.get("auto_resolvable"):
                mark_resolved(doc_id)
                print(f"    → 自動で対応済みにしました（low + 対応不要）")

        processed.append(item)

    # レポート生成
    if processed:
        report_path = generate_report(processed)
        print(f"  レポート保存: {report_path}")

        # 通知
        high_count = sum(1 for p in processed if p["analysis"].get("urgency") == "high")
        med_count = sum(1 for p in processed if p["analysis"].get("urgency") == "medium")
        summary_parts = []
        if high_count:
            summary_parts.append(f"緊急{high_count}件")
        if med_count:
            summary_parts.append(f"要対応{med_count}件")
        summary_parts.append(f"計{len(processed)}件")
        notify(
            "native-real フィードバック分析完了",
            "、".join(summary_parts) + f" → {os.path.basename(report_path)}"
        )


if __name__ == "__main__":
    main()
