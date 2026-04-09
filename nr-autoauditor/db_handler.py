"""
NR-AutoAuditor SQLite 履歴管理モジュール
全監査結果をSQLiteに保存し、履歴の検索・統計を提供する。
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from models import AuditResult, AuditStatus, FixSuggestion

logger = logging.getLogger(__name__)

# スキーマ定義
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    issues TEXT NOT NULL,  -- JSON配列
    fix_suggestions TEXT NOT NULL,  -- JSON配列
    reasoning TEXT NOT NULL,
    model_used TEXT NOT NULL,
    fix_applied INTEGER NOT NULL DEFAULT 0,
    fix_verified INTEGER NOT NULL DEFAULT 0,
    audited_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_question_id ON audit_results(question_id);
CREATE INDEX IF NOT EXISTS idx_status ON audit_results(status);
CREATE INDEX IF NOT EXISTS idx_audited_at ON audit_results(audited_at);
CREATE INDEX IF NOT EXISTS idx_category ON audit_results(category);

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_questions INTEGER NOT NULL,
    ok_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    auto_fixed_count INTEGER NOT NULL,
    fix_verified_count INTEGER NOT NULL,
    elapsed_seconds REAL NOT NULL,
    categories TEXT NOT NULL,  -- JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class AuditDB:
    """監査履歴データベース"""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """データベースとテーブルを初期化"""
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("DB初期化完了: %s", self.db_path)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """SQLite接続のコンテキストマネージャ"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_result(self, result: AuditResult) -> None:
        """監査結果を1件保存"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_results
                (question_id, category, status, confidence, issues,
                 fix_suggestions, reasoning, model_used, fix_applied,
                 fix_verified, audited_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.question_id,
                    result.category,
                    result.status.value,
                    result.confidence,
                    json.dumps(result.issues, ensure_ascii=False),
                    json.dumps(
                        [fs.model_dump() for fs in result.fix_suggestions],
                        ensure_ascii=False,
                    ),
                    result.reasoning,
                    result.model_used,
                    int(result.fix_applied),
                    int(result.fix_verified),
                    result.audited_at.isoformat(),
                ),
            )

    def save_results_batch(self, results: list[AuditResult]) -> None:
        """監査結果をバッチ保存"""
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO audit_results
                (question_id, category, status, confidence, issues,
                 fix_suggestions, reasoning, model_used, fix_applied,
                 fix_verified, audited_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.question_id,
                        r.category,
                        r.status.value,
                        r.confidence,
                        json.dumps(r.issues, ensure_ascii=False),
                        json.dumps(
                            [fs.model_dump() for fs in r.fix_suggestions],
                            ensure_ascii=False,
                        ),
                        r.reasoning,
                        r.model_used,
                        int(r.fix_applied),
                        int(r.fix_verified),
                        r.audited_at.isoformat(),
                    )
                    for r in results
                ],
            )
        logger.info("バッチ保存完了: %d件", len(results))

    def save_daily_report(
        self,
        date: str,
        total: int,
        ok: int,
        warning: int,
        error: int,
        auto_fixed: int,
        fix_verified: int,
        elapsed: float,
        categories: dict[str, int],
    ) -> None:
        """日次レポートサマリーを保存"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO daily_reports
                (date, total_questions, ok_count, warning_count, error_count,
                 auto_fixed_count, fix_verified_count, elapsed_seconds, categories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date, total, ok, warning, error,
                    auto_fixed, fix_verified, elapsed,
                    json.dumps(categories, ensure_ascii=False),
                ),
            )

    def get_recent_errors(self, days: int = 7) -> list[dict]:
        """直近N日間のERROR結果を取得"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM audit_results
                WHERE status = 'ERROR'
                  AND audited_at >= datetime('now', ?)
                ORDER BY audited_at DESC
                """,
                (f"-{days} days",),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_stats(self, date: str | None = None) -> dict:
        """統計情報を取得"""
        with self._connect() as conn:
            if date:
                where = "WHERE date(audited_at) = ?"
                params = (date,)
            else:
                where = ""
                params = ()

            row = conn.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as ok,
                    SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as error,
                    SUM(fix_applied) as fixed,
                    SUM(fix_verified) as verified
                FROM audit_results
                {where}
                """,
                params,
            ).fetchone()

            return dict(row) if row else {}

    def question_was_audited_today(self, question_id: str) -> bool:
        """今日すでに監査済みかチェック（重複実行防止）"""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM audit_results
                WHERE question_id = ? AND date(audited_at) = ?
                """,
                (question_id, today),
            ).fetchone()
            return row["cnt"] > 0 if row else False
