#!/usr/bin/env python3
"""
SaaS-D: 英語学習コンテンツ生成デモスクリプト
Claude API (claude-haiku-4-5) を使って英文法4択問題を自動生成し、
JSON / CSV 形式でエクスポートする。

Usage:
    python generate_questions.py [--level 初級|中級|上級] [--category 時制|冠詞|前置詞|関係詞|助動詞]
                                  [--target TOEIC|英検|一般] [--count 5] [--output json|csv|both]

Environment:
    ANTHROPIC_API_KEY  Anthropic API キー（必須）
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import anthropic

# ── 定数 ──────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"  # コスト最適化
MAX_TOKENS = 4096

SYSTEM_PROMPT = """あなたは英語教育のプロフェッショナルです。
指定された条件に従い、自然な英語を使った高品質な4択問題を生成します。

出力は必ず以下の JSON 配列形式のみで返してください（前後に説明文を付けないこと）:
[
  {
    "question": "問題文（英文）",
    "options": {"a": "選択肢A", "b": "選択肢B", "c": "選択肢C", "d": "選択肢D"},
    "correct": "a",
    "explanation": "解説文（50字以内の日本語）",
    "category": "カテゴリ名",
    "level": "レベル"
  }
]

品質基準:
- 問題文は自然な英語を使うこと
- 誤答選択肢は紛らわしいが明確に誤りであること
- 解説は簡潔・明確な日本語で
- 重複する問題を生成しないこと"""

# ── メイン生成関数 ─────────────────────────────────────

def generate_questions(
    level: str = "中級",
    category: str = "時制",
    target: str = "TOEIC",
    count: int = 5,
    api_key: str | None = None,
) -> list[dict]:
    """Claude API で英文法問題を生成して辞書リストで返す。"""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY 環境変数が設定されていません。\n"
            "  export ANTHROPIC_API_KEY='your-api-key'"
        )

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = (
        f"以下の条件で英語4択問題を {count} 問生成してください。\n\n"
        f"条件:\n"
        f"- レベル: {level}（初級/中級/上級）\n"
        f"- カテゴリ: {category}\n"
        f"- 対象試験: {target}\n"
        f"- 問題数: {count}\n\n"
        "JSON 配列のみ返してください。"
    )

    # プロンプトキャッシュを使ってコストを削減
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # キャッシュ有効化
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # JSON ブロックが含まれる場合は抽出
    if "```" in raw:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        raw = raw[start:end]

    questions = json.loads(raw)

    # ID を付与
    for i, q in enumerate(questions, start=1):
        q.setdefault("id", f"{category[:2].upper()}-{level[0]}-{i:03d}")

    print(
        f"[生成完了] {len(questions)}問生成 "
        f"(入力: {response.usage.input_tokens} tok, "
        f"出力: {response.usage.output_tokens} tok)"
    )
    return questions


# ── エクスポート関数 ──────────────────────────────────

def export_json(questions: list[dict], path: Path) -> None:
    """native-real questions.js 互換の JSON 形式で保存する。"""
    output = {
        "meta": {
            "generated_by": "saas-d-content-generator",
            "model": MODEL,
            "count": len(questions),
        },
        "questions": questions,
    }
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[JSON] {path} に {len(questions)}問を保存しました")


def export_csv(questions: list[dict], path: Path) -> None:
    """Excel / Google スプレッドシート対応の CSV 形式で保存する。"""
    fieldnames = ["id", "question", "option_a", "option_b", "option_c", "option_d",
                  "correct", "explanation", "category", "level"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM付きでExcel対応
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in questions:
            opts = q.get("options", {})
            writer.writerow({
                "id": q.get("id", ""),
                "question": q.get("question", ""),
                "option_a": opts.get("a", ""),
                "option_b": opts.get("b", ""),
                "option_c": opts.get("c", ""),
                "option_d": opts.get("d", ""),
                "correct": q.get("correct", ""),
                "explanation": q.get("explanation", ""),
                "category": q.get("category", ""),
                "level": q.get("level", ""),
            })
    print(f"[CSV]  {path} に {len(questions)}問を保存しました")


# ── CLI エントリポイント ──────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SaaS-D: Claude API を使った英語問題自動生成デモ"
    )
    parser.add_argument("--level", default="中級",
                        choices=["初級", "中級", "上級"], help="難易度")
    parser.add_argument("--category", default="時制",
                        choices=["時制", "冠詞", "前置詞", "関係詞", "助動詞",
                                 "比較", "仮定法", "受動態", "不定詞", "動名詞"],
                        help="文法カテゴリ")
    parser.add_argument("--target", default="TOEIC",
                        choices=["TOEIC", "英検", "一般"], help="対象試験")
    parser.add_argument("--count", type=int, default=5,
                        help="生成問題数（1〜20）")
    parser.add_argument("--output", default="both",
                        choices=["json", "csv", "both"], help="出力形式")
    parser.add_argument("--outdir", default=".",
                        help="出力ディレクトリ（デフォルト: カレント）")
    args = parser.parse_args()

    if not 1 <= args.count <= 20:
        print("[ERROR] --count は 1〜20 の範囲で指定してください")
        sys.exit(1)

    print(f"[設定] レベル={args.level} カテゴリ={args.category} "
          f"対象={args.target} 問題数={args.count}")
    print(f"[生成中] Claude API ({MODEL}) を呼び出しています...")

    try:
        questions = generate_questions(
            level=args.level,
            category=args.category,
            target=args.target,
            count=args.count,
        )
    except (anthropic.APIError, json.JSONDecodeError) as e:
        print(f"[ERROR] 生成に失敗しました: {e}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"questions_{args.category}_{args.level}_{args.target}"

    if args.output in ("json", "both"):
        export_json(questions, outdir / f"{stem}.json")
    if args.output in ("csv", "both"):
        export_csv(questions, outdir / f"{stem}.csv")

    # プレビュー表示
    print("\n--- 生成サンプル（1問目） ---")
    q = questions[0]
    print(f"Q: {q['question']}")
    for k, v in q["options"].items():
        mark = " ← 正解" if k == q["correct"] else ""
        print(f"  ({k}) {v}{mark}")
    print(f"解説: {q['explanation']}")


if __name__ == "__main__":
    main()
