---
name: note-publisher
description: |
  note.com への記事投稿を自動化するスキル。
  Playwright CLI（pw）経由でブラウザを操作し、
  記事の作成・本文入力・画像アップロード・公開設定・公開を一貫実行する。
  oac-writer が作成した記事を受け取り、note.com に投稿する。

  次のような依頼で使用すること：
  - 「noteに記事を投稿して」「noteに公開して」
  - 「note記事をアップして」「noteにデプロイして」
  - oac-bucho / oac-scheduler からのnote公開指示
  - パイプラインの公開ステップとして自動呼び出し
---

# note 記事投稿スキル（Claude Code + Playwright CLI版）

note.com のWeb UIを Playwright CLI（pw）経由のブラウザ操作で直接操作し、
記事の作成・本文入力・画像アップロード・公開設定・公開までを自動実行する。

## 前提条件

- `pw -s ichi-eigo` セッションが起動済みで note.com にログイン済みであること
- 投稿する記事のコンテンツ（タイトル・本文・画像パス）が準備済みであること
- oac-checker の品質検査が PASS 済みであること（OAC部門の記事の場合）

## 対象アカウント

| アカウント | pw セッション | 用途 |
|---|---|---|
| @one_ai_company | `pw -s ichi-eigo` | ひとりAI会社のnote記事 |

---

## ワークフロー

### Step 0: 入力の確認

スキル呼び出し時に以下の情報を確認:

| 項目 | 必須 | 説明 |
|---|---|---|
| タイトル | YES | 記事のタイトル |
| 本文 | YES | 記事本文（プレーンテキスト or マークダウン） |
| ヘッダー画像パス | NO | ヘッダーに設定する画像ファイルのパス |
| 本文中画像パス | NO | 本文に挿入する画像ファイルのパス（複数可） |
| 価格 | NO | 有料記事の場合の価格（例: 3980）。未指定なら無料記事 |
| 有料ライン位置 | NO | 有料記事の場合、無料部分と有料部分の境界テキスト |

---

### Step 1: 準備（並列実行）

以下を**同時に**実行する:

**A. 現在時刻の取得**
```bash
TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M %A'
```

**B. ブラウザの準備**
1. `pw -s ichi-eigo sessions` でセッション状態を確認
2. note.com が開いていない場合は `pw -s ichi-eigo open "https://note.com/dashboard"` で移動
3. `pw -s ichi-eigo screenshot` でログイン状態を確認

→ ログインしていない場合はユーザーに報告して中断。

---

### Step 2: 新規記事の作成画面を開く

```bash
pw -s ichi-eigo open "https://note.com/notes/new"
```

`pw -s ichi-eigo screenshot` で記事エディタが開いたことを確認。

---

### Step 3: タイトルの入力

1. `pw -s ichi-eigo state` でタイトル入力欄のインデックスを確認
2. タイトル入力欄をクリック:
   ```bash
   pw -s ichi-eigo click INDEX
   ```
3. タイトルを入力:
   ```bash
   pw -s ichi-eigo type "記事タイトル"
   ```
4. `pw -s ichi-eigo screenshot` で入力を確認

---

### Step 4: 本文の入力

note.com のエディタはブロック型リッチテキストエディタ。

#### 4-1: 本文エリアにフォーカス

1. `pw -s ichi-eigo state` で本文エリアのインデックスを確認
2. 本文エリアをクリック:
   ```bash
   pw -s ichi-eigo click INDEX
   ```

#### 4-2: テキストを段落ごとに入力

本文を段落単位で分割し、1段落ずつ入力する:

```bash
pw -s ichi-eigo type "第1段落のテキスト"
```

段落間の改行:
```bash
pw -s ichi-eigo eval "document.execCommand('insertParagraph')"
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
pw -s ichi-eigo screenshot
```

全体を確認。長い記事の場合はスクロールして複数回スクリーンショットを取る。

---

### Step 5: 画像のアップロード

#### 5-1: ヘッダー画像（みだし画像）

1. `pw -s ichi-eigo state` でエディタ上部の画像追加エリア（みだし画像の設定）を確認
2. 画像追加ボタンをクリック
3. ファイルアップロードの処理:

```bash
pw -s ichi-eigo eval "
  const input = document.querySelector('input[type=\"file\"]');
  if (input) {
    // ファイルインプットが見つかった場合
    console.log('File input found: ' + input.accept);
  } else {
    console.log('File input not found');
  }
"
```

ファイルのアップロードは Playwright の `setInputFiles` 相当の処理が必要。
以下の方法で対応:

