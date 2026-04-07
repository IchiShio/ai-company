---
name: note-publisher
description: |
  note.com への記事投稿を全自動化するスキル。
  Playwright CLI（pw）経由でブラウザを操作し、
  記事の作成・本文入力・画像アップロード・公開設定・公開を一貫実行する。
  checker PASS 済みなら承認不要で自動公開まで完了する。

  次のような依頼で使用すること：
  - 「noteに記事を投稿して」「noteに公開して」
  - 「note記事をアップして」「noteにデプロイして」
  - パイプラインの公開ステップとして自動呼び出し
---

# note 記事投稿スキル（Claude Code + Playwright CLI版）

note.com のWeb UIを Playwright CLI（pw）経由のブラウザ操作で直接操作し、
記事の作成・本文入力・画像アップロード・公開設定・公開までを**全自動**実行する。
ユーザー（社長）の工数はゼロ。

## 前提条件

- 対象アカウントの pw セッションが起動済みで note.com にログイン済みであること
- 投稿する記事のコンテンツ（タイトル・本文・画像パス）が準備済みであること
- 品質検査（checker）が PASS 済みであること

## 対象アカウント・セッション対応表

| 会社 | noteアカウント | pw セッション | checker | 備考 |
|---|---|---|---|---|
| いち英語社 | @one_ai_company | `pw -s ichi-eigo` | cso-native-real | native-real ブランド |

**セッション変数**: 以降のワークフローでは `SESSION` と表記する。
- いち英語社の場合: `SESSION=ichi-eigo`

---

## 自動公開ルール

| 条件 | 動作 |
|---|---|
| checker PASS 済み | **承認不要で自動公開** |
| checker 未実施 or FAIL | 公開せず、部長にエスカレーション |
| 有料記事（価格あり） | 自動公開（checker PASSが前提） |

社長の工数ゼロを実現するため、checker が PASS した記事は自動で公開まで完了する。

---

## ワークフロー

### Step 0: 入力の確認とアカウント判定

スキル呼び出し時に以下を確認:

| 項目 | 必須 | 説明 |
|---|---|---|
| タイトル | YES | 記事のタイトル |
| 本文 | YES | 記事本文（プレーンテキスト or マークダウン） |
| 対象会社 | YES | `ichi-eigo`（いち英語社） |
| ヘッダー画像パス | NO | ヘッダーに設定する画像ファイルのパス |
| 本文中画像パス | NO | 本文に挿入する画像ファイルのパス（複数可） |
| 価格 | NO | 有料記事の場合の価格（例: 3980）。未指定なら無料記事 |
| 有料ライン位置 | NO | 有料記事の場合、無料部分と有料部分の境界テキスト |
| ハッシュタグ | NO | 記事に付けるタグ（複数可） |
| checker結果 | YES | PASS/FAIL。PASSでなければ公開しない |

**アカウント**: `SESSION=ichi-eigo`（固定）

---

### Step 1: 準備（並列実行）

以下を**同時に**実行する:

**A. 現在時刻の取得**
```bash
TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M %A'
```

**B. ブラウザの準備**
1. `pw -s SESSION sessions` でセッション状態を確認
2. note.com が開いていない場合は `pw -s SESSION open "https://note.com/dashboard"` で移動
3. `pw -s SESSION screenshot` でログイン状態とアカウント名を確認

→ ログインしていない場合はユーザーに報告して中断。
→ **アカウント名が対象と一致することを必ず確認**（誤投稿防止）。

**C. 画像の準備（画像パスが指定されている場合）**
```bash
# 画像をBase64エンコード（後の画像アップロードで使用）
base64 -i /path/to/header.png | tr -d '\n' > /tmp/note-header-b64.txt
```

---

### Step 2: 新規記事の作成画面を開く

```bash
pw -s SESSION open "https://note.com/notes/new"
```

`pw -s SESSION screenshot` で記事エディタが開いたことを確認。

---

### Step 3: タイトルの入力

