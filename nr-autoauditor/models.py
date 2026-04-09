"""
NR-AutoAuditor データモデル
Pydantic v2 でクイズ問題と監査結果を型安全に管理
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── クイズカテゴリ ──

class QuizCategory(str, Enum):
    """クイズ種別"""
    LISTENUP = "listenup"
    GRAMMARUP = "grammarup"
    GRAMMARUP_EXTRA = "grammarup_extra"
    WORDSUP = "wordsup"
    READUP = "readup"


# ── 監査ステータス ──

class AuditStatus(str, Enum):
    """監査結果のステータス"""
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


# ── クイズ問題モデル ──

class QuizQuestion(BaseModel):
    """全クイズ種別を包含する汎用問題モデル"""

    # 共通フィールド
    question_id: str = Field(description="問題の一意識別子（カテゴリ+インデックス）")
    category: QuizCategory = Field(description="クイズ種別")
    index: int = Field(description="DATA配列内のインデックス（0始まり）")
    diff: str = Field(default="", description="難易度 (lv1-lv5)")
    axis: str = Field(default="", description="問題の軸")
    answer: str = Field(description="正解")
    choices: list[str] = Field(default_factory=list, description="選択肢リスト")
    expl: str = Field(default="", description="解説")

    # ListenUp 固有
    text: Optional[str] = Field(default=None, description="英語テキスト（ListenUp）")
    ja: Optional[str] = Field(default=None, description="日本語訳")
    audio: Optional[str] = Field(default=None, description="音声ファイルパス")
    kp: Optional[list[str]] = Field(default=None, description="キーフレーズ")

    # GrammarUp 固有
    id: Optional[str] = Field(default=None, description="問題ID (g001等)")
    stem: Optional[str] = Field(default=None, description="問題文（穴埋め）")
    tags: Optional[list[str]] = Field(default=None, description="タグ")
    rule: Optional[str] = Field(default=None, description="文法ルール")

    # WordsUp 固有
    word: Optional[str] = Field(default=None, description="対象単語")

    # ReadUp 固有
    pid: Optional[str] = Field(default=None, description="パッセージID")
    passage: Optional[str] = Field(default=None, description="パッセージ本文")
    question: Optional[str] = Field(default=None, description="設問テキスト（ReadUp）")

    # 元データ全体を保持（修正時に必要）
    raw_data: dict[str, Any] = Field(default_factory=dict, description="元のJS問題データ")


# ── 監査結果モデル ──

class FixSuggestion(BaseModel):
    """修正提案"""
    field: str = Field(description="修正対象フィールド名")
    current: str = Field(description="現在の値")
    suggested: str = Field(description="提案値")


class AuditResult(BaseModel):
    """1問あたりの監査結果"""
    question_id: str = Field(description="問題ID")
    category: str = Field(description="クイズ種別")
    status: AuditStatus = Field(description="OK / WARNING / ERROR")
    confidence: float = Field(ge=0.0, le=1.0, description="信頼度 (0.0-1.0)")
    issues: list[str] = Field(default_factory=list, description="検出された問題点")
    fix_suggestions: list[FixSuggestion] = Field(
        default_factory=list, description="修正提案"
    )
    reasoning: str = Field(default="", description="判断理由")

    # メタデータ
    audited_at: datetime = Field(default_factory=datetime.now)
    model_used: str = Field(default="")
    fix_applied: bool = Field(default=False, description="修正が適用されたか")
    fix_verified: bool = Field(default=False, description="修正後の再監査で OK になったか")


# ── 日次レポートモデル ──

class DailyReport(BaseModel):
    """日次監査レポートのサマリー"""
    date: str = Field(description="実行日 (YYYY-MM-DD)")
    total_questions: int = Field(default=0)
    ok_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    error_count: int = Field(default=0)
    auto_fixed_count: int = Field(default=0)
    fix_verified_count: int = Field(default=0)
    elapsed_seconds: float = Field(default=0.0)
    categories: dict[str, int] = Field(default_factory=dict, description="カテゴリ別問題数")
    results: list[AuditResult] = Field(default_factory=list)
