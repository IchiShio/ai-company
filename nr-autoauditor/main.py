"""
NR-AutoAuditor メインエントリーポイント
native-real.com の全クイズコンテンツを自動監査し、品質問題を検出・修正する。

Usage:
    # dry-run（デフォルト・修正なし）
    python main.py

    # 特定カテゴリのみ監査
    python main.py --category listenup

    # 自動修正を有効化（confidence >= 0.95 の ERROR のみ）
    python main.py --auto-fix

    # 問題数を制限してテスト
    python main.py --max-questions 10

    # 統計情報の表示
    python main.py --stats
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime

from config import Config
from db_handler import AuditDB
from extractor import extract_all
from auditor import audit_batch
from fixer import apply_fix, should_fix
from reporter import build_report, format_notification_summary, generate_markdown_report
from notifier import send_notifications

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nr-autoauditor")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NR-AutoAuditor — native-real.com クイズ品質自動監査システム",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="修正を適用せず監査のみ実行（デフォルト）",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        default=False,
        help="自動修正を有効化（confidence >= 0.95 の ERROR のみ）",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="特定カテゴリのみ監査 (listenup/grammarup/wordsup/readup)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=0,
        help="監査する最大問題数（0=無制限）",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="並列リクエスト数の上書き",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama モデル名の上書き（例: gemma3:12b）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="過去の統計情報を表示して終了",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        default=False,
        help="データ抽出のみ実行（監査なし）",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        default=False,
        help="完了後に通知を送信",
    )
    parser.add_argument(
        "--kill-switch",
        action="store_true",
        default=False,
        help="全処理を即時停止",
    )
    return parser.parse_args()


async def run_audit(args: argparse.Namespace) -> int:
    """メイン監査フロー"""
    config = Config()

    # コマンドライン引数で設定を上書き
    if args.auto_fix:
        config.auto_fix_enabled = True
    if args.max_questions:
        config.max_questions = args.max_questions
    if args.concurrency:
        config.max_concurrency = args.concurrency
    if args.model:
        config.ollama_model = args.model
    if args.kill_switch:
        config.kill_switch = True

    # DB初期化
    db = AuditDB(config.db_path)

    # 統計表示モード
    if args.stats:
        _show_stats(db)
        return 0

    # kill-switch チェック
    if config.kill_switch:
        logger.warning("kill-switch が有効です。処理を中止します。")
        return 1

    logger.info("=" * 60)
    logger.info("NR-AutoAuditor 開始")
    logger.info("  モード: %s", "AUTO-FIX" if config.auto_fix_enabled else "DRY-RUN")
    logger.info("  モデル: %s", config.ollama_model)
    logger.info("  並列数: %d", config.max_concurrency)
    logger.info("  閾値: %.2f", config.auto_fix_confidence)
    logger.info("=" * 60)

    start_time = time.time()

    # ── Step 1: データ抽出 ──
    logger.info("Step 1: データ抽出中...")
    all_questions = extract_all(config)

    # カテゴリフィルタ
    if args.category:
        all_questions = [
            q for q in all_questions
            if q.category.value == args.category
        ]
        logger.info("カテゴリ '%s' にフィルタ: %d問", args.category, len(all_questions))

    # 問題数制限
    if config.max_questions > 0:
        all_questions = all_questions[: config.max_questions]
        logger.info("最大問題数制限: %d問", len(all_questions))

    if not all_questions:
        logger.warning("監査対象の問題がありません。終了します。")
        return 0

    # extract-only モード
    if args.extract_only:
        logger.info("抽出完了: %d問", len(all_questions))
        for cat in set(q.category.value for q in all_questions):
            count = sum(1 for q in all_questions if q.category.value == cat)
            logger.info("  %s: %d問", cat, count)
        return 0

    # ── Step 2: 監査実行 ──
    logger.info("Step 2: 監査実行中... (%d問)", len(all_questions))
    results = await audit_batch(config, all_questions)

    # ── Step 3: 自動修正（有効時のみ） ──
    fix_count = 0
    verify_count = 0
    if config.auto_fix_enabled:
        logger.info("Step 3: 自動修正チェック中...")
        # 問題IDから QuizQuestion を引けるようにマップ作成
        q_map = {q.question_id: q for q in all_questions}

        for result in results:
            if should_fix(result, config):
                question = q_map.get(result.question_id)
                if question:
                    dry_run_mode = not config.auto_fix_enabled
                    success = apply_fix(question, result, config, dry_run=dry_run_mode)
                    if success:
                        result.fix_applied = True
                        fix_count += 1
                        # TODO: 修正後の再監査（Phase 2で実装）
    else:
        logger.info("Step 3: DRY-RUN モードのため修正をスキップ")
        # dry-run でも修正候補をログに出力
        for result in results:
            if result.status.value == "ERROR" and result.confidence >= config.auto_fix_confidence:
                logger.info(
                    "[DRY-RUN] 修正候補: %s (confidence=%.2f, issues=%s)",
                    result.question_id,
                    result.confidence,
                    result.issues,
                )

    elapsed = time.time() - start_time

    # ── Step 4: レポート生成 ──
    logger.info("Step 4: レポート生成中...")
    report = build_report(results, elapsed)
    report_path = generate_markdown_report(report, config.reports_dir)

    # DB保存
    db.save_results_batch(results)
    db.save_daily_report(
        date=report.date,
        total=report.total_questions,
        ok=report.ok_count,
        warning=report.warning_count,
        error=report.error_count,
        auto_fixed=report.auto_fixed_count,
        fix_verified=report.fix_verified_count,
        elapsed=report.elapsed_seconds,
        categories=report.categories,
    )

    # ── Step 5: 通知（設定がある場合のみ） ──
    if args.notify and config.has_notification:
        logger.info("Step 5: 通知送信中...")
        summary = format_notification_summary(report)
        await send_notifications(config, summary)

    # ── 完了サマリー ──
    logger.info("=" * 60)
    logger.info("監査完了!")
    logger.info("  総問題数: %d", report.total_questions)
    logger.info("  OK: %d", report.ok_count)
    logger.info("  WARNING: %d", report.warning_count)
    logger.info("  ERROR: %d", report.error_count)
    logger.info("  自動修正: %d", report.auto_fixed_count)
    logger.info("  所要時間: %.1f秒", elapsed)
    logger.info("  レポート: %s", report_path)
    logger.info("=" * 60)

    return 0


def _show_stats(db: AuditDB) -> None:
    """過去の統計情報を表示"""
    today = datetime.now().strftime("%Y-%m-%d")

    print("\n=== NR-AutoAuditor 統計情報 ===\n")

    # 全体統計
    all_stats = db.get_stats()
    if all_stats and all_stats.get("total"):
        print("【累計】")
        print(f"  総監査数: {all_stats['total']}")
        print(f"  OK: {all_stats['ok']} / WARNING: {all_stats['warning']} / ERROR: {all_stats['error']}")
        print(f"  自動修正: {all_stats['fixed']} / 検証済み: {all_stats['verified']}")
    else:
        print("まだ監査データがありません。")

    # 今日の統計
    today_stats = db.get_stats(today)
    if today_stats and today_stats.get("total"):
        print(f"\n【今日 ({today})】")
        print(f"  総監査数: {today_stats['total']}")
        print(f"  OK: {today_stats['ok']} / WARNING: {today_stats['warning']} / ERROR: {today_stats['error']}")

    # 直近のエラー
    errors = db.get_recent_errors(days=7)
    if errors:
        print(f"\n【直近7日間の ERROR ({len(errors)}件)】")
        for e in errors[:10]:
            print(f"  - {e['question_id']} ({e['category']}): {e['issues'][:80]}")

    print()


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(run_audit(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