1. `pw -s SESSION state` でタイトル入力欄のインデックスを確認
2. タイトル入力欄をクリック:
   ```bash
   pw -s SESSION click INDEX
   ```
3. タイトルを入力:
   ```bash
   pw -s SESSION type "記事タイトル"
   ```
4. `pw -s SESSION screenshot` で入力を確認

---

### Step 4: 本文の入力

note.com のエディタはブロック型リッチテキストエディタ。

#### 4-1: 本文エリアにフォーカス

1. `pw -s SESSION state` で本文エリアのインデックスを確認
2. 本文エリアをクリック:
   ```bash
   pw -s SESSION click INDEX
   ```

#### 4-2: テキストを段落ごとに入力

本文を段落単位で分割し、1段落ずつ入力する:

```bash
pw -s SESSION type "第1段落のテキスト"
```

段落間の改行:
```bash
pw -s SESSION eval "document.execCommand('insertParagraph')"
```

**重要**:
- 1度に大量のテキストを入力するとエディタが不安定になる可能性がある
- 段落ごとに区切って入力し、適宜 `screenshot` で確認する
- 見出し（h2/h3）はエディタのツールバーから設定する

#### 4-3: 見出しの設定

見出しにしたいテキストを入力後:
1. そのテキストを選択（ダブルクリックまたは eval で選択）
2. ツールバーから見出しレベルを選択

#### 4-4: 入力内容の検証

```bash
pw -s SESSION screenshot
```

全体を確認。長い記事の場合はスクロールして複数回スクリーンショットを取る。

---

### Step 5: 画像のアップロード

#### 5-1: ヘッダー画像（みだし画像）

1. `pw -s SESSION state` でエディタ上部の画像追加エリア（みだし画像の設定）を確認
2. 画像追加ボタンをクリック
3. ファイルアップロードの処理（3段階フォールバック）:

**方法A: Base64分割チャンク送信（実証済み・推奨）**

Base64エンコードした画像を80KBずつブラウザに送り、結合してファイルインプットに設定する。

```bash
# Step 1: 「画像を追加」→「画像をアップロード」をクリックしてファイルインプットを生成
pw -s SESSION click INDEX  # 「画像を追加」ボタン
pw -s SESSION click INDEX  # 「画像をアップロード」ボタン

# Step 2: ファイルインプットの存在を確認（id="note-editor-eyecatch-input"）
pw -s SESSION eval "document.getElementById('note-editor-eyecatch-input') ? 'found' : 'not found'"

# Step 3: ブラウザ側にチャンク配列を初期化
pw -s SESSION eval "window._imgChunks = []; 'ready'"

# Step 4: Base64を80KBチャンクに分割して順次送信
base64 -i /path/to/image.png | tr -d '\n' | fold -w 80000 | while IFS= read -r chunk; do
  pw -s SESSION eval "window._imgChunks.push('$chunk'); window._imgChunks.length"
done

# Step 5: チャンクを結合してファイルインプットに設定
pw -s SESSION eval "
  const b64 = window._imgChunks.join('');
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  const file = new File([arr], 'eyecatch.png', {type: 'image/png'});
  const dt = new DataTransfer();
  dt.items.add(file);
  const input = document.getElementById('note-editor-eyecatch-input');
  input.files = dt.files;
  input.dispatchEvent(new Event('change', {bubbles: true}));
  delete window._imgChunks;
  'SUCCESS: size=' + file.size;
"

# Step 6: クロップダイアログで「保存」をクリック
pw -s SESSION screenshot  # クロップダイアログが表示されることを確認
pw -s SESSION state       # 「保存」ボタンのインデックスを取得
pw -s SESSION click INDEX # 「保存」をクリック
```

**方法B: ユーザーに画像アップロードだけ依頼（フォールバック）**

方法Aが動作しない場合:
```
画像のアップロードだけお願いします:
  ヘッダー画像: /path/to/header.png
  ↑ エディタ上部の「みだし画像」にドラッグ&ドロップしてください
```

4. `pw -s SESSION screenshot` でアップロードされたことを確認

