"""
NR-AutoAuditor 自律修正モジュール
ERROR + confidence >= 0.95 の問題のみ安全に修正する。
修正前バックアップ → 修正適用 → 再監査 の順で実行。
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from config import Config
from models import AuditResult, AuditStatus, QuizCategory, QuizQuestion

logger = logging.getLogger(__name__)


def should_fix(result: AuditResult, config: Config) -> bool:
    """この監査結果に対して自動修正を行うべきか判定"""
    if not config.auto_fix_enabled:
        return False
    if config.kill_switch:
        return False
    if result.status != AuditStatus.ERROR:
        return False
    if result.confidence < config.auto_fix_confidence:
        return False
    if not result.fix_suggestions:
        return False
    return True


def backup_file(path: Path, config: Config) -> Path:
    """修正前にファイルをバックアップ"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.stem}_{timestamp}{path.suffix}"
    backup_path = config.backup_dir / backup_name
    shutil.copy2(path, backup_path)
    logger.info("バックアップ作成: %s", backup_path)
    return backup_path


def _category_to_path(category: str, config: Config) -> Path | None:
    """カテゴリ名からファイルパスを取得"""
    return config.quiz_sources.get(category)


def _rebuild_js_object(data: dict[str, Any]) -> str:
    """
    Python dict を JS オブジェクトリテラル形式に変換。
    questions.js の既存フォーマットを維持する。
    キーにクォートなし、値は適切にフォーマット。
    """
    parts: list[str] = []
    for key, value in data.items():
        if isinstance(value, str):
            # ダブルクォート内のエスケープ
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{key}: "{escaped}"')
        elif isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                items = ", ".join(f'"{v}"' for v in value)
                parts.append(f"{key}: [{items}]")
            else:
                parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        elif isinstance(value, bool):
            parts.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            parts.append(f"{key}: {value}")
        elif value is None:
            continue  # null フィールドはスキップ
        else:
            parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")

    return "  { " + ", ".join(parts) + " }"


def apply_fix(
    question: QuizQuestion,
    result: AuditResult,
    config: Config,
    dry_run: bool = True,
) -> bool:
    """
    問題データの修正を適用する。

    Returns:
        True: 修正成功
        False: 修正失敗またはスキップ
    """
    file_path = _category_to_path(question.category.value, config)
    if not file_path or not file_path.exists():
        logger.error("ファイルが見つかりません: category=%s", question.category.value)
        return False

    # 修正データの構築
    fixed_data = dict(question.raw_data)
    for suggestion in result.fix_suggestions:
        field = suggestion.field
        if field in fixed_data:
            logger.info(
                "修正適用: %s.%s = %r → %r",
                question.question_id, field,
                suggestion.current, suggestion.suggested,
            )
            # choices フィールドの場合はリストとして処理
            if field == "choices" and isinstance(suggestion.suggested, str):
                try:
                    fixed_data[field] = json.loads(suggestion.suggested)
                except json.JSONDecodeError:
                    fixed_data[field] = suggestion.suggested
            else:
                fixed_data[field] = suggestion.suggested
        else:
            logger.warning(
                "フィールド %s が元データに存在しません (question=%s)",
                field, question.question_id,
            )

    if dry_run:
        logger.info("[DRY-RUN] 修正をスキップ: %s", question.question_id)
        _log_fix_preview(question, result, fixed_data)
        return True

    # バックアップ作成
    backup_file(file_path, config)

    # ファイルの読み込みと修正
    try:
        content = file_path.read_text(encoding="utf-8")
        original_line = _rebuild_js_object(question.raw_data)
        fixed_line = _rebuild_js_object(fixed_data)

        # 元の行を見つけて置換
        # 正確なマッチのためにインデックス(位置)ベースで検索
        if original_line.strip() in content:
            content = content.replace(original_line.strip(), fixed_line.strip(), 1)
        else:
            # フォールバック: answer フィールドの値で行を特定
            logger.warning("完全一致で行が見つからないため、インデックスベースで修正")
            success = _apply_fix_by_index(
                file_path, content, question.index, fixed_data
            )
            if not success:
                return False
            return True

        file_path.write_text(content, encoding="utf-8")
        logger.info("修正をファイルに書き込み: %s (question=%s)", file_path, question.question_id)
        return True

    except Exception as e:
        logger.error("修正の適用に失敗: %s — %s", question.question_id, e)
        return False


def _apply_fix_by_index(
    file_path: Path,
    content: str,
    index: int,
    fixed_data: dict[str, Any],
) -> bool:
    """
    インデックスベースで問題行を特定し修正する。
    DATA 配列の n 番目のオブジェクトを書き換える。
    """
    # { ... } ブロックを順番に見つける
    pattern = re.compile(r"\{[^{}]+\}", re.DOTALL)
    matches = list(pattern.finditer(content))

    if index >= len(matches):
        logger.error("インデックス %d が範囲外 (全%d問)", index, len(matches))
        return False

    target_match = matches[index]
    fixed_line = _rebuild_js_object(fixed_data)

    new_content = (
        content[: target_match.start()]
        + fixed_line
        + content[target_match.end() :]
    )

    file_path.write_text(new_content, encoding="utf-8")
    return True


def _log_fix_preview(
    question: QuizQuestion,
    result: AuditResult,
    fixed_data: dict[str, Any],
) -> None:
    """dry-run モード時に修正プレビューをログに出力"""
    logger.info("=" * 60)
    logger.info("[DRY-RUN] 修正プレビュー: %s", question.question_id)
    logger.info("  カテゴリ: %s", question.category.value)
    logger.info("  ステータス: %s (confidence: %.2f)", result.status.value, result.confidence)
    logger.info("  検出問題:")
    for issue in result.issues:
        logger.info("    - %s", issue)
    logger.info("  修正提案:")
    for fs in result.fix_suggestions:
        logger.info("    %s: %r → %r", fs.field, fs.current, fs.suggested)
    logger.info("=" * 60)


def rollback(file_path: Path, config: Config) -> bool:
    """最新のバックアップからロールバック"""
    backups = sorted(
        config.backup_dir.glob(f"{file_path.stem}_*{file_path.suffix}"),
        reverse=True,
    )
    if not backups:
        logger.error("バックアップが見つかりません: %s", file_path.name)
        return False

    latest = backups[0]
    shutil.copy2(latest, file_path)
    logger.info("ロールバック完了: %s → %s", latest.name, file_path)
    return True
