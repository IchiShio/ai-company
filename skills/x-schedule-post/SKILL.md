---
name: x-schedule-post
description: >
  Xの予約投稿スキル。投稿テキストを受け取り、7:30と18:30の2枠から次の空き枠を
  自動判定し、Playwright CLI（pw）経由でブラウザを操作して予約投稿する。
  @ichi_eigo と @careermigaki の両アカウントに対応。アカウント切り替えも行う。
  「X投稿して」「予約投稿して」「ポストして」「ツイートして」「予約して」
  「次の空き枠に入れて」などのフレーズ、または投稿テキストを渡されて投稿を
  頼まれたとき、X投稿の作成フロー後に「投稿して」と言われたときに使う。
  投稿テキストの生成だけでなく、ブラウザ操作による実際の予約投稿まで行う。
---

# X 予約投稿スキル（Claude Code + Playwright CLI版）

XのWeb UIをPlaywright CLI（pw）経由のブラウザ操作（Chromium）で直接操作し、
指定アカウントの次の空き枠（7:00 or 18:00 JST（@ichi_eigo）/ 7:30 or 18:30 JST（@careermigaki））に予約投稿する。

## 前提条件

- `pw -s ichi-eigo` セッションが起動済みでXにログイン済みであること
  - @ichi_eigo の操作: `pw -s ichi-eigo`
  - @careermigaki の操作: `pw -s careermigaki`
  - @one_ai_company の操作: `pw -s ichi-eigo`（OACはいち英語社の事業のため同セッションを使用）
- タイムゾーンは JST（日本時間）

## 対象アカウント

- `@ichi_eigo`（英語コーチングラボ）— 英語学習系の投稿
- `@careermigaki`（キャリア磨き）— キャリア転職系の投稿

投稿内容から自動判定できる場合はそうする。判断がつかない場合のみユーザーに確認する。

---

## ワークフロー

### Step 0: 準備（並列実行）

以下を**同時に**実行する:

**A. 現在時刻の取得（Bash）**
```bash
TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M %A'
```

**B. ブラウザの準備**
1. `pw -s ichi-eigo sessions` でセッション状態を確認
2. `x.com` が開いていない場合は `pw -s ichi-eigo open "https://x.com/home"` で移動
3. `pw -s ichi-eigo screenshot` でアカウント名（左サイドバー最下部）を確認

→ アカウントが対象と異なる場合はStep 1でアカウント切り替えを行う。

---

### Step 1: アカウントの切り替え（必要な場合のみ）

スクリーンショットで左サイドバー最下部のアカウント名を確認。
対象アカウントでない場合:

1. `pw -s ichi-eigo state` でインデックスを確認し、アカウント名の右の「…」を `pw -s ichi-eigo click INDEX` でクリック
2. メニューから対象アカウントを選択
3. `pw -s ichi-eigo screenshot` で確認

---

### Step 2: 予約済み枠の確認（⚠️ テキスト入力より先に行う）

**重要**: テキストを入力する前に予約済み一覧を確認すること。
テキストがある状態で「下書き」をクリックすると保存ダイアログが出て、無駄な下書きが生まれる。

#### 2-1: 予約済み一覧を開く

1. `pw -s ichi-eigo state` でインデックスを確認し、サイドバーの「ポストする」ボタンを `pw -s ichi-eigo click INDEX` でクリック → **空の**投稿作成モーダルが開く
2. モーダル右上の「下書き」リンクをクリック（この時点でテキストエリアは空なのでダイアログは出ない）
3. 「予約済み」タブをクリック → 予約済み一覧が表示される

#### 2-2: 予約済みの日時を読み取る

1. `pw -s ichi-eigo screenshot` で予約済み投稿の日時を確認
2. 読み取れない場合は `pw -s ichi-eigo state` でページテキストを取得
3. 日時の表示形式: 「2026年3月14日(土)の午前7:34に送信されます」

#### 2-3: 空き枠の判定

Step 0で取得した現在時刻を使って計算:

