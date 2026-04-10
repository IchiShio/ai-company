# ファクトチェック出典リスト

## 語源学（Etymology）

### Tier 1: 最優先出典（必ず確認）
| 出典 | URL/アクセス方法 | 特徴 |
|---|---|---|
| EtymOnline | `https://www.etymonline.com/word/{word}` | 最も網羅的な無料語源辞典。Douglas Harper編纂 |
| Wiktionary | `https://en.wiktionary.org/wiki/{word}` | Etymology セクション。複数言語の派生を確認可能 |

### Tier 2: 補助出典（Tier 1で不十分な場合）
| 出典 | URL/アクセス方法 | 特徴 |
|---|---|---|
| Oxford English Dictionary | oed.com（有料） | 最も権威がある。アクセスできない場合はTier 1で代替 |
| American Heritage Dictionary | ahdictionary.com | Indo-European Roots付録が有用 |
| Merriam-Webster | merriam-webster.com | Word History セクション |

### 検証URL生成ルール
```
EtymOnline:  https://www.etymonline.com/word/{word}
Wiktionary:  https://en.wiktionary.org/wiki/{word}#Etymology
```

## 認知言語学（Cognitive Linguistics）

### 主要文献と対応する概念
| 文献 | 著者 | 年 | 主な概念 |
|---|---|---|---|
| Metaphors We Live By | Lakoff & Johnson | 1980 | 概念メタファー全般（UP IS MORE, IMPORTANT IS HEAVY等） |
| Women, Fire, and Dangerous Things | Lakoff | 1987 | カテゴリ化、放射状カテゴリ、overの多義性分析 |
| The Body in the Mind | Johnson | 1987 | イメージスキーマ（CONTAINER, PATH, FORCE等） |
| The Semantics of English Prepositions | Tyler & Evans | 2003 | 前置詞の原型的意味と派生意味のネットワーク |
| Word Power: Phrasal Verbs and Compounds | Rudzka-Ostyn | 2003 | 句動詞の認知的分析、particle の意味体系 |
| A Cognitive Approach to English Phrasal Verbs | Lindner | 1981 | OUT, UP等の空間粒子の体系的分類 |
| Philosophy in the Flesh | Lakoff & Johnson | 1999 | 身体性認知の哲学的基盤 |

### 主要な概念メタファー一覧（Lakoff & Johnson 1980由来）
確認済みのメタファーのみ。これ以外を使う場合は出典を追加確認すること。

- UP IS MORE / DOWN IS LESS
- UP IS GOOD / DOWN IS BAD
- UP IS ACTIVE / DOWN IS PASSIVE（CONSCIOUS IS UP / UNCONSCIOUS IS DOWN）
- IMPORTANT IS HEAVY（SIGNIFICANT IS HEAVY）
- KNOWING IS SEEING（UNDERSTANDING IS SEEING）
- IDEAS ARE OBJECTS
- COMMUNICATION IS SENDING
- TIME IS MONEY
- ARGUMENT IS WAR
- LOVE IS A JOURNEY
- LIFE IS A JOURNEY
- RELATIONSHIPS ARE CONTAINERS
- STATES ARE LOCATIONS
- CHANGE IS MOTION
- PURPOSES ARE DESTINATIONS
- DIFFICULTIES ARE IMPEDIMENTS TO MOTION
- HAPPY IS UP / SAD IS DOWN
- RATIONAL IS UP / EMOTIONAL IS DOWN

### 主要なイメージスキーマ一覧（Johnson 1987由来）
- CONTAINER（容器）
- PATH（経路: SOURCE → PATH → GOAL）
- FORCE（力: COMPULSION, BLOCKAGE, COUNTERFORCE, REMOVAL OF RESTRAINT）
- BALANCE（均衡）
- UP-DOWN（上下）
- LINK（結合）
- CENTER-PERIPHERY（中心-周辺）
- PART-WHOLE（部分-全体）

### 前置詞/副詞の原型的意味（Tyler & Evans 2003由来）
| particle | 原型的意味 | 代表的な派生意味 |
|---|---|---|
| over | 上方を越える | 完了、超過、支配、繰り返し |
| out | 容器の外へ | 消滅、出現、完了、拡散 |
| up | 上方向 | 完了、増加、出現、活性化 |
| off | 接触面からの分離 | 切断、開始、逸脱、完了 |
| through | 経路を通り抜ける | 完遂、貫通、手段 |
| down | 下方向 | 減少、記録、抑圧、完了 |
| on | 接触・支持 | 継続、作動、負担 |
| in | 容器の中へ | 包含、参加、状態変化 |

## チェック時の注意

### False Cognate（偽の同根語）に注意
見た目が似ているが語源が異なる単語ペア:
- island（古英語 īegland）と isle（ラテン語 insula）→ 同根ではない
- ache（古英語 acan）と ache（ギリシャ語?）→ 綴りの混乱あり
- ear（耳: 古英語 ēare）と ear（穂: 古英語 ēar）→ 同形異義

### Folk Etymology（民間語源）に注意
広く信じられているが間違っている語源:
- "posh" = "Port Out, Starboard Home" → 根拠なし（EtymOnline: origin unknown）
- "fuck" = 各種頭字語説 → 全て都市伝説
- "sincere" = "without wax (sine cera)" → 民間語源（実際はラテン語 sincerus「純粋な」）
- "golf" = "Gentlemen Only Ladies Forbidden" → 完全な作り話

これらの民間語源を事実として使うことは**絶対禁止**。