**方法A: pw eval でファイルインプットに直接設定**
```bash
pw -s ichi-eigo eval "
  const input = document.querySelector('input[type=\"file\"][accept*=\"image\"]');
  if (input) {
    const dt = new DataTransfer();
    // ファイルデータはBase64で渡す
    const b64 = 'BASE64_ENCODED_IMAGE_DATA';
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    const file = new File([arr], 'header.png', {type: 'image/png'});
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', {bubbles: true}));
    console.log('Image uploaded');
  }
"
```

**方法B: クリップボードペースト（フォールバック）**
```bash
# macOS: 画像をクリップボードにコピーしてペースト
osascript -e 'set the clipboard to (read (POSIX file "/path/to/image.png") as TIFF picture)'
pw -s ichi-eigo eval "document.execCommand('paste')"
```

**方法C: ユーザーに画像アップロードだけ依頼（最終フォールバック）**

方法A/Bが動作しない場合:
```
画像のアップロードだけお願いします:
  ヘッダー画像: /path/to/header.png
  ↑ エディタ上部の「みだし画像」にドラッグ&ドロップしてください
```

#### 5-2: 本文中の画像

本文中の画像挿入位置にカーソルを移動後:
1. エディタの「+」ボタンまたは画像挿入ボタンをクリック
2. 上記と同様の方法でファイルをアップロード

**注意**: 画像の挿入位置は本文の構成に合わせて正確に配置すること。

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

1. `pw -s ichi-eigo state` でエディタ右上の「公開設定」または「公開」ボタンを確認
2. クリック:
   ```bash
   pw -s ichi-eigo click INDEX
   ```

#### 7-2: 設定項目を確認・入力

`pw -s ichi-eigo screenshot` で公開設定画面を確認し、以下を設定:

| 設定 | 操作 |
|---|---|
| ハッシュタグ | 関連タグを入力 |
| 販売設定（有料の場合） | 価格を入力 |
| 公開範囲 | 「全体に公開」を選択 |

#### 7-3: ユーザーに最終確認

公開前に必ずユーザーの承認を得る:

```
note記事の公開準備が完了しました:

  タイトル: 「{タイトル}」
  価格: {無料 or ¥X,XXX}
  ハッシュタグ: #{tag1} #{tag2}

公開してよろしいですか？
```

ユーザーが承認（「ok」「はい」等）するまで待つ。

---

### Step 8: 公開実行

1. `pw -s ichi-eigo state` で「投稿」または「公開」ボタンのインデックスを確認
2. クリック:
   ```bash
   pw -s ichi-eigo click INDEX
   ```
3. `pw -s ichi-eigo screenshot` で公開完了画面を確認
4. 公開された記事のURLを取得:
   ```bash
   pw -s ichi-eigo eval "location.href"
   ```

---

### Step 9: 完了報告

```
note記事を公開しました

タイトル: 「{タイトル}」
URL: {記事URL}
価格: {無料 or ¥X,XXX}
公開日時: {YYYY-MM-DD HH:MM JST}
```

---

## 注意事項

- **公開前にユーザーの承認を必ず得ること**（Step 7-3）
- 本文入力は段落ごとに区切って行い、適宜スクリーンショットで確認する
- 画像アップロードが自動化できない場合はユーザーに依頼する（方法C）
- oac-checker の PASS 判定がない記事は公開しない
- エディタのUIが変更されている可能性があるため、各ステップで `state` と `screenshot` で現状を確認してから操作する
- 長い記事は入力に時間がかかるため、途中経過をユーザーに報告する

---

## Playwright CLI（pw）コマンド対応表

| 操作 | pw コマンド |
|------|------------------------|
| セッション状態確認 | `pw -s ichi-eigo sessions` |
| URL移動 | `pw -s ichi-eigo open "URL"` |
| スクリーンショット | `pw -s ichi-eigo screenshot` |
| クリック | `pw -s ichi-eigo click INDEX` |
| テキスト入力（type） | `pw -s ichi-eigo type "text"` |
| フォーム入力 | `pw -s ichi-eigo input INDEX "text"` |
| ページ状態・インデックス | `pw -s ichi-eigo state` |
| JS実行 | `pw -s ichi-eigo eval "JS"` |

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
1. pw -s ichi-eigo open "https://note.com/login"
2. 手動でログイン
3. 再度スキルを実行
```

### 画像アップロードが失敗する場合
方法A → 方法B → 方法C の順で試行。
方法Cでもダメな場合はユーザーに報告して手動アップロードを依頼。

### エディタが応答しない場合
```bash
pw -s ichi-eigo open "https://note.com/notes/new"
```
でページをリロードし、最初からやり直す。