#### 5-2: 本文中の画像

本文中の画像挿入位置にカーソルを移動後:
1. エディタの「+」ボタンまたは画像挿入ボタンをクリック
2. 上記と同様の方法でファイルをアップロード

---

### Step 6: 有料記事の設定（有料の場合のみ）

#### 6-1: 有料ラインの設定

1. 本文中の有料/無料の境界位置にカーソルを配置
2. エディタツールバーまたは `+` メニューから「有料エリア」の区切りを挿入

#### 6-2: 価格の設定

公開設定画面で価格を入力（Step 7 の公開設定時に行う）。

---

### Step 7: 公開設定

#### 7-1: 公開設定画面を開く

1. `pw -s SESSION state` でエディタ右上の「公開設定」または「公開」ボタンを確認
2. クリック:
   ```bash
   pw -s SESSION click INDEX
   ```

#### 7-2: 設定項目を確認・入力

`pw -s SESSION screenshot` で公開設定画面を確認し、以下を設定:

| 設定 | 操作 |
|---|---|
| ハッシュタグ | 関連タグを入力 |
| 販売設定（有料の場合） | 価格を入力 |
| 公開範囲 | 「全体に公開」を選択 |

---

### Step 8: 公開実行（checker PASS 時は自動）

checker が PASS 済みであることを再確認し、自動で公開する。

1. `pw -s SESSION state` で「投稿」または「公開」ボタンのインデックスを確認
2. クリック:
   ```bash
   pw -s SESSION click INDEX
   ```
3. `pw -s SESSION screenshot` で公開完了画面を確認
4. 公開された記事のURLを取得:
   ```bash
   pw -s SESSION eval "location.href"
   ```

---

### Step 9: 完了報告

部長（oac-bucho / cm-bucho）およびユーザーに報告:

```
note記事を公開しました

会社: {いち英語社 or ひつじ社}
アカウント: {@one_ai_company or @careermigaki}
タイトル: 「{タイトル}」
URL: {記事URL}
価格: {無料 or ¥X,XXX}
公開日時: {YYYY-MM-DD HH:MM JST}
checker: PASS（{oac-checker or cm-checker}）
```

---

## 画像の自動生成（オプション）

ヘッダー画像が指定されていない場合、HTMLテンプレートから自動生成できる:

```bash
# 1. HTMLテンプレートで画像を生成（pwでレンダリング→スクリーンショット）
pw -s SESSION open "file:///path/to/eyecatch-template.html?title=記事タイトル"
pw -s SESSION screenshot
# → スクリーンショットをヘッダー画像として使用
```

既存テンプレート:
- `~/projects/claude/ai-company/products/careermigaki-guide/eyecatch-template.html`
- 各部門で独自のテンプレートを用意可能

---

## 注意事項

- **セッションの取り違え厳禁**: いち英語社の記事を `careermigaki` セッションで投稿しない（逆も同様）
- **身元分離ルール厳守**: 各社のコンテンツに他社の情報を含めない
- checker PASS がない記事は絶対に公開しない
- 本文入力は段落ごとに区切って行い、適宜スクリーンショットで確認する
- 画像アップロードが自動化できない場合は方法Cでユーザーに依頼（これが唯一の手動介入ポイント）
- エディタのUIが変更されている可能性があるため、各ステップで `state` と `screenshot` で現状を確認してから操作する

---

## Playwright CLI（pw）コマンド対応表

| 操作 | pw コマンド |
|------|------------------------|
| セッション状態確認 | `pw -s SESSION sessions` |
| URL移動 | `pw -s SESSION open "URL"` |
| スクリーンショット | `pw -s SESSION screenshot` |
| クリック | `pw -s SESSION click INDEX` |
| テキスト入力（type） | `pw -s SESSION type "text"` |
| フォーム入力 | `pw -s SESSION input INDEX "text"` |
| ページ状態・インデックス | `pw -s SESSION state` |
| JS実行 | `pw -s SESSION eval "JS"` |

