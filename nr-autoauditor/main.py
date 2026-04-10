"""
NR-AutoAuditor メインエントリーポイント
native-real.com の全クイズコンテンツを3段階パイプラインで自動監査・修正する。

3段階パイプライン:
  Stage 1: gemma4:e4b  — 全問を高速スクリーニング
  Stage 2: gemma4:31b  — WARNING/ERROR のみ精密監査
  Stage 3: gemma4:31b  — ERROR (confidence>=0.95) を修正生成

Usage:
    # dry-run（デフォルト・修正なし）
    python main.py --max-questions 10

    # 特定カテゴリのみ
    python main.py --category listenup

    # 自動修正を有効化
    python main.py --auto-fix

    # 31bのみで全問監査（旧方式）
    python main.py --single-stage

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
from auditor import screening_batch, audit_batch_detailed, AuditStatus
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
        "--single-stage",
        action="store_true",
        default=False,
        help="3段階パイプラインを使わず 31b のみで全問監査",
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
    """メイン監査フロー（3段階パイプライン）"""
    config = Config()

    # コマンドライン引数で設定を上書き
    if args.auto_fix:
        config.auto_fix_enabled = True
    if args.max_questions:
        config.max_questions = args.max_questions
    if args.concurrency:
        config.max_concurrency = args.concurrency
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

    pipeline_mode = "SINGLE (31b only)" if args.single_stage else "3-STAGE (e4b → 31b → 31b)"

    logger.info("=" * 60)
    logger.info("NR-AutoAuditor 開始")
    logger.info("  パイプライン: %s", pipeline_mode)
    logger.info("  モード: %s", "AUTO-FIX" if config.auto_fix_enabled else "DRY-RUN")
    logger.info("  スクリーニング: %s", config.screening_model)
    logger.info("  精密監査/修正: %s", config.audit_model)
    logger.info("  並列数: %d", config.max_concurrency)
    logger.info("  修正閾値: confidence >= %.2f", config.auto_fix_confidence)
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
        for cat in sorted(set(q.category.value for q in all_questions)):
            count = sum(1 for q in all_questions if q.category.value == cat)
            logger.info("  %s: %d問", cat, count)
        return 0

    # 問題IDからQuizQuestionを引くマップ
    q_map = {q.question_id: q for q in all_questions}

    if args.single_stage:
        # ── 旧方式: 31b で全問監査 ──
        logger.info("Step 2: 全問監査 (%d問, model=%s)", len(all_questions), config.audit_model)
        all_results = await audit_batch_detailed(config, all_questions)
    else:
        # ── 3段階パイプライン ──

        # Stage 1: e4b で全問スクリーニング
        screening_results = await screening_batch(config, all_questions)

        # Stage 1 の結果を振り分け
        ok_results = []
        flagged_question_ids = []
        for r in screening_results:
            if r.status == AuditStatus.OK:
                ok_results.append(r)
            else:
                flagged_question_ids.append(r.question_id)

        logger.info(
            "Stage 1 結果: OK=%d, 要精査=%d (%.1f%%)",
            len(ok_results),
            len(flagged_question_ids),
            len(flagged_question_ids) / max(len(screening_results), 1) * 100,
        )

        # Stage 2: フラグ付き問題のみ 31b で精密監査
        if flagged_question_ids:
            flagged_questions = [
                q_map[qid] for qid in flagged_question_ids if qid in q_map
            ]
            detailed_results = await audit_batch_detailed(config, flagged_questions)
        else:
            detailed_results = []
            logger.info("Stage 2: スクリーニングで問題なし。精密監査をスキップ。")

        # 結果を統合: OK結果 + 精密監査結果
        all_results = ok_results + detailed_results

    # ── Step 3: 自動修正（31b の結果に基づく） ──
    if config.auto_fix_enabled:
        logger.info("Step 3: 自動修正チェック中... (model=%s)", config.fix_model)
        for result in all_results:
            if should_fix(result, config):
                question = q_map.get(result.question_id)
                if question:
                    success = apply_fix(question, result, config, dry_run=False)
                    if success:
                        result.fix_applied = True
    else:
        logger.info("Step 3: DRY-RUN モードのため修正をスキップ")
        fix_candidates = [
            r for r in all_results
            if r.status == AuditStatus.ERROR and r.confidence >= config.auto_fix_confidence
        ]
        for r in fix_candidates:
            logger.info(
                "[DRY-RUN] 修正候補: %s (confidence=%.2f, issues=%s)",
                r.question_id, r.confidence, r.issues,
            )
        if not fix_candidates:
            logger.info("[DRY-RUN] 高信頼度の修正候補なし")

    elapsed = time.time() - start_time

    # ── Step 4: レポート生成 ──
    logger.info("Step 4: レポート生成中...")
    report = build_report(all_results, elapsed)
    report_path = generate_markdown_report(report, config.reports_dir)

    # DB保存
    db.save_results_batch(all_results)
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
    logger.info("  パイプライン: %s", pipeline_mode)
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
