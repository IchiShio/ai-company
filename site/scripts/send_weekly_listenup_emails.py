#!/usr/bin/env python3
"""
send_weekly_listenup_emails.py
毎週月曜日にMailerLite購読者へ弱点axisに基づいたパーソナライズメールを送信する。

必要な環境変数:
  MAILERLITE_API_KEY  - MailerLite API キー
  RESEND_API_KEY      - Resend API キー
  FROM_EMAIL          - 送信元メールアドレス（例: listenup@native-real.com）
                        ※ Resendでドメイン認証済みのアドレスを使用すること

実行:
  python3 scripts/send_weekly_listenup_emails.py
  python3 scripts/send_weekly_listenup_emails.py --dry-run  # 送信せずに確認
"""

import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"

ML_GROUP_ID = "183233023152489636"
SITE_URL = "https://native-real.com"

AXIS_LABELS = {
    "speed": "速度",
    "reduction": "音変化",
    "vocab": "語彙",
    "context": "文脈",
    "distractor": "識別",
}

AXIS_DESC = {
    "speed": "早口・崩れた発音が聞き取りにくい傾向があります。",
    "reduction": "gonna/wanna などの音変化に慣れると一気に伸びます。",
    "vocab": "イディオムや低頻度語の語彙を増やすことが鍵です。",
    "context": "文脈から意図を読み取る練習が最も効果的です。",
    "distractor": "紛らわしい選択肢を見分ける精度を上げましょう。",
}


# ─────────────────────────────────────────
# questions.js パーサー
# ─────────────────────────────────────────

def parse_questions_by_axis():
    """questions.js から axis ごとの問題リストを返す"""
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    questions_by_axis = {ax: [] for ax in AXIS_LABELS}

    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("{"):
            continue

        q = {}

        m = re.search(r'\baxis:\s*"([^"]+)"', line)
        if m:
            q["axis"] = m.group(1)

        m = re.search(r'\btext:\s*"((?:[^"\\]|\\.)*)"', line)
        if m:
            q["text"] = m.group(1).replace('\\"', '"').replace("\\n", " ")

        m = re.search(r'\bja:\s*"((?:[^"\\]|\\.)*)"', line)
        if m:
            q["ja"] = m.group(1).replace('\\"', '"')

        m = re.search(r'\bkp:\s*(\[[^\]]+\])', line)
        if m:
            try:
                q["kp"] = json.loads(m.group(1))
            except Exception:
                q["kp"] = []

        m = re.search(r'\bdiff:\s*"([^"]+)"', line)
        if m:
            q["diff"] = m.group(1)

        if "axis" in q and "text" in q and q["axis"] in questions_by_axis:
            questions_by_axis[q["axis"]].append(q)

    return questions_by_axis


# ─────────────────────────────────────────
# MailerLite API
# ─────────────────────────────────────────

def fetch_subscribers(api_key, group_id):
    """MailerLite からアクティブな購読者一覧を取得"""
    subscribers = []
    cursor = None

    while True:
        url = f"https://connect.mailerlite.com/api/subscribers?filter[status]=active&filter[group_id]={group_id}&limit=100"
        if cursor:
            url += f"&cursor={cursor}"

        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"ERROR: MailerLite API 失敗: {e}", file=sys.stderr)
            break

        for sub in data.get("data", []):
            email = sub.get("email", "")
            fields = sub.get("fields", {}) or {}
            weak_axis = fields.get("weak_axis", "") or ""
            total_answered = fields.get("total_answered", 0) or 0
            sub_id = sub.get("id", "")

            if email:
                subscribers.append({
                    "id": sub_id,
                    "email": email,
                    "weak_axis": weak_axis if weak_axis in AXIS_LABELS else "",
                    "total_answered": int(total_answered) if str(total_answered).isdigit() else 0,
                })

        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return subscribers


# ─────────────────────────────────────────
# メールテンプレート生成
# ─────────────────────────────────────────

def build_question_html(q, idx):
    kp_chips = "".join(
        f'<span style="display:inline-block;background:#EEF2FF;color:#3730A3;'
        f'font-size:11px;padding:3px 8px;border-radius:20px;margin:2px 2px 0 0;">'
        f'{kp}</span>'
        for kp in (q.get("kp") or [])[:3]
    )
    diff_map = {"lv1": "★☆☆☆☆", "lv2": "★★☆☆☆", "lv3": "★★★☆☆", "lv4": "★★★★☆", "lv5": "★★★★★"}
    diff_stars = diff_map.get(q.get("diff", ""), "")

    return f"""
    <div style="background:#f8f9fa;border-radius:12px;padding:14px 16px;margin-bottom:12px;border-left:3px solid #2563EB;">
      <div style="font-size:10px;color:#aaa;margin-bottom:4px;">{idx}問目 {diff_stars}</div>
      <div style="font-size:14px;font-weight:600;color:#111;margin-bottom:4px;line-height:1.5;">{q['text']}</div>
      <div style="font-size:12px;color:#666;margin-bottom:8px;">{q.get('ja', '')}</div>
      {f'<div>{kp_chips}</div>' if kp_chips else ''}
    </div>"""


