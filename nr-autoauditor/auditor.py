"""
NR-AutoAuditor 監査モジュール
Ollama (Gemma 4) を使って各問題を監査し、品質問題を検出する。

3段階パイプライン:
  1次: gemma4:e4b で高速スクリーニング（全問）
  2次: gemma4:31b で精密監査（WARNING/ERROR のみ）
  3次: gemma4:31b で修正生成（ERROR + confidence>=0.95 のみ）
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from config import Config
from models import AuditResult, AuditStatus, FixSuggestion, QuizCategory, QuizQuestion

logger = logging.getLogger(__name__)

# プロンプトファイルのパス
AUDIT_PROMPT_PATH = Path(__file__).parent / "audit_prompt.txt"
SCREENING_PROMPT_PATH = Path(__file__).parent / "screening_prompt.txt"


def _load_prompt(path: Path) -> str:
    """プロンプトファイルを読み込む"""
    return path.read_text(encoding="utf-8")


def _build_question_payload(q: QuizQuestion) -> dict[str, Any]:
    """QuizQuestion を監査用 JSON ペイロードに変換"""
    payload: dict[str, Any] = {
        "question_id": q.question_id,
        "category": q.category.value,
        "difficulty": q.diff,
        "axis": q.axis,
        "correct_answer": q.answer,
        "choices": q.choices,
        "explanation": q.expl,
    }

    # カテゴリ固有フィールドの追加
    if q.category == QuizCategory.LISTENUP:
        payload["question_text"] = q.text or ""
        payload["japanese_translation"] = q.ja or ""
        payload["key_phrases"] = q.kp or []
        payload["audio_url"] = q.audio or ""

    elif q.category in (QuizCategory.GRAMMARUP, QuizCategory.GRAMMARUP_EXTRA):
        payload["question_text"] = q.stem or ""
        payload["japanese_translation"] = q.ja or ""
        payload["grammar_rule"] = q.rule or ""
        payload["tags"] = q.tags or []

    elif q.category == QuizCategory.WORDSUP:
        payload["target_word"] = q.word or ""
        payload["question_text"] = q.text or ""
        payload["japanese_translation"] = q.ja or ""

    elif q.category == QuizCategory.READUP:
        payload["passage"] = q.passage or ""
        payload["question_text"] = q.question or ""
        payload["key_phrases"] = q.kp or []

    return payload


def _parse_audit_response(response_text: str, question_id: str, model: str) -> AuditResult:
    """
    Gemma 4 のレスポンスから AuditResult をパースする。
    JSON が見つからない場合は WARNING として返す。
    """
    json_str = response_text.strip()

    # コードブロックを除去
    if "```json" in json_str:
        start = json_str.index("```json") + 7
        end = json_str.index("```", start)
        json_str = json_str[start:end].strip()
    elif "```" in json_str:
        start = json_str.index("```") + 3
        end = json_str.index("```", start)
        json_str = json_str[start:end].strip()

    # { ... } だけを抽出
    brace_start = json_str.find("{")
    brace_end = json_str.rfind("}")
    if brace_start != -1 and brace_end != -1:
        json_str = json_str[brace_start : brace_end + 1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("JSON パース失敗 (question=%s): %s", question_id, e)
        return AuditResult(
            question_id=question_id,
            category="unknown",
            status=AuditStatus.WARNING,
            confidence=0.0,
            issues=["LLM応答のJSONパースに失敗"],
            reasoning=response_text[:500],
            model_used=model,
        )

    # ステータスの正規化
    raw_status = data.get("status", "WARNING").upper()
    try:
        status = AuditStatus(raw_status)
    except ValueError:
        status = AuditStatus.WARNING

    # fix_suggestions のパース
    fix_suggestions = []
    for fs in data.get("fix_suggestions", []):
        if isinstance(fs, dict) and "field" in fs:
            fix_suggestions.append(FixSuggestion(
                field=fs["field"],
                current=str(fs.get("current", "")),
                suggested=str(fs.get("suggested", "")),
            ))

    result = AuditResult(
        question_id=data.get("question_id", question_id),
        category=data.get("category", "unknown"),
        status=status,
        confidence=float(data.get("confidence", 0.0)),
        issues=data.get("issues", []),
        fix_suggestions=fix_suggestions,
        reasoning=data.get("reasoning", ""),
        model_used=model,
    )

    # 後処理フィルター: 誤検出を自動降格
    result = _postprocess_result(result)
    return result


def _postprocess_result(result: AuditResult) -> AuditResult:
    """LLM の明らかな誤検出のみフィルター"""
    if result.status == AuditStatus.OK:
        return result

    # 修正提案が現在値と同じ → 実質問題なし → OK に降格
    if result.fix_suggestions:
        all_noop = all(
            fs.current.strip() == fs.suggested.strip()
            for fs in result.fix_suggestions
        )
        if all_noop:
            logger.info("後処理: %s を OK に降格（修正提案=現在値）", result.question_id)
            result.status = AuditStatus.OK
            result.fix_suggestions = []
            result.issues = []

    return result


async def _call_ollama(
    client: httpx.AsyncClient,
    config: Config,
    model: str,
    prompt: str,
    max_tokens: int = 2048,
) -> str:
    """Ollama API にリクエストを送信（JSON モード強制）"""
    url = f"{config.ollama_base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",  # JSON 出力を強制
        "options": {
            "temperature": 0.1,  # 監査は確定的であるべき
            "num_predict": max_tokens,
        },
    }

    for attempt in range(config.max_retries + 1):
        try:
            resp = await client.post(
                url,
                json=payload,
                timeout=config.ollama_timeout,
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "")
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if attempt < config.max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Ollama リクエスト失敗 (attempt %d/%d, model=%s): %s — %d秒後にリトライ",
                    attempt + 1, config.max_retries + 1, model, e, wait,
                )
                await asyncio.sleep(wait)
            else:
                raise


# ── 1次スクリーニング（gemma4:e4b — 高速） ──

async def screen_question(
    client: httpx.AsyncClient,
    config: Config,
    question: QuizQuestion,
    screening_prompt: str,
) -> AuditResult:
    """1問を高速スクリーニング（e4b）"""
    payload = _build_question_payload(question)
    question_json = json.dumps(payload, ensure_ascii=False, indent=2)
    full_prompt = f"{screening_prompt}\n\n### QUIZ ITEM\n```json\n{question_json}\n```"

    try:
        response_text = await _call_ollama(
            client, config, config.screening_model, full_prompt, max_tokens=512
        )
        result = _parse_audit_response(
            response_text, question.question_id, config.screening_model
        )
        result.category = question.category.value
        return result
    except Exception as e:
        logger.error("スクリーニング失敗 (question=%s): %s", question.question_id, e)
        return AuditResult(
            question_id=question.question_id,
            category=question.category.value,
            status=AuditStatus.WARNING,
            confidence=0.0,
            issues=[f"スクリーニングエラー: {e}"],
            model_used=config.screening_model,
        )


async def screening_batch(
    config: Config,
    questions: list[QuizQuestion],
) -> list[AuditResult]:
    """
    1次スクリーニング: 全問を e4b で高速チェック。
    OK 以外の問題を2次監査に回す。
    """
    screening_prompt = _load_prompt(SCREENING_PROMPT_PATH)
    semaphore = asyncio.Semaphore(config.max_concurrency)
    total = len(questions)

    logger.info("[Stage 1] スクリーニング開始: %d問 (model=%s)", total, config.screening_model)

    async with httpx.AsyncClient() as client:

        async def _screen(q: QuizQuestion, idx: int) -> AuditResult:
            async with semaphore:
                if config.kill_switch:
                    return AuditResult(
                        question_id=q.question_id,
                        category=q.category.value,
                        status=AuditStatus.WARNING,
                        confidence=0.0,
                        issues=["kill-switch が有効"],
                        model_used=config.screening_model,
                    )
                result = await screen_question(client, config, q, screening_prompt)
                if (idx + 1) % 100 == 0 or idx + 1 == total:
                    logger.info("[Stage 1] 進捗: %d / %d", idx + 1, total)
                return result

        tasks = [_screen(q, i) for i, q in enumerate(questions)]
        results = await asyncio.gather(*tasks)

    ok_count = sum(1 for r in results if r.status == AuditStatus.OK)
    flagged = sum(1 for r in results if r.status != AuditStatus.OK)
    logger.info("[Stage 1] 完了: OK=%d, 要精査=%d", ok_count, flagged)

    return list(results)


# ── 2次精密監査（gemma4:31b — 高精度） ──

async def audit_question_detailed(
    client: httpx.AsyncClient,
    config: Config,
    question: QuizQuestion,
    audit_prompt: str,
) -> AuditResult:
    """1問を精密監査（31b）— 詳細な分析と修正提案を生成"""
    payload = _build_question_payload(question)
    question_json = json.dumps(payload, ensure_ascii=False, indent=2)
    full_prompt = f"{audit_prompt}\n\n### QUIZ ITEM TO AUDIT\n```json\n{question_json}\n```"

    try:
        response_text = await _call_ollama(
            client, config, config.audit_model, full_prompt, max_tokens=2048
        )
        result = _parse_audit_response(
            response_text, question.question_id, config.audit_model
        )
        result.category = question.category.value
        return result
    except Exception as e:
        logger.error("精密監査失敗 (question=%s): %s", question.question_id, e)
        return AuditResult(
            question_id=question.question_id,
            category=question.category.value,
            status=AuditStatus.WARNING,
            confidence=0.0,
            issues=[f"精密監査エラー: {e}"],
            model_used=config.audit_model,
        )


async def audit_batch_detailed(
    config: Config,
    questions: list[QuizQuestion],
) -> list[AuditResult]:
    """
    2次精密監査: フラグ付き問題を 31b で詳細チェック。
    修正提案 (fix_suggestions) もここで生成される。
    """
    audit_prompt = _load_prompt(AUDIT_PROMPT_PATH)
    semaphore = asyncio.Semaphore(config.max_concurrency)
    total = len(questions)

    logger.info("[Stage 2] 精密監査開始: %d問 (model=%s)", total, config.audit_model)

    async with httpx.AsyncClient() as client:

        async def _audit(q: QuizQuestion, idx: int) -> AuditResult:
            async with semaphore:
                if config.kill_switch:
                    return AuditResult(
                        question_id=q.question_id,
                        category=q.category.value,
                        status=AuditStatus.WARNING,
                        confidence=0.0,
                        issues=["kill-switch が有効"],
                        model_used=config.audit_model,
                    )
                result = await audit_question_detailed(client, config, q, audit_prompt)
                if (idx + 1) % 10 == 0 or idx + 1 == total:
                    logger.info("[Stage 2] 進捗: %d / %d", idx + 1, total)
                return result

        tasks = [_audit(q, i) for i, q in enumerate(questions)]
        results = await asyncio.gather(*tasks)

    ok_count = sum(1 for r in results if r.status == AuditStatus.OK)
    warn_count = sum(1 for r in results if r.status == AuditStatus.WARNING)
    err_count = sum(1 for r in results if r.status == AuditStatus.ERROR)
    logger.info("[Stage 2] 完了: OK=%d, WARNING=%d, ERROR=%d", ok_count, warn_count, err_count)

    return list(results)


# ── 後方互換: 単一モデルで全問監査（--single-stage 用） ──

async def audit_batch(
    config: Config,
    questions: list[QuizQuestion],
) -> list[AuditResult]:
    """単一モデルで全問監査（後方互換）"""
    return await audit_batch_detailed(config, questions)
