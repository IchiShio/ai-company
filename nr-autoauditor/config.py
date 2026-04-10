"""
NR-AutoAuditor 設定管理
環境変数と.envファイルから設定を読み込む
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# .env ファイルがあれば読み込む（python-dotenv は任意依存）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass


@dataclass
class Config:
    """アプリケーション設定"""

    # ── パス設定 ──
    # native-real リポジトリルート（nr-autoauditor の親ディレクトリ）
    repo_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    # レポート保存先
    reports_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports")
    # SQLite DB パス
    db_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "audit_history.db")
    # バックアップ保存先
    backup_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "backups")

    # ── Ollama / Gemma 4 設定 ──
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:31b"
    # Ollama API タイムアウト（秒）
    ollama_timeout: int = 120
    # 並列リクエスト数（Ollama はローカル実行なので控えめに）
    max_concurrency: int = 4
    # リトライ回数
    max_retries: int = 2

    # ── 監査設定 ──
    # 自動修正の信頼度閾値（これ以上で自動修正）
    auto_fix_confidence: float = 0.95
    # 自動修正を有効にするか（False = dry-run）
    auto_fix_enabled: bool = False
    # kill-switch: True にすると全処理を即停止
    kill_switch: bool = False
    # 1回の監査で処理する最大問題数（0 = 無制限）
    max_questions: int = 0

    # ── 通知設定 ──
    # Slack Webhook URL
    slack_webhook_url: Optional[str] = None
    # Discord Webhook URL
    discord_webhook_url: Optional[str] = None
    # Email 設定
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None

    # ── クイズ種別ごとの questions.js パス ──
    quiz_sources: dict[str, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初期化後処理: 環境変数の読み込みとパス解決"""
        # 環境変数からの上書き
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", str(self.ollama_timeout)))
        self.max_concurrency = int(os.getenv("MAX_CONCURRENCY", str(self.max_concurrency)))
        self.auto_fix_confidence = float(
            os.getenv("AUTO_FIX_CONFIDENCE", str(self.auto_fix_confidence))
        )
        self.auto_fix_enabled = os.getenv("AUTO_FIX_ENABLED", "").lower() in ("1", "true", "yes")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", self.slack_webhook_url)
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", self.discord_webhook_url)
        self.smtp_host = os.getenv("SMTP_HOST", self.smtp_host)
        self.smtp_port = int(os.getenv("SMTP_PORT", str(self.smtp_port)))
        self.smtp_user = os.getenv("SMTP_USER", self.smtp_user)
        self.smtp_password = os.getenv("SMTP_PASSWORD", self.smtp_password)
        self.email_from = os.getenv("EMAIL_FROM", self.email_from)
        self.email_to = os.getenv("EMAIL_TO", self.email_to)

        # ディレクトリ作成
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # クイズソースの自動検出
        if not self.quiz_sources:
            self.quiz_sources = self._detect_quiz_sources()

    def _detect_quiz_sources(self) -> dict[str, Path]:
        """リポジトリ内の questions.js ファイルを自動検出"""
        sources: dict[str, Path] = {}
        quiz_dirs = {
            "listenup": self.repo_root / "listening" / "questions.js",
            "grammarup": self.repo_root / "grammar" / "questions.js",
            "grammarup_extra": self.repo_root / "grammar" / "questions_extra.js",
            "wordsup": self.repo_root / "words" / "questions.js",
            "readup": self.repo_root / "reading" / "questions.js",
        }
        for name, path in quiz_dirs.items():
            if path.exists():
                sources[name] = path
        return sources

    @property
    def has_notification(self) -> bool:
        """通知設定が1つでもあるか"""
        return bool(
            self.slack_webhook_url
            or self.discord_webhook_url
            or (self.smtp_host and self.email_to)
        )
