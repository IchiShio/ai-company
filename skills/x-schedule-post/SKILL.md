---
name: x-schedule-post
description: >
  Xの予約投稿スキル。投稿テキストを受け取り、schedule.jsonに書き込む（@ichi_eigo）。
  「X投稿して」「予約投稿して」「ポストして」「ツイートして」「予約して」
  「次の空き枠に入れて」などのフレーズ、または投稿テキストを渡されて投稿を
  頼まれたとき、X投稿の作成フロー後に「投稿して」と言われたときに使う。
---

# X 予約投稿スキル

## アカウント別の投稿方式

| アカウント | 投稿方式 | 投稿枠 |
|---|---|---|
| @ichi_eigo | **GitHub Actions + schedule.json**（自動）| 7:00 / 12:00 / 18:00 / 21:00 JST |

---

## @ichi_eigo の予約投稿（schedule.json方式）

GitHub Actionsが毎日 7:00 / 18:00 JSTに `schedule.json` を読んで自動投稿する。
**Playwright不要。schedule.jsonに書くだけで完結。**

### 仕組み

```
schedule.json に posted: false のエントリを追加
    ↓
GitHub Actions cron（UTC 22:00 / 9:00 = JST 7:00 / 18:00）が起動
    ↓
pick_scheduled_post.py: 当日・当該枠のエントリを選択
    ↓
post_tweet_ga.py: X API v2 で投稿
    ↓
mark_posted.py: posted: true に更新してコミット
```

### Step 1: schedule.json の空き枠を確認

```bash
TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M'
cat ~/projects/claude/ai-company/x-knowledge/posts/schedule.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
pending = [p for p in data if not p.get('posted', False)]
for p in sorted(pending, key=lambda x: (x['date'], x['slot'])):
    print(p['date'], p['slot'], p['text'][:30])
"
```

現在時刻から次の空き枠を判定:
- 現在が 7:00 より前 → 今日の morning
- 現在が 7:00〜12:00 の間 → 今日の noon
- 現在が 12:00〜18:00 の間 → 今日の evening
- 現在が 18:00〜21:00 の間 → 今日の night
- 現在が 21:00 以降 → 明日の morning

すでにその日・枠のエントリがある場合は次の枠へ。

### Step 2: schedule.json に追記

`~/projects/claude/ai-company/x-knowledge/posts/schedule.json` を読み込み、末尾に追記:

```json
{
  "date": "YYYY-MM-DD",
  "slot": "morning",
  "text": "投稿テキスト（改行は\\nで記述）",
  "posted": false,
  "fact_ref": "facts/{カテゴリ}/{ID}（わかる場合）",
  "hook_pattern": "P7",
  "theme": "テーマ名"
}
```

**slot の値**:
- `"morning"` → 7:00 JST
- `"noon"` → 12:00 JST
- `"evening"` → 18:00 JST
- `"night"` → 21:00 JST

### Step 3: コミット＆プッシュ

```bash
cd ~/projects/claude/ai-company && git add x-knowledge/posts/schedule.json && git commit -m "投稿予約: YYYY-MM-DD {morning/evening} - テーマ名" && git push origin main
```

### Step 4: 完了報告

```
✅ 予約完了（GitHub Actions自動投稿）
アカウント: @ichi_eigo
投稿予定: 〇月〇日(曜) 〇:〇〇 JST
本文冒頭: 「〇〇〇...」

GitHub Actionsが自動で投稿します。schedule.jsonにposted: falseで登録済み。
```

---

## 注意事項

- schedule.json の `text` フィールドの改行は `\n` で記述
- `posted: false` を必ず設定すること（`true` にすると投稿されない）
- 同じ日・枠のエントリが既にある場合は追加しない（ダブル投稿防止）
- コミット後は必ずpushすること（pushしないとGitHub Actionsが読めない）

---

## Playwright CLI（pw）コマンド対応表

| 操作 | pw コマンド |
|------|------------------------|
| セッション状態確認 | `pw -s careermigaki sessions` |
| URL移動 | `pw -s careermigaki open "URL"` |
| スクリーンショット | `pw -s careermigaki screenshot` |
| クリック | `pw -s careermigaki click INDEX` |
| テキスト入力（type） | `pw -s careermigaki type "text"` |
| フォーム入力 | `pw -s careermigaki input INDEX "text"` |
| ページ状態確認 | `pw -s careermigaki state` |
| JS実行 | `pw -s careermigaki eval "JS"` |