```
アカウント別の投稿枠:
  - @ichi_eigo:    7:00 / 18:00
  - @careermigaki: 7:30 / 18:30

今日の残り枠を確認（@ichi_eigo の場合）:
  - 現在が 7:00 より前 → 今日の 7:00 が候補
  - 現在が 7:00〜18:00 の間 → 今日の 18:00 が候補
  - 現在が 18:00 以降 → 明日の 7:00 が候補

今日の残り枠を確認（@careermigaki の場合）:
  - 現在が 7:30 より前 → 今日の 7:30 が候補
  - 現在が 7:30〜18:30 の間 → 今日の 18:30 が候補
  - 現在が 18:30 以降 → 明日の 7:30 が候補

候補の枠がすでに予約済みなら次の枠へ（繰り返す）
```

**枠の判定基準**: 予約時刻が枠の前後30分以内 → その枠は埋まっている

#### 2-4: ユーザーに確認して承認を得る

```
「**〇月〇日(曜) 〇:〇〇** に @xxx で予約します。よろしいですか？」
```

ユーザーが承認（「ok」「はい」等）するまで待つ。

#### 2-5: 予約済み画面を閉じる

`pw -s ichi-eigo state` でインデックスを確認し、「←」（戻るボタン）を `pw -s ichi-eigo click INDEX` でクリックしてホーム画面に戻る。
（× で閉じてもOKだが、戻るボタンのほうが確実）

---

### Step 3: 投稿テキストの入力

#### 3-1: 投稿作成画面を開く

`https://x.com/compose/post` に **直接ナビゲート** する。
（ホームページのインライン入力欄は不安定なため使わない）

```
pw -s ichi-eigo open "https://x.com/compose/post"
```

`pw -s ichi-eigo screenshot` で「いまどうしてる？」のモーダルが開いたことを確認。

#### 3-2: テキストを入力する

1. `pw -s ichi-eigo state` でテキストエリア（「いまどうしてる？」）のインデックスを確認し `pw -s ichi-eigo click INDEX` でフォーカス
2. `pw -s ichi-eigo input INDEX "投稿テキスト"` でテキストを入力

#### 3-3: テキスト入力を JavaScript で検証（必須）

```
pw -s ichi-eigo eval "const editor = document.querySelector('[data-testid=\"tweetTextarea_0\"]'); JSON.stringify(editor ? editor.innerText : 'not found');"
```

**確認ポイント**:
- 全行が揃っているか（特に最初の行が抜けていないか）
- 改行が正しく入っているか

もし最初の行が欠けていた場合:
1. テキストエリアをクリック → `pw -s ichi-eigo eval "..."` でカーソルを先頭に移動
2. 欠けている行を `pw -s ichi-eigo type "テキスト"` で入力し改行

---

### Step 4: スケジュールを設定する

#### 4-1: スケジュールアイコンをクリック

- `pw -s ichi-eigo state` でツールバーのスケジュールアイコン（カレンダー+時計）のインデックスを確認し `pw -s ichi-eigo click INDEX` でクリック
- または `pw -s ichi-eigo state` で「ポストを予約」ボタンを探してクリック
- 「予約設定」ダイアログが開く

#### 4-2: 日時を設定する（⚠️ インデックスは設定直前に取得）

**重要**: ドロップダウンのインデックスはページ状態が変わると変わる。
必ず `pw -s ichi-eigo state` で設定直前に最新のインデックスを取得してから設定する。

```
pw -s ichi-eigo state
```

取得したインデックスを使って設定:
- 月のドロップダウン: `pw -s ichi-eigo input INDEX "3"`（デフォルトが正しければスキップ可）
- **日のドロップダウン**: `pw -s ichi-eigo input INDEX "15"`
- 年のドロップダウン: デフォルトが正しければスキップ可
- **時のドロップダウン**: `pw -s ichi-eigo input INDEX "18"`（0〜23 の文字列）
- **分のドロップダウン**: `pw -s ichi-eigo input INDEX "30"`（`"0"`〜`"59"`）

`pw -s ichi-eigo screenshot` でタイムゾーンが「日本標準時」であることを確認。