**セッション使い分け**:
- いち英語社（@one_ai_company）: `pw -s ichi-eigo`
- ひつじ社（@careermigaki）: `pw -s careermigaki`

---

## UIのヒント（2026-03-28 実証済み）

以下はnote.comエディタのUI情報。実際のブラウザ操作で検証済み。

### エディタ画面（`https://editor.note.com/notes/{id}/edit/`）

| 要素 | インデックス(参考) | 備考 |
|---|---|---|
| AIアシスタント | `[2]` | 左サイドバー。邪魔になるので先に `[18]` で閉じる |
| 閉じる（エディタ終了） | `[6]` | 左上 |
| 一時保存 | `[8]` | 右上 |
| 公開に進む | `[9]` | 右上。公開設定画面に遷移 |
| 画像を追加 | `[10]` | タイトル上。クリックでメニュー表示 |
| → 画像をアップロード | `[11]` | メニュー内。クリックで `input[type=file]` を動的生成 |
| → 記事にあう画像を選ぶ | `[12]` | フォトギャラリーから選択 |
| タイトル | `[11]`/`textarea` | エディタ上部 |
| 本文 | `[12]`/`div[role=textbox]` | タイトルの下、ブロック型リッチテキスト |
| AIと相談ダイアログ | `[16]-[18]` | 左サイドバーに常時表示。操作の邪魔になる |

### 重要な発見事項

- **ファイルインプットID**: `note-editor-eyecatch-input`（`accept="image/jpeg,image/png,image/webp"`）
  - 「画像をアップロード」クリック時に動的生成される
- **AIダイアログ**: エディタ左に「AIと相談」が常時表示。クリック操作をインターセプトするので、**画像アップロード前に必ず閉じる**
- **クロップダイアログ**: 画像設定後に自動表示。「保存」をクリックで確定
- **公開済み記事の更新**: エディタで画像変更→保存するだけで即反映。**再公開フロー不要**
- **未保存変更の確認ダイアログ**: エディタから離脱時にブラウザダイアログが出る場合がある

### 公開設定画面（`/publish/`）

- **ハッシュタグ入力**: `input[role=combobox]`
- **記事タイプ**: 無料/有料のラジオボタン
- **価格入力**: 有料選択時に表示
- **注意**: 公開済み記事の場合、「投稿する」ボタンは表示されない（変更は即反映）

### URL構成

- **新規記事**: `https://note.com/notes/new` → エディタにリダイレクト
- **記事編集**: `https://editor.note.com/notes/{id}/edit/`
- **公開設定**: `https://editor.note.com/notes/{id}/publish/`
- **プロフィール**: `https://note.com/{username}`
- **記事公開ページ**: `https://note.com/{username}/n/{note_id}`

---

## トラブルシューティング

### ログインしていない場合
```
note.comにログインされていません。
以下の手順でログインしてください:
1. pw -s SESSION open "https://note.com/login"
2. 手動でログイン
3. 再度スキルを実行
```

### 画像アップロードが失敗する場合
方法A（Base64チャンク送信）→ 方法B（ユーザーに依頼）の順で試行。

方法Aの典型的な失敗パターン:
- ファイルインプットが見つからない → 「画像をアップロード」ボタンを再クリック
- `change` イベントが反応しない → `input` イベントも追加で dispatch
- Base64が壊れている → チャンク数を確認（`window._imgChunks.length`）

### AIダイアログが操作を妨害する場合
エディタ左の「AIと相談」ダイアログがクリック操作をインターセプトすることがある。
```bash
pw -s SESSION click 18  # AIダイアログの「閉じる」ボタン
```
閉じてから目的の操作を行う。

### エディタが応答しない場合
```bash
pw -s SESSION open "https://note.com/notes/new"
```
でページをリロードし、最初からやり直す。

### アカウントが違う場合
```
現在ログイン中のnoteアカウントが対象と異なります。
現在: {現在のアカウント名}
対象: {期待するアカウント名}

対象アカウントでログインし直してください。
```
