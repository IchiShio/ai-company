"""
NR-AutoAuditor メインエントリーポイント
native-real.com の全クイズコンテンツを3段階パイプラインで自動監査・修正・デプロイする。

運用パターン:
    # 今日: 全問監査 + 修正 + git push
    python main.py --auto-fix --auto-push

    # 毎日: 未監査の新規問題のみ
    python main.py --new-only --auto-fix --auto-push

    # 3日ごと: 全問フル監査
    python main.py --auto-fix --auto-push

    # cron wrapper（推奨）
    ./cron_audit.sh
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from config import Config
from db_handler import AuditDB
from extractor import extract_all
from auditor import screening_batch, audit_batch_detailed, precheck_all, AuditStatus
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
        "--auto-fix",
        action="store_true",
        default=False,
        help="自動修正を有効化（confidence >= 0.95 の ERROR のみ）",
    )
    parser.add_argument(
        "--auto-push",
        action="store_true",
        default=False,
        help="修正後に自動で git commit & push（デプロイ）",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        default=False,
        help="まだ一度も監査されていない問題のみ対象",
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
        help="3段階パイプラインを使わず単一モデルで全問監査",
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

    pipeline_mode = (
        f"SINGLE ({config.audit_model})" if args.single_stage
        else f"3-STAGE ({config.screening_model} → {config.audit_model})"
    )
    run_mode = "NEW-ONLY" if args.new_only else "FULL"

    logger.info("=" * 60)
    logger.info("NR-AutoAuditor 開始")
    logger.info("  実行モード: %s", run_mode)
    logger.info("  パイプライン: %s", pipeline_mode)
    logger.info("  修正: %s", "AUTO-FIX + AUTO-PUSH" if (config.auto_fix_enabled and args.auto_push) else "AUTO-FIX" if config.auto_fix_enabled else "DRY-RUN")
    logger.info("  モデル: %s", config.screening_model)
    logger.info("  並列数: %d", config.max_concurrency)
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

    # new-only モード: 未監査の問題のみ対象
    if args.new_only:
        before = len(all_questions)
        all_questions = [
            q for q in all_questions
            if not db.question_was_audited_today(q.question_id)
        ]
        skipped = before - len(all_questions)
        logger.info("NEW-ONLY: %d問スキップ（監査済み）、%d問を監査", skipped, len(all_questions))

    # 問題数制限
    if config.max_questions > 0:
        all_questions = all_questions[: config.max_questions]
        logger.info("最大問題数制限: %d問", len(all_questions))

    if not all_questions:
        logger.info("監査対象の問題がありません。終了します。")
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

    # ── Step 1.5: プログラム的プリチェック（LLM不要・即時） ──
    logger.info("Step 1.5: プリチェック中（正解不在・下線欠落・重複選択肢）...")
    precheck_results = precheck_all(all_questions)
    if precheck_results:
        for r in precheck_results:
            logger.warning("  [Precheck ERROR] %s: %s", r.question_id, r.issues)

    # ── Step 2: LLM 監査 ──
    if args.single_stage:
        logger.info("Step 2: 全問監査 (%d問, model=%s)", len(all_questions), config.audit_model)
        all_results = await audit_batch_detailed(config, all_questions)
    else:
        # Stage 1: スクリーニング
        screening_results = await screening_batch(config, all_questions)

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

        # Stage 2: 精密監査
        if flagged_question_ids:
            flagged_questions = [
                q_map[qid] for qid in flagged_question_ids if qid in q_map
            ]
            detailed_results = await audit_batch_detailed(config, flagged_questions)
        else:
            detailed_results = []
            logger.info("Stage 2: 問題なし。精密監査スキップ。")

        all_results = ok_results + detailed_results

    # プリチェック結果を統合（LLM結果より優先）
    for pr in precheck_results:
        replaced = False
        for i, r in enumerate(all_results):
            if r.question_id == pr.question_id:
                all_results[i] = pr
                replaced = True
                break
        if not replaced:
            all_results.append(pr)

    # ── Step 3: 自動修正 ──
    fix_count = 0
    if config.auto_fix_enabled:
        logger.info("Step 3: 自動修正中...")
        for result in all_results:
            if should_fix(result, config):
                question = q_map.get(result.question_id)
                if question:
                    success = apply_fix(question, result, config, dry_run=False)
                    if success:
                        result.fix_applied = True
                        fix_count += 1
        logger.info("  修正適用: %d件", fix_count)
    else:
        logger.info("Step 3: DRY-RUN モード")
        fix_candidates = [
            r for r in all_results
            if r.status == AuditStatus.ERROR and r.confidence >= config.auto_fix_confidence
        ]
        for r in fix_candidates:
            logger.info("  [DRY-RUN] 修正候補: %s (confidence=%.2f)", r.question_id, r.confidence)

    elapsed = time.time() - start_time

    # ── Step 4: レポート生成 + DB保存 ──
    logger.info("Step 4: レポート生成中...")
    report = build_report(all_results, elapsed)
    report_path = generate_markdown_report(report, config.reports_dir)

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

    # ── Step 5: 自動 git push（修正があった場合のみ） ──
    if args.auto_push and fix_count > 0:
        logger.info("Step 5: git commit & push 中...")
        push_success = _git_push(config, fix_count, report.date)
        if push_success:
            logger.info("  デプロイ完了")
        else:
            logger.error("  git push 失敗")
    elif args.auto_push:
        logger.info("Step 5: 修正なしのため push スキップ")

    # ── Step 6: 通知 ──
    if args.notify and config.has_notification:
        logger.info("Step 6: 通知送信中...")
        summary = format_notification_summary(report)
        await send_notifications(config, summary)

    # ── 完了サマリー ──
    logger.info("=" * 60)
    logger.info("監査完了!")
    logger.info("  モード: %s | %s", run_mode, pipeline_mode)
    logger.info("  総問題数: %d", report.total_questions)
    logger.info("  OK: %d / WARNING: %d / ERROR: %d", report.ok_count, report.warning_count, report.error_count)
    logger.info("  自動修正: %d件", report.auto_fixed_count)
    if args.auto_push and fix_count > 0:
        logger.info("  デプロイ: 済")
    logger.info("  所要時間: %.1f秒", elapsed)
    logger.info("  レポート: %s", report_path)
    logger.info("=" * 60)

    return 0


def _git_push(config: Config, fix_count: int, date: str) -> bool:
    """修正済みファイルを git commit & push"""
    repo_root = config.repo_root
    try:
        # 変更されたファイルをステージ
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo_root, check=True, capture_output=True,
        )
        # コミット
        msg = f"fix(auto-audit): {fix_count}件の問題を自動修正 ({date})\n\nNR-AutoAuditor による自動修正"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=repo_root, check=True, capture_output=True,
        )
        # プッシュ（リトライ付き）
        for attempt in range(4):
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo_root, capture_output=True, text=True,
            )
            if result.returncode == 0:
                return True
            wait = 2 ** (attempt + 1)
            logger.warning("git push 失敗 (attempt %d/4): %s — %d秒後にリトライ", attempt + 1, result.stderr.strip(), wait)
            time.sleep(wait)
        return False
    except subprocess.CalledProcessError as e:
        logger.error("git 操作失敗: %s", e)
        return False


def _show_stats(db: AuditDB) -> None:
    """過去の統計情報を表示"""
    today = datetime.now().strftime("%Y-%m-%d")

    print("\n=== NR-AutoAuditor 統計情報 ===\n")

    all_stats = db.get_stats()
    if all_stats and all_stats.get("total"):
        print("【累計】")
        print(f"  総監査数: {all_stats['total']}")
        print(f"  OK: {all_stats['ok']} / WARNING: {all_stats['warning']} / ERROR: {all_stats['error']}")
        print(f"  自動修正: {all_stats['fixed']} / 検証済み: {all_stats['verified']}")
    else:
        print("まだ監査データがありません。")

    today_stats = db.get_stats(today)
    if today_stats and today_stats.get("total"):
        print(f"\n【今日 ({today})】")
        print(f"  総監査数: {today_stats['total']}")
        print(f"  OK: {today_stats['ok']} / WARNING: {today_stats['warning']} / ERROR: {today_stats['error']}")

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