#### 4-3: 予約を確定する（2段階）

1. `pw -s ichi-eigo state` で「確認する」ボタンのインデックスを確認し `pw -s ichi-eigo click INDEX` でクリック → 投稿作成画面に戻る
2. `pw -s ichi-eigo screenshot` で上部に「〇年〇月〇日(曜)の午前/午後〇:〇〇に送信されます」と青字で表示されることを確認
3. `pw -s ichi-eigo state` で「予約設定」ボタンのインデックスを確認し `pw -s ichi-eigo click INDEX` でクリック
4. 予約済み一覧画面に遷移すれば予約完了

---

### Step 5: 完了報告

`pw -s ichi-eigo screenshot` で予約済み一覧に新しい投稿が追加されたことを確認し、ユーザーに報告:

```
✅ 予約完了
アカウント: @xxx
日時: 〇月〇日(曜) 〇:〇〇 JST
本文冒頭: 「〇〇〇...」
```

---

## 注意事項

- **テキスト入力は必ず `/compose/post` への直接ナビゲート後に行う**（ホームのインライン入力欄は不安定）
- **予約済み確認は必ずテキスト入力前に行う**（下書き保存ループを防ぐ）
- **テキスト入力後は JS で必ず内容を検証する**（最初の行が抜けるバグへの対策）
- **ドロップダウンのインデックスは設定直前に `pw -s ichi-eigo state` で再取得する**（古いインデックスは無効になることがある）
- 各操作の後はUIの反応を待つ（必要に応じて `pw -s ichi-eigo screenshot` で状態確認）
- 想定外のUIの場合は `pw -s ichi-eigo screenshot` で確認して柔軟に対応
- 複数投稿を一度に予約する場合は1件ずつ順番に処理する
- @careermigaki の投稿は `pw -s careermigaki` セッションを使用する

---

## Playwright CLI（pw）コマンド対応表

| 操作 | pw コマンド |
|------|------------------------|
| セッション状態確認 | `pw -s ichi-eigo sessions` |
| URL移動・新しいタブ | `pw -s ichi-eigo open "URL"` |
| スクリーンショット | `pw -s ichi-eigo screenshot` |
| クリック | `pw -s ichi-eigo click INDEX` |
| テキスト入力（type） | `pw -s ichi-eigo type "text"` |
| フォーム入力 | `pw -s ichi-eigo input INDEX "text"` |
| キー操作 / JS実行 | `pw -s ichi-eigo eval "JS"` |
| インデックス探索・ページ状態 | `pw -s ichi-eigo state` |
| JS実行 | `pw -s ichi-eigo eval "JS"` |

**セッション使い分け**:
- `@ichi_eigo`（英語コーチングラボ）: `pw -s ichi-eigo`
- `@careermigaki`（キャリア磨き）: `pw -s careermigaki`
- `@one_ai_company`（OAC、いち英語社の事業）: `pw -s ichi-eigo`

---

## UIのヒント（2026年3月時点で確認済み）

- **投稿ボタン（ポストする）**: 左サイドバー下部、青いボタン
- **アカウント表示**: 左サイドバー最下部（例: 「いち英語 @ichi_eigo」）
- **アカウント切り替え**: アカウント名の右の「…」→ メニューからアカウント選択
- **投稿モーダルURL**: `https://x.com/compose/post` に直接ナビゲートで開く
- **テキストエリアのセレクタ**: `[data-testid="tweetTextarea_0"]`
- **ツールバー（左→右）**: 画像, GIF, リンク, リスト, 絵文字, スケジュール, 位置情報, 旗, 太字, 斜体
- **下書き/予約済み**: モーダル右上「下書き」→「未送信ポスト」と「予約済み」タブ
- **予約投稿の日時形式**: 「2026年3月14日(土)の午前7:34に送信されます」
- **予約設定画面**: 月/日/年のドロップダウン + 時/分のドロップダウン（24時間表記）+ タイムゾーン表示
- **予約確定フロー**: 「確認する」→ 投稿画面に戻る → 「予約設定」ボタンで確定
