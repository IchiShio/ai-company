---
name: x-schedule-post
description: >
  Xの予約投稿スキル。投稿テキストを受け取り、schedule.jsonに書き込む（@ichi_eigo）か
  Playwright CLIで予約投稿する（@careermigaki）。
  「X投稿して」「予約投稿して」「ポストして」「ツイートして」「予約して」
  「次の空き枠に入れて」などのフレーズ、または投稿テキストを渡されて投稿を
  頼まれたとき、X投稿の作成フロー後に「投稿して」と言われたときに使う。
---

# X 予約投稿スキル

## アカウント別の投稿方式

| アカウント | 投稿方式 | 投稿枠 |
|---|---|---|
| @ichi_eigo | **GitHub Actions + schedule.json**（自動）| 7:00 / 18:00 JST |
| @careermigaki | **Playwright CLI**（ブラウザ操作）| 7:30 / 18:30 JST |

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
- 現在が 7:00〜18:00 の間 → 今日の evening
- 現在が 18:00 以降 → 明日の morning

すでにその日・枠のエントリがある場合は次の枠へ。

### Step 2: ユーザーに確認

```
「**〇月〇日(曜) 〇:〇〇 JST** に @ichi_eigo で投稿します。よろしいですか？」
```

ユーザーが承認するまで待つ。

### Step 3: schedule.json に追記

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
- `"evening"` → 18:00 JST

### Step 4: コミット＆プッシュ

```bash
cd ~/projects/claude/ai-company && git add x-knowledge/posts/schedule.json && git commit -m "投稿予約: YYYY-MM-DD {morning/evening} - テーマ名" && git push origin main
```

### Step 5: 完了報告

```
✅ 予約完了（GitHub Actions自動投稿）
アカウント: @ichi_eigo
投稿予定: 〇月〇日(曜) 〇:〇〇 JST
本文冒頭: 「〇〇〇...」

GitHub Actionsが自動で投稿します。schedule.jsonにposted: falseで登録済み。
```

---

## @careermigaki の予約投稿（Playwright方式）

Playwright CLI（`pw -s careermigaki`）でブラウザを操作して予約投稿する。

### 前提条件

- `pw -s careermigaki` セッションが起動済みでXにログイン済みであること

### ワークフロー

#### Step 0: 準備（並列実行）

**A. 現在時刻の取得**
```bash
TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M %A'
```

**B. ブラウザの準備**
1. `pw -s careermigaki sessions` でセッション状態を確認
2. `x.com` が開いていない場合は `pw -s careermigaki open "https://x.com/home"` で移動
3. `pw -s careermigaki screenshot` でアカウント名を確認

#### Step 1: アカウントの切り替え（必要な場合のみ）

左サイドバー最下部のアカウント名を確認。対象アカウントでない場合:
1. アカウント名の右の「…」をクリック
2. メニューから @careermigaki を選択

#### Step 2: 予約済み枠の確認（⚠️ テキスト入力より先に行う）

**重要**: テキストを入力する前に予約済み一覧を確認すること。

1. 「ポストする」ボタンをクリック → 空の投稿作成モーダルが開く
2. モーダル右上の「下書き」をクリック
3. 「予約済み」タブをクリック → 予約済み一覧を確認
4. `pw -s careermigaki screenshot` で日時を確認

空き枠の判定（@careermigaki）:
- 現在が 7:30 より前 → 今日の 7:30
- 現在が 7:30〜18:30 の間 → 今日の 18:30
- 現在が 18:30 以降 → 明日の 7:30

候補の枠がすでに予約済みなら次の枠へ。

ユーザーに確認:
```
「**〇月〇日(曜) 〇:〇〇 JST** に @careermigaki で予約します。よろしいですか？」
```

#### Step 3: 投稿テキストの入力

1. `pw -s careermigaki open "https://x.com/compose/post"` で直接ナビゲート
2. `pw -s careermigaki state` でテキストエリアのインデックスを確認
3. `pw -s careermigaki click INDEX` でフォーカス
4. `pw -s careermigaki input INDEX "投稿テキスト"` で入力

テキスト検証（必須）:
```
pw -s careermigaki eval "const editor = document.querySelector('[data-testid=\"tweetTextarea_0\"]'); JSON.stringify(editor ? editor.innerText : 'not found');"
```

全行が揃っているか確認。最初の行が欠けていた場合は `type` で補完。

#### Step 4: スケジュールを設定する

1. `pw -s careermigaki state` でスケジュールアイコン（カレンダー+時計）のインデックスを確認してクリック
2. `pw -s careermigaki state` で月/日/年/時/分のドロップダウンのインデックスを確認（**設定直前に毎回取得すること**）
3. 各ドロップダウンに値を設定:
   - 月: `pw -s careermigaki input INDEX "4"`
   - 日: `pw -s careermigaki input INDEX "15"`
   - 時: `pw -s careermigaki input INDEX "18"`（24時間表記）
   - 分: `pw -s careermigaki input INDEX "30"`
4. `pw -s careermigaki screenshot` でタイムゾーンが「日本標準時」であることを確認

#### Step 5: 予約を確定する（2段階）

1. `pw -s careermigaki state` で「確認する」ボタンを確認してクリック → 投稿作成画面に戻る
2. `pw -s careermigaki screenshot` で「〇年〇月〇日(曜)の午前/午後〇:〇〇に送信されます」を確認
3. 「予約設定」ボタンをクリック → 予約済み一覧に遷移で完了

#### Step 6: 完了報告

```
✅ 予約完了
アカウント: @careermigaki
日時: 〇月〇日(曜) 〇:〇〇 JST
本文冒頭: 「〇〇〇...」
```

---

## 注意事項

### @ichi_eigo 共通
- schedule.json の `text` フィールドの改行は `\n` で記述
- `posted: false` を必ず設定すること（`true` にすると投稿されない）
- 同じ日・枠のエントリが既にある場合は追加しない（ダブル投稿防止）
- コミット後は必ずpushすること（pushしないとGitHub Actionsが読めない）

### @careermigaki 共通
- テキスト入力は必ず `/compose/post` への直接ナビゲート後に行う
- 予約済み確認は必ずテキスト入力前に行う
- ドロップダウンのインデックスは設定直前に `state` で再取得する

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