def build_email_html(subscriber, questions, week_label):
    axis = subscriber.get("weak_axis") or "context"
    axis_label = AXIS_LABELS.get(axis, "")
    axis_desc = AXIS_DESC.get(axis, "")
    total = subscriber.get("total_answered", 0)
    week_mode_url = f"{SITE_URL}/listening/?mode=weak"

    questions_html = "".join(
        build_question_html(q, i + 1) for i, q in enumerate(questions)
    )

    total_section = ""
    if total > 0:
        total_section = f'<div style="font-size:12px;color:#888;margin-bottom:16px;">累計 {total} 問解いています</div>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif;">
  <div style="max-width:480px;margin:24px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- ヘッダー -->
    <div style="background:#1e40af;padding:20px 24px 18px;">
      <div style="font-size:11px;color:rgba(255,255,255,0.6);letter-spacing:0.5px;margin-bottom:4px;">ListenUp 週次レポート · {week_label}</div>
      <div style="font-size:20px;font-weight:800;color:#fff;">今週の<span style="color:#fbbf24;">{axis_label}</span>対策</div>
      <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:6px;">{axis_desc}</div>
    </div>

    <!-- コンテンツ -->
    <div style="padding:20px 24px;">
      {total_section}

      <div style="font-size:12px;font-weight:700;color:#888;letter-spacing:0.5px;margin-bottom:12px;">今週の練習フレーズ</div>

      {questions_html}

      <!-- CTA -->
      <div style="text-align:center;margin:24px 0 8px;">
        <a href="{week_mode_url}"
           style="display:inline-block;background:#2563EB;color:#fff;padding:14px 32px;
                  border-radius:10px;font-size:15px;font-weight:700;text-decoration:none;
                  letter-spacing:0.3px;">
          弱点集中モードで練習する →
        </a>
        <div style="font-size:11px;color:#aaa;margin-top:8px;">クリックするとすぐ弱点問題が始まります</div>
      </div>
    </div>

    <!-- フッター -->
    <div style="padding:16px 24px;border-top:1px solid #f0f0f0;text-align:center;">
      <div style="font-size:11px;color:#bbb;line-height:1.8;">
        このメールは <a href="{SITE_URL}/listening/" style="color:#6b7280;">native-real.com/listening/</a> で<br>
        メールアドレスを登録した方にお送りしています。<br>
        <a href="{{{{unsubscribe_url}}}}" style="color:#9ca3af;">配信停止はこちら</a>
      </div>
    </div>
  </div>
</body>
</html>"""


# ─────────────────────────────────────────
# Resend API
# ─────────────────────────────────────────

def send_email_resend(api_key, from_email, to_email, subject, html_body):
    """Resend API でメールを1通送信する"""
    payload = json.dumps({
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "headers": {
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return True, result.get("id", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    ml_api_key = os.environ.get("MAILERLITE_API_KEY", "")
    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    from_email = os.environ.get("FROM_EMAIL", "ListenUp <listenup@native-real.com>")

    if not ml_api_key:
        print("ERROR: MAILERLITE_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)
    if not resend_api_key and not dry_run:
        print("ERROR: RESEND_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    # 今週の日付ラベル
    import datetime
    today = datetime.date.today()
    week_label = f"{today.month}月{today.day}日週"

    print("=== ListenUp 週次メール送信 ===")
    print(f"日付: {today} | dry_run: {dry_run}")

    # 問題データ読み込み
    print("\n[1/3] 問題データ読み込み中...")
    questions_by_axis = parse_questions_by_axis()
    for ax, qs in questions_by_axis.items():
        print(f"  {ax}: {len(qs)}問")

    # 購読者取得
    print("\n[2/3] MailerLite 購読者取得中...")
    subscribers = fetch_subscribers(ml_api_key, ML_GROUP_ID)
    print(f"  アクティブ購読者: {len(subscribers)}人")

    if not subscribers:
        print("  購読者なし。終了します。")
        return

    # 購読者ごとにメール送信
    print(f"\n[3/3] メール送信 ({'' if not dry_run else 'dry-run'})...")
    sent_ok = 0
    sent_ng = 0

    for sub in subscribers:
        email = sub["email"]
        weak_axis = sub.get("weak_axis") or "context"  # 弱点未設定はcontextをデフォルトに

        # axisに応じた問題を3問サンプリング
        pool = questions_by_axis.get(weak_axis, [])
        if not pool:
            pool = sum(questions_by_axis.values(), [])  # fallback: 全問題
        sample = random.sample(pool, min(3, len(pool)))

        # 件名
        axis_label = AXIS_LABELS.get(weak_axis, weak_axis)
        subject = f"今週のあなた専用練習（{axis_label}弱点対策）| ListenUp"

        # HTML生成
        html_body = build_email_html(sub, sample, week_label)

        if dry_run:
            print(f"  [DRY] {email} → {axis_label}({weak_axis}) {len(sample)}問")
            continue

        ok, result = send_email_resend(resend_api_key, from_email, email, subject, html_body)
        if ok:
            print(f"  ✅ {email} → {axis_label} (id: {result})")
            sent_ok += 1
        else:
            print(f"  ❌ {email} → 失敗: {result}", file=sys.stderr)
            sent_ng += 1

        time.sleep(0.3)  # レート制限対策

    if not dry_run:
        print(f"\n完了: 成功={sent_ok} 失敗={sent_ng}")


if __name__ == "__main__":
    main()
