"""
NR-AutoAuditor データ抽出モジュール
questions.js ファイルから問題データを直接パースして QuizQuestion モデルに変換する。
JS オブジェクトリテラル（キーにクォートなし）をPythonで安全にパースする。
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from config import Config
from models import QuizCategory, QuizQuestion

logger = logging.getLogger(__name__)


def _js_to_json(js_text: str) -> str:
    """
    JS オブジェクトリテラルを JSON に変換する。
    - const DATA = [...]; → 配列部分だけ抽出
    - // コメント除去
    - キーにクォートを付与
    - 末尾カンマ除去
    """
    # 1. 配列部分を抽出
    # パターン1: const DATA = [...] 形式
    match = re.search(r"(?:const|let|var)\s+\w+\s*=\s*(\[.*\])", js_text, re.DOTALL)
    if not match:
        # パターン2: DATA.push(...) 形式 → 中身を配列に変換
        match = re.search(r"\w+\.push\(\s*([\s\S]+)\s*\)\s*;?\s*$", js_text.strip(), re.DOTALL)
        if match:
            inner = match.group(1).strip()
            # push() の引数は個別オブジェクト列なので [...] で囲む
            if not inner.startswith("["):
                inner = "[" + inner + "]"
            array_text = inner
        else:
            raise ValueError("DATA配列が見つかりません")
    else:
        array_text = match.group(1)

    # 2. 行コメント除去（文字列中の // は除外）
    # 文字列リテラル内でない // コメントだけ除去する
    lines = array_text.split("\n")
    cleaned_lines = []
    for line in lines:
        # 行全体がコメントの場合
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        # 行末コメント除去（文字列外の // のみ）
        cleaned = _remove_inline_comment(line)
        cleaned_lines.append(cleaned)
    array_text = "\n".join(cleaned_lines)

    # 3. キーにクォートを付与: { key: → { "key":
    # 既にクォートされているキーはスキップ
    array_text = re.sub(
        r'(?<=[{,\s])(\w+)\s*:',
        r'"\1":',
        array_text
    )

    # 4. 末尾カンマ除去: ,] → ] と ,} → }
    array_text = re.sub(r",\s*([}\]])", r"\1", array_text)

    return array_text


def _remove_inline_comment(line: str) -> str:
    """文字列リテラル外の行末 // コメントを除去"""
    in_string = False
    escape_next = False
    quote_char = None
    i = 0
    while i < len(line):
        ch = line[i]
        if escape_next:
            escape_next = False
            i += 1
            continue
        if ch == "\\":
            escape_next = True
            i += 1
            continue
        if in_string:
            if ch == quote_char:
                in_string = False
                quote_char = None
        else:
            if ch in ('"', "'"):
                in_string = True
                quote_char = ch
            elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                return line[:i].rstrip()
        i += 1
    return line


def parse_questions_js(path: Path) -> list[dict[str, Any]]:
    """questions.js ファイルを読み込み、問題データのリストを返す"""
    logger.info("パース中: %s", path)
    js_text = path.read_text(encoding="utf-8")

    try:
        json_text = _js_to_json(js_text)
        data = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("JSON パースエラー (%s): %s", path.name, e)
        # フォールバック: 正規表現で個別オブジェクトを抽出
        data = _fallback_parse(js_text)

    logger.info("  → %d 問読み込み完了", len(data))
    return data


def _fallback_parse(js_text: str) -> list[dict[str, Any]]:
    """
    フォールバックパーサー: 正規表現でオブジェクトを1つずつ抽出。
    メインパーサーが失敗した場合の安全策。
    """
    results = []
    # { ... } ブロックを1つずつ抽出
    pattern = re.compile(r"\{[^{}]+\}", re.DOTALL)
    for match in pattern.finditer(js_text):
        obj_text = match.group()
        try:
            # キーにクォート付与
            obj_text = re.sub(r'(?<=[{,\s])(\w+)\s*:', r'"\1":', obj_text)
            obj_text = re.sub(r",\s*}", "}", obj_text)
            obj = json.loads(obj_text)
            results.append(obj)
        except json.JSONDecodeError:
            continue
    return results


def _detect_category(source_name: str) -> QuizCategory:
    """ソース名からクイズカテゴリを判定"""
    mapping = {
        "listenup": QuizCategory.LISTENUP,
        "grammarup": QuizCategory.GRAMMARUP,
        "grammarup_extra": QuizCategory.GRAMMARUP_EXTRA,
        "wordsup": QuizCategory.WORDSUP,
        "readup": QuizCategory.READUP,
    }
    return mapping.get(source_name, QuizCategory.LISTENUP)


def _raw_to_question(
    raw: dict[str, Any],
    category: QuizCategory,
    index: int,
) -> QuizQuestion:
    """生データを QuizQuestion モデルに変換"""
    # question_id の生成: 既存IDがあればそれを使用、なければカテゴリ+インデックス
    qid = raw.get("id", f"{category.value}_{index:04d}")

    return QuizQuestion(
        question_id=qid,
        category=category,
        index=index,
        diff=raw.get("diff", ""),
        axis=raw.get("axis", ""),
        answer=raw.get("answer", ""),
        choices=raw.get("choices", []),
        expl=raw.get("expl", ""),
        # ListenUp
        text=raw.get("text"),
        ja=raw.get("ja"),
        audio=raw.get("audio"),
        kp=raw.get("kp"),
        # GrammarUp
        id=raw.get("id"),
        stem=raw.get("stem"),
        tags=raw.get("tags"),
        rule=raw.get("rule"),
        # WordsUp
        word=raw.get("word"),
        # ReadUp
        pid=raw.get("pid"),
        passage=raw.get("passage"),
        question=raw.get("question"),
        # 元データ保持
        raw_data=raw,
    )


def extract_all(config: Config) -> list[QuizQuestion]:
    """全クイズソースから問題を抽出"""
    all_questions: list[QuizQuestion] = []

    for source_name, path in config.quiz_sources.items():
        try:
            raw_data = parse_questions_js(path)
            category = _detect_category(source_name)
            for i, raw in enumerate(raw_data):
                q = _raw_to_question(raw, category, i)
                all_questions.append(q)
        except Exception as e:
            logger.error("ソース %s の読み込みに失敗: %s", source_name, e)

    logger.info("合計 %d 問を抽出完了", len(all_questions))
    return all_questions
