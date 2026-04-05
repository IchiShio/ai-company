# 収入自動化・複数化バックログ

> **方针**: 全タスクは収入の自動化・複数化を目的とする。
> アイドル時間に自律実行する。完了したら次のタスクへ。

---

## Tier 1：即収益（最優先）

### [ ] note有料記事 - oac新作
- **収益**: note販売（¥980〜¥3,980）
- **パイプライン**: `/oac-bucho` → `/oac-writer` → `/note-publisher`
- **候補テーマ**: Claude Codeで月収を作る具体的な方法、AIエージェント組織の作り方
- **実行方法**: `/oac-bucho review` でネタ選定→執筆→公開

### [ ] note有料記事 - careermigaki新作
- **収益**: note販売（¥500〜¥1,980）
- **パイプライン**: `/cm-bucho` → `/cm-seo-writer` → `/note-publisher`
- **候補テーマ**: 転職成功事例、面接対策、年収交渉術
- **実行方法**: `/cm-bucho post` でネタ選定→執筆→公開

### [x] native-real アフィリ強化
- **収益**: アフィリエイトCVR改善
- **実行方法**: `/native-real-seo-pipeline` → アフィリCTA強化
- **対象**: /ranking/ ページのCTA最適化、個別サービスレビュー追加

---

## Tier 2：新収益柱

### [x] ニッチ比較サイト（native-realモデル複製）
- **収益**: アフィリエイト
- **ジャンル候補**: プログラミングスクール比較 / 副業ツール比較 / AI活用ツール比較
- **技術**: 静的HTML、GitHub Pages（native-realと同構成）
- **実行方法**: ジャンル選定→サイト構造設計→コンテンツ生成→デプロイ
- **完了**: 2026-04-01 プログラミングスクール比較サイト設計・コンテンツ生成（`projects/programming-school-comparison/`）。index.html・ranking/index.html・README.md・spec.md作成。デプロイはprog-school.net新規リポジトリ作成後に実施。

### [x] メールリスト×ステップメール
- **収益**: 自社商品・アフィリへの誘導
- **対象**: native-real読者（英語学習者）
- **実行方法**: Beehiiv設定→ステップメール設計→CTAページ作成
- **完了**: 2026-04-02 CTAページ作成（`/newsletter/`）・7日間ステップメール設計書作成（`docs/newsletter-stepmail.md`）。Beehiiv埋め込みフォーム・Day0〜Day7全8通設計・A8アフィリCTA組み込み済み。

---

## Tier 3：自社商品SaaS（優先度順）

### [x] D: 英語学習コンテンツ生成SaaS ⭐️最優先
- **収益**: B2B月額サブスク（英語教室・スクール向け）
- **コア機能**:
  - ListenUp/GrammarUp形式の問題を自動生成
  - Claude APIで問題生成 → 音声合成 → エクスポート
  - ターゲット: 英語教室運営者、教材制作者
- **技術候補**: Next.js + Stripe + Claude API
- **MVP**: 問題生成フォーム → JSON/CSV出力（無料トライアル付き）
- **実行方法**: MVP設計→実装→Vercelデプロイ→Gumroadで先行販売
- **完了**: 2026-03-30 MVP設計書作成（`projects/saas-d-content-generator/`）

### [x] B: Claude Code活用SaaS（ひとりAI会社モデル販売）
- **収益**: 月額サブスク or 初期費用
- **コア機能**:
  - AIエージェント組織のテンプレートセット販売
  - セットアップ支援ツール
- **実行方法**: oac-buchoと連携してコンテンツ設計
- **完了**: 2026-04-01 MVP設計書作成（`projects/saas-b-claude-code-saas/`）。README.md・spec.md作成。Gumroad販売・GitHub Pages LP・月額サポートプランを設計。

### [x] A: X自動化SaaS
- **収益**: 月額サブスク
- **コア機能**: 複数アカウント管理・スケジュール投稿・パフォーマンス分析
- **注意**: 競合多い。差別化（AI生成+自動PDCA）が必須
- **完了**: 2026-04-02 MVP設計書作成（`projects/saas-a-x-automation/`）。README.md・spec.md作成。Claude API投稿生成・PDCA自動化・Stripe課金・X API v2連携を設計。

### [x] C: SEO自動化SaaS
- **収益**: 月額サブスク
- **実行方法**: native-realパイプラインのサービス化
- **完了**: 2026-04-02 MVP設計書作成（`projects/saas-c-seo-automation/`）。README.md・spec.md作成。静的サイト対応・日本語SEO特化・native-realパイプライン参照実装を設計。

---

## native-real MAU強化（M&A戦略）

