# NR-AutoAuditor

native-real.com の全クイズコンテンツ（8,000問以上）を **Gemma 4（ローカルLLM）** で毎日自動監査し、品質問題を検出・修正するシステム。

## 対象クイズ

| クイズ | ファイル | 問題数 |
|--------|----------|--------|
| ListenUp | `listening/questions.js` | ~1,674 |
| GrammarUp | `grammar/questions.js` + `questions_extra.js` | ~1,500 |
| WordsUp | `words/questions.js` | ~5,005 |
| ReadUp | `reading/questions.js` | ~520 |

## セットアップ

### 1. Ollama のインストールと Gemma 4 の準備

```bash
# Ollama インストール
curl -fsSL https://ollama.ai/install.sh | sh

# Gemma 3 27B をダウンロード（推奨）
ollama pull gemma3:27b

# または軽量版
ollama pull gemma3:12b
```

### 2. Python 環境

```bash
cd nr-autoauditor
pip install -r requirements.txt

# .env ファイルの作成
cp .env.example .env
# 必要に応じて .env を編集
```

### 3. 動作確認

```bash
# データ抽出テスト（監査なし）
python main.py --extract-only

# 少数の問題で dry-run テスト
python main.py --max-questions 5

# 特定カテゴリのみ
python main.py --category listenup --max-questions 10
```

## 使い方

### 基本実行（dry-run）

```bash
# 全問題を監査（修正なし）
python main.py

# 特定カテゴリのみ
python main.py --category grammarup

# 問題数を制限
python main.py --max-questions 100
```

### 自動修正を有効化

```bash
# confidence >= 0.95 の ERROR のみ自動修正
python main.py --auto-fix
```

### 統計情報の確認

```bash
python main.py --stats
```

### 通知付きで実行

```bash
python main.py --notify
```

### cron で毎日実行

```bash
# 毎日午前3時に実行
0 3 * * * cd /path/to/nr-autoauditor && python main.py --notify 2>&1 >> /var/log/nr-autoauditor.log
```

## Docker

```bash
# ビルド
docker build -t nr-autoauditor .

# 実行（ホストの Ollama に接続）
docker run --network=host \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/../listening:/repo/listening:ro \
  -v $(pwd)/../grammar:/repo/grammar:ro \
  -v $(pwd)/../words:/repo/words:ro \
  -v $(pwd)/../reading:/repo/reading:ro \
  nr-autoauditor
```

## 安全策

1. **dry-run がデフォルト**: `--auto-fix` を明示的に指定しない限り修正は適用されない
2. **高閾値**: confidence >= 0.95 かつ ERROR の場合のみ自動修正
3. **バックアップ**: 修正前にファイルを `backups/` にコピー
4. **kill-switch**: `--kill-switch` で全処理を即停止
5. **SQLite 履歴**: 全監査結果を DB に保存（ロールバック判断に使用可能）

## ファイル構成

```
nr-autoauditor/
├── main.py              # エントリーポイント
├── config.py            # 設定管理（環境変数 + .env）
├── models.py            # Pydantic データモデル
├── extractor.py         # questions.js パーサー
├── auditor.py           # Gemma 4 / Ollama 監査
├── fixer.py             # 自律修正（バックアップ + ロールバック）
├── db_handler.py        # SQLite 履歴管理
├── reporter.py          # Markdown レポート生成
├── notifier.py          # Slack / Discord / Email 通知
├── audit_prompt.txt     # Gemma 4 用監査プロンプト
├── requirements.txt     # Python 依存パッケージ
├── Dockerfile           # Docker イメージ定義
├── .env.example         # 環境変数テンプレート
├── reports/             # 生成レポート保存先
└── backups/             # 修正前バックアップ保存先
```

## 監査チェック項目

### CRITICAL (ERROR)
- 正解が選択肢に含まれていない
- 複数の正解がある
- 正解が間違っている
- 解説が正解と矛盾
- 英文の文法エラー
- 穴埋め問題の答えが文法的に合わない

### IMPORTANT (WARNING/ERROR)
- 日本語訳の不一致
- 解説の不正確さ
- 選択肢の品質問題
- 難易度の不一致

### MINOR (WARNING)
- タイポ・フォーマット問題
- 空フィールド
- 重複コンテンツの疑い
