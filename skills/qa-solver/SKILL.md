---
name: qa-solver
model: claude-sonnet-4-6
description: |
  QAソルバー。ListenUp・GrammarUp・kioku-shinaiの問題を解答者として解き品質を検証する。
  「問題をテストして」「QAチェックして」「問題の品質を確認して」で使用。
user-invocable: true
---

# QAソルバー（問題品質検査担当）

英語学習3サービス（ListenUp・GrammarUp・kioku-shinai）の問題を
**解答者として解き**、品質を検証する専任スキル。

## 役割

問題を「教える側」ではなく「解く側」の視点でチェックする。
正解を見ずに回答し、自分の回答と設定された正解が一致しなければフラグを立てる。

## 実行タイミング

- **毎日朝**、COOが日次タスクを開始したタイミングで呼び出される
- または `/qa-solver` で手動実行

## 検査対象

| サービス | ファイル | サンプル数/日 |
|---|---|---|
| GrammarUp | `~/projects/claude/native-real/grammar/questions.js` | 30問 |
| ListenUp | `~/projects/claude/native-real/listening/questions.js` | 20問 |
| kioku-shinai | `~/projects/claude/native-real/kioku-shinai/data/words/*.json` | 10語根（各1問） |

合計: 毎日約60問をランダムサンプリングして解く。

## 検査手順

### Step 1: ランダムサンプリング

各サービスのデータファイルを読み込み、ランダムに問題を抽出する。
**前回チェック済みIDを記録し、未チェック問題を優先する**（ローテーション）。

チェック履歴ファイル: `~/projects/claude/native-real/qa-solver-log/history.json`
```json
{
  "grammar_checked": ["g001", "g002", ...],
  "listening_checked": [1, 2, ...],
  "kioku_checked": ["duct:produce", "port:export", ...],
  "last_run": "2026-03-24"
}
```

### Step 2: 問題を解く（正解を見ない）

**重要: 各問題について、answer フィールドを読まずに自分で解答する。**

#### GrammarUp の解き方
1. stem（空欄付き英文）と choices（5択）を読む
2. 文法知識に基づいて正解を1つ選ぶ
3. 「他の選択肢も正解になりうるか」を検討する
4. 自分の回答を記録する

#### ListenUp の解き方
1. text（英文スクリプト）と choices（5択の日本語意味）を読む
2. 英文の意味に最も合う選択肢を選ぶ
3. 自分の回答を記録する

#### kioku-shinai の解き方
1. formats 内のクイズを読む
2. 語源の知識に基づいて回答する
3. 自分の回答を記録する

### Step 3: 正解と照合

自分の回答と設定された answer を比較する。

#### 判定パターン

| パターン | 判定 | アクション |
|---|---|---|
| 自分の回答 = answer | ✅ PASS | 記録のみ |
| 自分の回答 ≠ answer（自分が間違い） | ✅ PASS | 記録のみ（問題は正しい） |
| 自分の回答 ≠ answer（自分も正しい可能性） | ⚠️ FLAG | 詳細レビューに回す |
| answer が文法的に間違い | ❌ FAIL | 即修正対象 |
| 複数の choices が正解になりうる | ❌ FAIL | 即修正対象 |
| 問題文が曖昧・不自然 | ⚠️ FLAG | 詳細レビューに回す |

### Step 4: レポート出力

結果を以下のパスに保存:
```
~/projects/claude/native-real/qa-solver-log/YYYY-MM-DD.md
```

レポート形式:
```markdown
# QAソルバー日次レポート（YYYY-MM-DD）

## サマリー
- GrammarUp: 30問中 XX問PASS / XX問FLAG / XX問FAIL
- ListenUp: 20問中 XX問PASS / XX問FLAG / XX問FAIL
- kioku-shinai: 10問中 XX問PASS / XX問FLAG / XX問FAIL

## FAIL（即修正が必要）
| サービス | ID | 問題点 | 修正案 |
|---|---|---|---|
| GrammarUp | gXXX | ... | ... |

## FLAG（詳細レビュー推奨）
| サービス | ID | 問題点 |
|---|---|---|
| ... | ... | ... |

## 検査詳細
### GrammarUp
| ID | 自分の回答 | 設定正解 | 判定 | 備考 |
|---|---|---|---|---|
| gXXX | is | is | PASS | |
| gXXX | can | does | FLAG | canも文法的に正解になりうる |
```

### Step 5: 修正の実行

- **FAIL**: レポート内の修正案に基づいて即座に修正。git commit & push。
- **FLAG**: レポートに記録し、部長（native-real-bucho）に報告。人間判断を仰ぐ。

## 複数正解チェックリスト（解答時に参照）

GrammarUp の問題を解く際、以下のパターンに特に注意する:

1. need + -ing = need + to be pp（両方正解）
2. suggest/recommend + 原形 / should + 原形（両方正解）
3. who / that（制限用法・人が先行詞）
4. which / that（制限用法・物が先行詞）
5. any / much / some（疑問文の文脈次第）
6. flat adverbs: loud/loudly, quick/quickly, slow/slowly
7. due to / because of（ほぼ同義）
8. despite / in spite of（同義）
9. will / be going to（未来表現で互換の場合）
10. one / a/an（数量として自然な場合）

## ディレクトリ構成

```
native-real/qa-solver-log/
├── history.json        # チェック履歴（ローテーション管理）
├── 2026-03-24.md       # 日次レポート
├── 2026-03-25.md
└── ...
```

## COOとの連携

COOが朝の日次タスクを開始する際、以下の順序で実行:
1. `/qa-solver` を実行（またはCOOスキルから自動呼び出し）
2. レポートを確認
3. FAILがあれば即修正を指示
4. FLAGがあれば部長に確認を依頼

## 注意事項

- **自分もハルシネーションする前提で動く**。「自分が正しい」と思っても、辞書・文法書で裏取りしてからFAIL判定する
- GrammarUp の文法判断は Purdue OWL、Cambridge Grammar 等の権威ある文法書を基準にする
- ListenUp は「英文の意味として最も適切か」を基準にする
- kioku-shinai は語源の正確性（EtymOnline 等）を基準にする
