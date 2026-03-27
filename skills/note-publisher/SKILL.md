---
name: note-publisher
description: |
  note.com への記事投稿を全自動化するスキル。
  Playwright CLI（pw）経由でブラウザを操作し、
  記事の作成・本文入力・画像アップロード・公開設定・公開を一貫実行する。
  いち英語社（@one_ai_company）・ひつじ社（@careermigaki）の両社に対応。
  checker PASS 済みなら承認不要で自動公開まで完了する。

  次のような依頼で使用すること：
  - 「noteに記事を投稿して」「noteに公開して」
  - 「note記事をアップして」「noteにデプロイして」
  - oac-bucho / cm-bucho からのnote公開指示
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
| いち英語社 | @one_ai_company | `pw -s ichi-eigo` | oac-checker | ひとりAI会社ブランド |
| ひつじ社 | @careermigaki | `pw -s careermigaki` | cm-checker | キャリア磨きブランド |

**セッション変数**: 以降のワークフローでは `SESSION` と表記する。
- いち英語社の場合: `SESSION=ichi-eigo`
- ひつじ社の場合: `SESSION=careermigaki`

**重要: 身元分離ルール**
- いち英語社の記事にひつじ社の情報を含めない（逆も同様）
- セッションを間違えない（別会社のnoteに投稿したら致命的）
- 投稿内容から対象アカウントを自動判定。判断がつかない場合のみユーザーに確認

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
| 対象会社 | YES | `ichi-eigo`（いち英語社）or `careermigaki`（ひつじ社） |
| ヘッダー画像パス | NO | ヘッダーに設定する画像ファイルのパス |
| 本文中画像パス | NO | 本文に挿入する画像ファイルのパス（複数可） |
| 価格 | NO | 有料記事の場合の価格（例: 3980）。未指定なら無料記事 |
| 有料ライン位置 | NO | 有料記事の場合、無料部分と有料部分の境界テキスト |
| ハッシュタグ | NO | 記事に付けるタグ（複数可） |
| checker結果 | YES | PASS/FAIL。PASSでなければ公開しない |

**アカウント自動判定**:
- 呼び出し元が `oac-*` → `SESSION=ichi-eigo`
- 呼び出し元が `cm-*` → `SESSION=careermigaki`
- 明示指定がある場合はそちらを優先

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

**方法A: pw eval + DataTransfer API（推奨）**
```bash
# Step 1: Base64データを読み込み
B64=$(cat /tmp/note-header-b64.txt)

# Step 2: pw eval でファイルインプットに設定
pw -s SESSION eval "
  const input = document.querySelector('input[type=\"file\"][accept*=\"image\"]');
  if (input) {
    const dt = new DataTransfer();
    const b64 = '$B64';
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    const file = new File([arr], 'header.png', {type: 'image/png'});
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', {bubbles: true}));
    console.log('Image uploaded');
  } else {
    console.log('File input not found');
  }
"
```

**方法B: macOS クリップボードペースト**
```bash
osascript -e 'set the clipboard to (read (POSIX file "/path/to/image.png") as TIFF picture)'
pw -s SESSION eval "document.execCommand('paste')"
```

**方法C: ユーザーに画像アップロードだけ依頼（最終フォールバック）**

方法A/Bが動作しない場合:
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

## UIのヒント（初回実行時に要検証）

以下はnote.comのUIに関する想定。**初回実行時に `state` と `screenshot` で実際のUIを確認し、このセクションを更新すること。**

- **新規記事URL**: `https://note.com/notes/new`
- **ダッシュボード**: `https://note.com/dashboard`
- **タイトル入力欄**: エディタ上部の大きなテキストエリア
- **本文入力欄**: タイトルの下、ブロック型エディタ
- **みだし画像**: エディタ最上部の画像追加エリア
- **「+」ボタン**: 本文中の各行の左側に表示、画像・埋め込み等の追加
- **公開ボタン**: エディタ右上
- **ハッシュタグ入力**: 公開設定画面内
- **有料ライン**: エディタのメニューから挿入

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
方法A → 方法B → 方法C の順で試行。
方法Cでもダメな場合はユーザーに報告して手動アップロードを依頼。

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
