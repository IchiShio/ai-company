"""
NR-AutoAuditor 監査モジュール
Ollama (Gemma 4) を使って各問題を監査し、品質問題を検出する。
非同期処理でバッチ実行。
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from config import Config
from models import AuditResult, AuditStatus, FixSuggestion, QuizCategory, QuizQuestion

logger = logging.getLogger(__name__)

# 監査プロンプトテンプレートのパス
PROMPT_PATH = Path(__file__).parent / "audit_prompt.txt"


def _load_audit_prompt() -> str:
    """audit_prompt.txt を読み込む"""
    return PROMPT_PATH.read_text(encoding="utf-8")


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
    # JSON ブロックを抽出（```json ... ``` 形式にも対応）
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

    return AuditResult(
        question_id=data.get("question_id", question_id),
        category=data.get("category", "unknown"),
        status=status,
        confidence=float(data.get("confidence", 0.0)),
        issues=data.get("issues", []),
        fix_suggestions=fix_suggestions,
        reasoning=data.get("reasoning", ""),
        model_used=model,
    )


async def _call_ollama(
    client: httpx.AsyncClient,
    config: Config,
    prompt: str,
) -> str:
    """Ollama API にリクエストを送信"""
    url = f"{config.ollama_base_url}/api/generate"
    payload = {
        "model": config.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # 監査は確定的であるべき
            "num_predict": 2048,
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
                    "Ollama リクエスト失敗 (attempt %d/%d): %s — %d秒後にリトライ",
                    attempt + 1, config.max_retries + 1, e, wait,
                )
                await asyncio.sleep(wait)
            else:
                raise


async def audit_question(
    client: httpx.AsyncClient,
    config: Config,
    question: QuizQuestion,
    audit_prompt_template: str,
) -> AuditResult:
    """1問を監査する"""
    # 問題データをJSONに変換
    payload = _build_question_payload(question)
    question_json = json.dumps(payload, ensure_ascii=False, indent=2)

    # プロンプトを構築
    full_prompt = f"{audit_prompt_template}\n\n### QUIZ ITEM TO AUDIT\n```json\n{question_json}\n```"

    try:
        response_text = await _call_ollama(client, config, full_prompt)
        result = _parse_audit_response(
            response_text, question.question_id, config.ollama_model
        )
        result.category = question.category.value
        return result
    except Exception as e:
        logger.error("監査失敗 (question=%s): %s", question.question_id, e)
        return AuditResult(
            question_id=question.question_id,
            category=question.category.value,
            status=AuditStatus.WARNING,
            confidence=0.0,
            issues=[f"監査実行エラー: {e}"],
            model_used=config.ollama_model,
        )


async def audit_batch(
    config: Config,
    questions: list[QuizQuestion],
) -> list[AuditResult]:
    """
    問題をバッチで監査する。
    セマフォで並列数を制御し、Ollama への過負荷を防ぐ。
    """
    audit_prompt_template = _load_audit_prompt()
    semaphore = asyncio.Semaphore(config.max_concurrency)
    results: list[AuditResult] = []
    total = len(questions)

    async with httpx.AsyncClient() as client:

        async def _audit_with_semaphore(q: QuizQuestion, idx: int) -> AuditResult:
            async with semaphore:
                # kill-switch チェック
                if config.kill_switch:
                    return AuditResult(
                        question_id=q.question_id,
                        category=q.category.value,
                        status=AuditStatus.WARNING,
                        confidence=0.0,
                        issues=["kill-switch が有効なため監査をスキップ"],
                        model_used=config.ollama_model,
                    )

                result = await audit_question(
                    client, config, q, audit_prompt_template
                )

                # 進捗ログ（100問ごと）
                if (idx + 1) % 100 == 0 or idx + 1 == total:
                    logger.info("進捗: %d / %d 問完了", idx + 1, total)

                return result

        tasks = [
            _audit_with_semaphore(q, i)
            for i, q in enumerate(questions)
        ]
        results = await asyncio.gather(*tasks)

    return list(results)
