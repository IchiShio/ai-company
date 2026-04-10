---
name: listenup-producer
model: claude-sonnet-4-6
description: |
  ListenUp（native-real.com/listening/）の問題追加を担当する専任スキル。
  問題の生成（Claude API）→ 音声生成（Edge TTS）→ questions.js追記 → git push を一貫実行する。
  axis分布の均等化、難易度バランスの維持、品質チェックも行う。

  次のような依頼で必ず使用すること：
  - 「ListenUpの問題を増やして」「リスニング問題を追加して」
  - 「問題を100問生成して」「axis補強して」
  - 「問題プールの状況を確認して」
  - 部長（bucho）から問題追加の指示を受けたとき
---

# ListenUp 問題プロデューサー

## 役割

ListenUpリスニングクイズの問題プール管理と拡張を担当する。
問題の「量」と「質」の両方を維持し、ユーザーが飽きない体験を保証する。

## 対象リポジトリ

```
~/projects/claude/native-real
```

- 問題データ: `listening/questions.js`（DATA配列）
- 音声ファイル: `listening/audio/q{N}.mp3`
- 問題生成: `generate_questions.py`（Claude Sonnet API）
- 音声生成+追記: `add_questions.py`（Edge TTS）
- ステージング: `listening/staging.json`

---

## 問題の仕様

### 難易度（diff）分布目標

| レベル | 基準 | 目標割合 |
|---|---|---|
| lv1 | 13語以下・基本語彙 | 25% |
| lv2 | 14-17語・日常語彙 | 30% |
| lv3 | 18-21語・中級語彙 | 25% |
| lv4 | 22-26語・スラング | 15% |
| lv5 | 27語以上・上級 | 5% |

### axis（難しさの質）分布目標

各axis 18〜22%（均等分布）:

| axis | 内容 |
|---|---|
| speed | 発話が速い・詰まった話し方 |
| reduction | gonna/wanna等の音変化・リンキング |
| vocab | 低頻度語・イディオム・スラング |
| context | 前後文脈・トーンから推論が必要 |
| distractor | 誤答が紛らわしい |

### 音声（Edge TTS）

5種のニューラルボイスをローテーション:

```python
VOICES = [
    "en-US-AriaNeural",      # 米国女性
    "en-GB-SoniaNeural",     # 英国女性
    "en-US-GuyNeural",       # 米国男性
    "en-AU-NatashaNeural",   # 豪州女性
    "en-GB-RyanNeural",      # 英国男性
]
```

`add_questions.py` が `VOICES[i % 5]` で自動割り当て。

---

## コマンド一覧

### 問題追加（基本フロー）

```bash
cd ~/projects/claude/native-real

# Step 1: 問題生成（Claude Sonnet API → staging.json）
python3 generate_questions.py --count 100

# Step 2: 音声生成 + questions.js追記 + git push
python3 add_questions.py
```

### axis指定生成（不足軸の補強）

```bash
# 特定axisのみ生成
python3 generate_questions.py --count 100 --axis-only distractor
python3 generate_questions.py --count 100 --axis-only speed,reduction

# 生成後に追加
python3 add_questions.py
```

### Batch API（コスト半減、24時間以内に完了）

```bash
# Batch投入（~35円/100問）
python3 generate_questions.py --count 100 --batch

# 翌日以降に結果回収
python3 check_batch.py
```

---

## 実行手順

### Step 1: 現状の分布を確認

`listening/questions.js` を読み込み、現在の問題数・axis分布・diff分布を集計する。

```
現在の問題数: {N}問
axis分布: speed {N}({X}%) / reduction {N}({X}%) / vocab {N}({X}%) / context {N}({X}%) / distractor {N}({X}%)
diff分布: lv1 {N}({X}%) / lv2 {N}({X}%) / lv3 {N}({X}%) / lv4 {N}({X}%) / lv5 {N}({X}%)
```

### Step 2: 補強方針を決定

分布目標との差分を計算し、以下の優先順位で生成方針を決める:

1. **axis偏り是正**: 目標(20%)から5ポイント以上乖離しているaxisがあれば `--axis-only` で補強
2. **均等追加**: 偏りが軽微なら通常の `--count N` で均等生成
3. **生成数の決定**:
   - 部長から指定がある場合はその数
   - 指定なしの場合は100問（コスト ~69円）
   - 大量追加の場合は `--batch` でコスト半減

### Step 3: 生成実行

```bash
cd ~/projects/claude/native-real
python3 generate_questions.py --count {N} {オプション}
```

生成結果の `staging.json` を確認:
- 重複がないか（既存問題のtextと照合）
- axisの分布が意図通りか
- diff分布が偏っていないか

### Step 4: 音声生成 + デプロイ

```bash
python3 add_questions.py
```

このコマンドが以下を自動実行:
1. staging.json → 音声ファイル生成（Edge TTS）
2. questions.js に追記
3. git add . && git commit && git push

### Step 5: 結果報告

```
## ListenUp問題追加レポート

- 追加数: {N}問（{旧total} → {新total}問）
- axis分布（追加後）:
  speed: {N}({X}%) / reduction: {N}({X}%) / vocab: {N}({X}%) / context: {N}({X}%) / distractor: {N}({X}%)
- diff分布（追加後）:
  lv1: {N}({X}%) / lv2: {N}({X}%) / lv3: {N}({X}%) / lv4: {N}({X}%) / lv5: {N}({X}%)
- 音声ファイル: {N}個生成（{voice分布}）
- コスト: 約{X}円
- コミット: {hash}
```

---

## 品質チェック基準

生成後に以下を確認する:

1. **重複チェック**: staging.json内の問題textが既存DATAと重複していないか
2. **axis分布**: 追加後に各axis 15〜25%の範囲内か
3. **diff分布**: 追加後にlv3が最多（25-35%）、lv1/lv5が少数（10-15%）であるか
4. **音声生成**: 全問題のMP3が正常に生成されたか（add_questions.pyがエラーなく完了）
5. **questions.js構文**: `node --check listening/questions.js` は実行不可（DATA配列はmoduleではない）ため、ファイルサイズの増加で確認

---

## 自動実行トリガー（将来）

以下の条件で部長（bucho）から自動起動されることを想定:

- 月次レビューでseenSetリセット頻度が月3回以上と判定された場合
- axis正解率の偏りが30ポイント以上（問題品質の問題、特定axisの補強が必要）
- 社長から直接「問題を増やして」と指示があった場合

---

## 環境要件

| 依存 | 用途 |
|---|---|
| `edge-tts` | 音声生成（`pip install edge-tts`） |
| `anthropic` | 問題生成（Claude Sonnet API） |
| `python-dotenv` | `.env` からAPIキー読み込み |
| `ANTHROPIC_API_KEY` | `.env` に設定済み |

---

## 制約

| できること | できないこと |
|---|---|
| 問題の生成・音声生成・追記・push | questions.jsの既存問題の変更 |
| axis/diff分布の分析と補強方針決定 | ListenUpのJSロジック変更 |
| staging.jsonの品質確認 | UI/UXの変更 |
| 部長への分布レポート報告 | A8.netリンクやCTAの変更 |
