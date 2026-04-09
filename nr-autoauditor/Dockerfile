# NR-AutoAuditor Dockerfile
# Ollama はホスト側で別途起動する前提（network=host で接続）

FROM python:3.12-slim

WORKDIR /app

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# レポート・バックアップディレクトリの作成
RUN mkdir -p reports backups

# 非root ユーザーで実行
RUN useradd -m auditor && chown -R auditor:auditor /app
USER auditor

# デフォルトは dry-run モード
ENTRYPOINT ["python", "main.py"]
CMD ["--dry-run"]