### [x] GrammarUp 問題追加（目橐1000問）
- 1005問 → 2026-03-30: 20問追加（g1048-g1067）、計1025問
- 2026-04-02: 20問追加（g1068-g1087）、計1045問（条件文・受動態・比較・仮定法・強調構文など）
- 2026-04-02: 20問追加（g1088-g1107）、計1065問（推量過去・数量詞・間接疑問・動名詞vs不定詞・前置詞・使役・否定接頭辞など）
- 2026-04-03: 20問追加（g1108-g1127）、計1085問（現在完了・目的不定詞・逆接接続詞・受動態・完了不定詞・時間前置詞・倒置・比例比較・動名詞・関係詞what・助動詞・仮定法wish・楽器冠詞・強調構文・期限by・受動分詞構文・so that・had better・付加疑問・未来完了）
- 2026-04-03: 20問追加（g1128-g1147）、計1105問（状態動詞・whose・不定詞形容詞的用法・too-to・enough-to・just現在完了・might・仮定法過去完了・結果不定詞・suggest that・関係副詞where・either-or・感情分詞・despite・used to・seem to・受動進行形・関係代名詞what・unless・make+O+形容詞）
- 2026-04-03: 20問追加（g1148-g1167）、計1125問（since/for・so that・wish仮定法過去完了・交通手段by・強調構文・as-as同等比較・過去完了・however譲歩・使役have+O+過去分詞・形容詞enough-to・動名詞主語・worried about・未来完了will have・関係代名詞whom・not only but also・too-to・不定詞受動態・at時刻・否定副詞倒置・although逆接）
- 2026-04-03: 20問追加（g1168-g1187）、計1145問（関係副詞when・現在分詞形容詞的用法・such that結果・until継続・時制の一致・would rather・the比較級比例・分詞構文・非制限用法which・whoever・stop+動名詞・現在完了進行形・be known to・感嘆文what・suggest仮定法現在・if only仮定法・during vs for・look forward to・a few vs few・in case予防）
- 2026-04-03: 20問追加（g1188-g1207）、計1165問（ask+O+to-V・already肯定・both-and・as soon as・get受動態・形式主語it・過去進行形・must義務・although逆接・what関係代名詞・as if仮定法・mind+動名詞・強調do・used to過去習慣・最上級ever・目的不定詞・it takes時間・by the time過去完了・have+O+過去分詞・neither倒置）
- 2026-04-04: 20問追加（g1208-g1227）、計1185問（whose所有格・have been to経験・仮定法過去・形式目的語it・every vs each・although逆接・much+比較級・something形容詞的用法・時制の一致・分詞構文・not only but also・過去進行受動態・the+形容詞複数・on+動名詞・仮定法現在necessity・過去完了進行形・hardly否定副詞・関係副詞why・the first time現在完了・look forward to動名詞）
- 2026-04-04: 20問追加（g1228-g1247）、計1205問（since/for・受動不定詞・either-or・what名詞節・should助言・no sooner than・be worried about・suggest仮定法現在・too-to・過去完了進行形・as long as・let使役・enough-to・in spite of・最上級the・never倒置・by期限・wish過去完了・remind-to・未来完了）
- 2026-04-05: 20問追加（g1248-g1267）、計1225問（現在完了経験・in order to目的・現在完了受動態・感情前置詞at・仮定法現在suggest・動名詞avoid・while接続詞・使役make受動態・worth動名詞・強調構文it・時制の一致・混合仮定法・on特定の日・否定付加疑問・so-that結果・too-to否定・非制限用法who・句動詞give up・否定副詞倒置hardly・unless）
- 2026-04-05: 20問追加（g1268-g1287）、計1245問（関係代名詞that制限用法・depend on前置詞・比例比較the比較級・仮定法過去were・not A but B・完了分詞構文having pp・should have過去後悔・間接疑問how・as soon as possible・動名詞の意味上主語所有格・seem to have pp・so do I倒置同意・were to仮定法・目的格関係代名詞省略・provided that条件・what is more追加・stop動名詞・不定詞受動態to be pp・whenever複合関係副詞・句動詞look up）
- 2026-04-05: 20問追加（g1288-g1307）、計1265問（現在完了継続for・so that目的・使役受動have pp・仮定法現在recommend・at時刻・完了分詞構文having pp・even though逆接・whose所有格関係詞・should助言・強調構文it was that・much比較級強調・No sooner倒置・unless条件・動名詞所有格主語・so that結果・wish仮定法過去完了・the最上級・as if仮定法・受動態be pp・混合仮定法）
- 2026-04-05: 20問追加（g1308-g1327）、計1285問（現在完了経験been・目的to不定詞・非制限用法which・as-as同等比較・間接疑問・too-to・during前置詞・現在完了受動態・仮定法過去were・worth動名詞・付加疑問・let使役・while対比・関係副詞where・-ing/-ed感情形容詞・except除外・not only but also・分詞構文現在分詞・might弱い推量・should have過去後悔）
- 2026-04-05: 20問追加（g1328-g1347）、計1305問（現在完了just・進行受動態・whose・whether・no matter what・avoid動名詞・as if仮定法・in addition to動名詞・demand仮定法現在・過去完了・it is time仮定法・less than・so as not to・how long・prefer A to B・having完了分詞構文・be supposed to・once条件・過去分詞後置修飾・only when倒置）

### [x] NewsUp MVP実装
- VOA記事ベースのニュース英語読解クイズ
- **完了**: 2026-03-31: 10記事・3問/記事実装（`/newsup/`）

### [x] kioku-shinai 語根追加
- 無料600語完成を目指す
- **完了**: 2026-04-01: 30語根×20語=600語達成。index.htmlのcount表示を全語根20語に修正

---

## 完了済み
<!-- 完了したタスクをここに移動 -->

---

## メモ
- StarterForge: Stripe設定完了まで保留
- 英語学習系有料ツール → native-realで無料公開（MAU戦略）
