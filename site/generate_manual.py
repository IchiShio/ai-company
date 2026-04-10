#!/usr/bin/env python3
"""
generate_manual.py - Claude Code が直接生成した問題を staging.json に保存する
重複チェック・バリデーションを実施してから書き込む
"""
import json, re
from pathlib import Path

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"
STAGING_JSON = REPO_ROOT / "listening" / "staging.json"

# ──────────────────────────────────────────────
# 手動生成問題 100問
# reduction:35 / speed:18 / vocab:20 / distractor:22 / context:5
# diff分布: lv1×25, lv2×30, lv3×25, lv4×15, lv5×5
# ──────────────────────────────────────────────
QUESTIONS = [
  # ── REDUCTION lv1 (7問) ───────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "reduction",
    "text": "I'm gonna head out soon. See you tomorrow.",
    "ja": "もうすぐ出かけるよ。また明日。",
    "answer": "間もなく退席する",
    "choices": ["間もなく退席する", "頭を使って考える", "次の会議に向かう", "今から外出の準備をする", "遅れてもいいと伝えている"],
    "expl": "gonna は 'going to' の縮約形。'head out' は「出かける・立ち去る」という口語表現。",
    "kp": ["gonna", "head out"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "You wanna grab something to eat before we go?",
    "ja": "出発前に何か食べていく？",
    "answer": "食べてから出発しないか提案している",
    "choices": ["食べてから出発しないか提案している", "何かを掴んで持っていくよう頼んでいる", "出発前に買い物を提案している", "先に食べてきてほしいと頼んでいる", "食事の場所を確認している"],
    "expl": "wanna は 'want to' の縮約形。'grab something to eat' は「手軽に何か食べる」という口語表現。",
    "kp": ["wanna", "grab something to eat"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "Lemme just check my calendar real quick.",
    "ja": "ちょっとカレンダーを確認するね。",
    "answer": "すぐにスケジュールを確認する",
    "choices": ["すぐにスケジュールを確認する", "予定を代わりに確認してもらう", "今日の日程を変更したい", "急いでいるから後で確認する", "カレンダーを誰かに渡す"],
    "expl": "lemme は 'let me' の縮約形。'real quick' は「すぐに・手短に」という口語表現。",
    "kp": ["lemme", "real quick"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "I dunno. It's probably fine, but let's double-check anyway.",
    "ja": "わからないけど、たぶん大丈夫だとは思う。でも念のため確認しよう。",
    "answer": "不確かだが念のため確認を提案している",
    "choices": ["不確かだが念のため確認を提案している", "問題があると断言している", "確認は不要だと言っている", "相手に全て任せたいと伝えている", "既に確認済みだと言っている"],
    "expl": "dunno は 'don't know' の縮約形。'double-check' は「念のために確認する」。",
    "kp": ["dunno", "double-check"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "She's gotta submit it before the end of the day.",
    "ja": "彼女は今日中に提出しなければならない。",
    "answer": "今日中に提出する義務がある",
    "choices": ["今日中に提出する義務がある", "今日中に提出したいと思っている", "提出期限をいつにするか決める必要がある", "提出の許可をもらった", "提出先を確認している"],
    "expl": "gotta は 'has got to' の縮約形で、義務・必要性を表す。",
    "kp": ["gotta", "end of the day"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "It's kinda hard to explain, but I'll try.",
    "ja": "うまく説明するのが難しいんだけど、やってみるね。",
    "answer": "説明しにくいが努力すると言っている",
    "choices": ["説明しにくいが努力すると言っている", "説明を拒否している", "相手に説明を頼んでいる", "難しくないと言っている", "後で説明すると言っている"],
    "expl": "kinda は 'kind of' の縮約形で、「少し・なんとなく」と曖昧さを表す口語表現。",
    "kp": ["kinda", "hard to explain"]
  },
  {
    "diff": "lv1", "axis": "reduction",
    "text": "I hafta run a couple of errands before I head back.",
    "ja": "戻る前にいくつか用を済ませないといけない。",
    "answer": "戻る前にいくつかのタスクをこなす必要がある",
    "choices": ["戻る前にいくつかのタスクをこなす必要がある", "急いで走って戻る必要がある", "用事があるから先に帰ると言っている", "帰り道でエラーを修正する必要がある", "仕事が終わったら走りに行く予定"],
    "expl": "hafta は 'have to' の縮約形。'run errands' は「用事・雑務をこなす」という日常表現。",
    "kp": ["hafta", "run errands"]
  },
  # ── REDUCTION lv2 (11問) ──────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "reduction",
    "text": "Didja catch the announcement they made this morning?",
    "ja": "今朝のアナウンスを聞いた？",
    "answer": "今朝の発表を聞いたか確認している",
    "choices": ["今朝の発表を聞いたか確認している", "今朝の魚を捕まえたか聞いている", "午前中に何かを受け取ったか聞いている", "今朝の会議に出席したか確認している", "アナウンスを作ったのが誰か聞いている"],
    "expl": "Didja は 'Did you' の縮約形。'catch an announcement' は「アナウンスを聞く・掴む」という口語的表現。",
    "kp": ["Didja", "catch the announcement"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "Whadya do with the extra copies? I can't find them.",
    "ja": "余分なコピーはどうした？見つからないんだけど。",
    "answer": "余分なコピーをどこに置いたか尋ねている",
    "choices": ["余分なコピーをどこに置いたか尋ねている", "コピーが多すぎると文句を言っている", "コピーを探してほしいと頼んでいる", "コピーの部数が足りないと言っている", "コピー機の使い方を聞いている"],
    "expl": "Whadya は 'What did you' の縮約形。'do with' は「〜をどうする・〜をどこに置く」という表現。",
    "kp": ["Whadya", "do with"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "I shoulda checked the weather before we left. Now we're soaked.",
    "ja": "出発前に天気を確認しておくべきだった。今はびしょ濡れだ。",
    "answer": "出発前に確認しなかったことを後悔している",
    "choices": ["出発前に確認しなかったことを後悔している", "天気予報が間違っていたと批判している", "雨に降られて嬉しいと言っている", "今後は天気を確認すると約束している", "相手が確認すべきだったと非難している"],
    "expl": "shoulda は 'should have' の縮約形。過去の後悔を表す用法（should have + 過去分詞）。",
    "kp": ["shoulda", "soaked"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "We're gonna hafta reschedule if the client can't make it by noon.",
    "ja": "クライアントが正午までに来られないなら、予定を変更しなければならない。",
    "answer": "条件によっては予定変更が必要だと言っている",
    "choices": ["条件によっては予定変更が必要だと言っている", "正午には必ず間に合うと言っている", "クライアントは正午に来ると言っている", "自分が正午に来られないと伝えている", "スケジュールは変更しないと言っている"],
    "expl": "gonna は 'going to'、hafta は 'have to' の縮約形。連続した縮約に注意。",
    "kp": ["gonna hafta", "reschedule", "make it by noon"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "Doncha want to look it over before you sign?",
    "ja": "署名する前に目を通さなくていいの？",
    "answer": "署名前に内容を確認するよう促している",
    "choices": ["署名前に内容を確認するよう促している", "署名しなくていいと言っている", "代わりに確認してほしいと頼んでいる", "既に確認したか尋ねている", "署名が不要だと伝えている"],
    "expl": "Doncha は 'Don't you' の縮約形。'look it over' は「全体にざっと目を通す」という表現。",
    "kp": ["Doncha", "look it over", "sign"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "Whaddya say we take a quick break? Everyone looks exhausted.",
    "ja": "ちょっと休憩を取らない？みんな疲れているみたいだし。",
    "answer": "休憩を取ることを提案している",
    "choices": ["休憩を取ることを提案している", "話し合いを早く終わらせるよう求めている", "全員に帰宅を促している", "誰かが何かを言ったか確認している", "疲れているから早退すると言っている"],
    "expl": "Whaddya say は 'What do you say' の縮約形で、「〜はどう？」という提案表現。",
    "kp": ["Whaddya say", "take a quick break"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "I'm s'posed to be there by eight, but traffic's terrible.",
    "ja": "8時までに着くはずなんだけど、渋滞がひどい。",
    "answer": "8時に着く予定だが渋滞で遅れるかもしれない",
    "choices": ["8時に着く予定だが渋滞で遅れるかもしれない", "8時に出発する予定だと言っている", "渋滞のせいで8時に仕事が終わらないと言っている", "渋滞なら8時に来なくていいと言っている", "8時に交通状況を確認すると言っている"],
    "expl": "s'posed to は 'supposed to' の縮約形で、「〜する予定/義務がある」という表現。",
    "kp": ["s'posed to", "traffic's terrible"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "She musta left early—her jacket's not on the hook.",
    "ja": "彼女は早退したんだろう。ジャケットがフックにかかっていない。",
    "answer": "状況証拠から早退したと推測している",
    "choices": ["状況証拠から早退したと推測している", "ジャケットを誰かが盗んだと疑っている", "彼女が遅刻していると言っている", "今日は来なかったと確信している", "ジャケットをどこかに忘れたと言っている"],
    "expl": "musta は 'must have' の縮約形。'must have + 過去分詞' で過去の推測を表す。",
    "kp": ["musta", "left early", "not on the hook"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "C'mon, you oughta at least reach out and apologize.",
    "ja": "なあ、せめて連絡して謝るべきだよ。",
    "answer": "連絡して謝罪するよう強く促している",
    "choices": ["連絡して謝罪するよう強く促している", "相手が連絡してきた理由を聞いている", "謝罪しなくていいと言っている", "先に謝ってもらいたいと伝えている", "もっと努力するよう頼んでいる"],
    "expl": "C'mon は 'Come on' の縮約形で、催促・励ましに使う。oughta は 'ought to' の縮約形。",
    "kp": ["C'mon", "oughta", "reach out", "apologize"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "Didja hear they're pushing the launch back to Q3?",
    "ja": "ローンチをQ3に延期するって聞いた？",
    "answer": "ローンチが延期されたという情報を共有している",
    "choices": ["ローンチが延期されたという情報を共有している", "Q3の資料を押してほしいと頼んでいる", "第3四半期の計画を立てるよう提案している", "ローンチがQ3に前倒しになったと言っている", "Q3の会議の予定を確認している"],
    "expl": "Didja は 'Did you' の縮約形。'push back' は「延期する・先送りにする」というビジネス表現。",
    "kp": ["Didja", "push back", "launch"]
  },
  {
    "diff": "lv2", "axis": "reduction",
    "text": "I'm gonna need ya to take another look at those figures.",
    "ja": "あの数字をもう一度確認してほしいんだけど。",
    "answer": "数字を再確認するよう依頼している",
    "choices": ["数字を再確認するよう依頼している", "数字を提出するよう命令している", "数字が間違っていると批判している", "新しい数字を計算してほしいと頼んでいる", "数字の見た目を改善するよう求めている"],
    "expl": "ya は 'you' の口語形。'take another look at' は「もう一度見直す・再確認する」という表現。",
    "kp": ["ya", "take another look at", "figures"]
  },
  # ── REDUCTION lv3 (10問) ──────────────────────────────────────────────────
  {
    "diff": "lv3", "axis": "reduction",
    "text": "I woulda called you sooner, but I had no idea things had gotten that bad.",
    "ja": "もっと早く電話すればよかったけど、そんなに悪くなっていたとは知らなかった。",
    "answer": "早く連絡しなかったことを後悔している",
    "choices": ["早く連絡しなかったことを後悔している", "これから電話すると言っている", "知っていたら連絡しなかったと言っている", "状況が悪くなったのは自分のせいだと認めている", "電話できなかった別の理由を述べている"],
    "expl": "woulda は 'would have' の縮約形。'would have + 過去分詞' は反実仮想（実際にはしなかったこと）を表す。",
    "kp": ["woulda", "had no idea", "gotten that bad"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "He shoulda flagged the issue sooner. Now we're dealing with a much bigger problem.",
    "ja": "もっと早くその問題を報告すべきだった。今ははるかに大きな問題に対処している。",
    "answer": "早期報告がなかったことを批判している",
    "choices": ["早期報告がなかったことを批判している", "問題が大きくなってから初めて気づいたと言っている", "今後は問題を素早く解決すると約束している", "自分が早く対処すればよかったと後悔している", "問題を無視するよう提案している"],
    "expl": "shoulda は 'should have' の縮約形。'flag an issue' は「問題を報告する・注意を引く」というビジネス表現。",
    "kp": ["shoulda", "flagged the issue", "dealing with"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "We'da been done by three if we hadn't run into that problem.",
    "ja": "あの問題に突き当たらなければ、3時には終わっていた。",
    "answer": "問題がなければもっと早く終わっていたという反実仮想",
    "choices": ["問題がなければもっと早く終わっていたという反実仮想", "3時までには必ず終わると言っている", "問題があったので3時に始めたと言っている", "3時以降に終わる見込みだと説明している", "問題を起こした人を批判している"],
    "expl": "We'da は 'We would have' の縮約形。'run into a problem' は「問題に直面する」。",
    "kp": ["We'da", "run into", "if we hadn't"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "Whaddya know, they actually came through. I honestly didn't think they would.",
    "ja": "やあ驚いた。本当にやり遂げたね。正直できないと思っていた。",
    "answer": "予想に反してうまくいったことへの驚き",
    "choices": ["予想に反してうまくいったことへの驚き", "彼らが何を知っているか確認している", "やっぱり無理だったことへの皮肉", "うまくいったのは知っていたと言っている", "次も同じように頑張るよう励ましている"],
    "expl": "Whaddya know は感嘆表現で「やあ、驚いた・なんと」という意味。'come through' は「期待に応える・やり遂げる」。",
    "kp": ["Whaddya know", "came through"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "I'm kinda thinking we oughta take a step back and rethink this.",
    "ja": "少し立ち止まって、これを再考した方がいいような気がしてる。",
    "answer": "一歩引いて再考することを提案している",
    "choices": ["一歩引いて再考することを提案している", "プロジェクトから撤退すべきだと主張している", "後退したことを後悔していると言っている", "考えるのをやめるよう提案している", "他の人に任せるよう提案している"],
    "expl": "kinda は 'kind of' の縮約形で、控えめな表現に使う。oughta は 'ought to' の縮約形。",
    "kp": ["kinda", "oughta", "take a step back", "rethink"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "You don't hafta commit right now—just lemmie know what you're thinking.",
    "ja": "今すぐ決めなくていいよ。今どう思っているか教えてくれればいい。",
    "answer": "今すぐ決断しなくていいが考えを共有してほしいと伝えている",
    "choices": ["今すぐ決断しなくていいが考えを共有してほしいと伝えている", "今すぐ決断が必要だと圧力をかけている", "考えを言わなくていいと言っている", "決断を他の人に任せると言っている", "意見を聞く必要はないと言っている"],
    "expl": "hafta は 'have to' の縮約形。lemmie は 'let me' の縮約形。'commit' は「決断する・確約する」。",
    "kp": ["hafta", "lemmie", "commit"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "It shoulda been resolved long before anyone had to escalate it.",
    "ja": "誰かがエスカレーションするずっと前に解決されているべきだった。",
    "answer": "もっと早い段階で解決すべきだったと批判している",
    "choices": ["もっと早い段階で解決すべきだったと批判している", "エスカレーションは正しい判断だったと言っている", "解決策を持っている人がいたと言っている", "問題がエスカレーションする前に解決したと言っている", "今後は早く対処すると約束している"],
    "expl": "shoulda は 'should have' の縮約形。'escalate' はビジネスで「上位に問題を引き上げる・報告する」という表現。",
    "kp": ["shoulda", "resolved", "escalate"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "C'mon, it's not like we couldn'ta predicted this would happen.",
    "ja": "なあ、こうなることを予測できなかったはずがないでしょ。",
    "answer": "問題を予測できたはずなのに対処しなかったと批判している",
    "choices": ["問題を予測できたはずなのに対処しなかったと批判している", "予測が難しかったことへの同情を示している", "予測できなかったのは仕方ないと言っている", "次は予測できると約束している", "相手だけが予測できたと非難している"],
    "expl": "couldn'ta は 'couldn't have' の縮約形。二重否定（it's not like we couldn't）で「できたはず」を強調。",
    "kp": ["couldn'ta", "predicted", "it's not like"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "D'ya think they'da gone for it if we'd sweetened the deal a bit?",
    "ja": "もう少し条件をよくしていたら、彼らは乗っていたと思う？",
    "answer": "条件改善があれば相手が合意したかを仮定で問いかけている",
    "choices": ["条件改善があれば相手が合意したかを仮定で問いかけている", "条件をよくするよう頼んでいる", "相手がすでに合意したと伝えている", "取引を改善することを提案している", "相手が断った理由を分析している"],
    "expl": "D'ya は 'Do you' の縮約形。they'da は 'they would have' の縮約形。'sweeten the deal' は「条件を有利にする・上乗せする」。",
    "kp": ["D'ya", "they'da", "sweeten the deal"]
  },
  {
    "diff": "lv3", "axis": "reduction",
    "text": "She musta been waiting outside for at least half an hour before anyone noticed.",
    "ja": "誰かが気づくまで、彼女は少なくとも30分は外で待っていたはずだ。",
    "answer": "誰にも気づかれないまま長時間待っていたと推測している",
    "choices": ["誰にも気づかれないまま長時間待っていたと推測している", "彼女は30分で来ると言っていた", "30分前に誰かが外に出たと言っている", "外で待つよう頼まれていたと言っている", "半時間後に誰かが来ると言っている"],
    "expl": "musta は 'must have' の縮約形。'must have been -ing' で過去の進行中の出来事への推測を表す。",
    "kp": ["musta", "been waiting", "before anyone noticed"]
  },
  # ── REDUCTION lv4 (5問) ──────────────────────────────────────────────────
  {
    "diff": "lv4", "axis": "reduction",
    "text": "He was s'posed to have confirmed it with finance before he went ahead.",
    "ja": "彼は先に進む前に経理と確認しておくべきだったんだ。",
    "answer": "手続きを飛ばして進めたことへの批判",
    "choices": ["手続きを飛ばして進めたことへの批判", "経理と確認が取れたと言っている", "経理が確認を断ったと言っている", "先に進む前に確認すると約束している", "確認の義務はなかったと主張している"],
    "expl": "s'posed to は 'supposed to' の縮約形。'have confirmed' は完了形で、先行して終わらせるべき行動を指す。",
    "kp": ["s'posed to", "confirmed with finance", "before he went ahead"]
  },
  {
    "diff": "lv4", "axis": "reduction",
    "text": "I woulda expected at least an acknowledgment, but nothing—not even a reply.",
    "ja": "せめて確認の返信くらいはあると思っていたのに—何もなし、返信すら来ない。",
    "answer": "最低限の反応すらなかったことへの失望",
    "choices": ["最低限の反応すらなかったことへの失望", "返信が遅れていることを説明している", "相手から何かを受け取ったと言っている", "返信が不要だと伝えている", "確認メールを送ったと言っている"],
    "expl": "woulda は 'would have' の縮約形。'acknowledgment' は「確認・受領の返信」というビジネス用語。",
    "kp": ["woulda", "acknowledgment", "not even a reply"]
  },
  {
    "diff": "lv4", "axis": "reduction",
    "text": "It's not like we didn'ta put in the effort. We tried everything we could.",
    "ja": "努力しなかったわけじゃない。できることは全部試した。",
    "answer": "十分な努力はしたと弁明している",
    "choices": ["十分な努力はしたと弁明している", "努力が足りなかったことを認めている", "これ以上の努力はできないと言っている", "相手の努力を認めている", "努力の方法が間違っていたと批判している"],
    "expl": "didn'ta は 'didn't' の口語的縮約形。'put in the effort' は「努力する・尽力する」という表現。",
    "kp": ["didn'ta", "put in the effort", "it's not like"]
  },
  {
    "diff": "lv4", "axis": "reduction",
    "text": "Whaddya think woulda happened if we hadn't caught that discrepancy early?",
    "ja": "あの不一致を早めに見つけていなかったら、どうなっていたと思う？",
    "answer": "早期発見がなかった場合の仮定シナリオを問いかけている",
    "choices": ["早期発見がなかった場合の仮定シナリオを問いかけている", "不一致を誰が見つけたか尋ねている", "早めに見つかったことへの安堵を伝えている", "問題の原因を調査するよう頼んでいる", "今後は早めに確認するよう促している"],
    "expl": "Whaddya は 'What do you' の縮約形。woulda は 'would have' の縮約形。'discrepancy' は「不一致・矛盾」。",
    "kp": ["Whaddya", "woulda", "discrepancy", "caught early"]
  },
  {
    "diff": "lv4", "axis": "reduction",
    "text": "I'm telling ya, we'da been in a completely different situation without that last-minute fix.",
    "ja": "本当に、あの土壇場の修正がなかったら、完全に違う状況になっていた。",
    "answer": "土壇場の修正がなければ深刻な結果になっていたと評価している",
    "choices": ["土壇場の修正がなければ深刻な結果になっていたと評価している", "土壇場の修正は無意味だったと言っている", "もう少しで修正できなかったと言っている", "最後に別の問題が発生したと言っている", "土壇場の修正を誰がしたか述べている"],
    "expl": "we'da は 'we would have' の縮約形。'last-minute fix' は「土壇場の修正」というビジネス表現。",
    "kp": ["we'da", "last-minute fix", "I'm telling ya"]
  },
  # ── REDUCTION lv5 (2問) ──────────────────────────────────────────────────
  {
    "diff": "lv5", "axis": "reduction",
    "text": "Woulda, coulda, shoulda—none of that helps now. What we gotta do is figure out the next move.",
    "ja": "あれができた、これができた、すべきだった—そんなこと今は関係ない。今やるべきことは次の手を考えることだ。",
    "answer": "過去への後悔より前進することを強調している",
    "choices": ["過去への後悔より前進することを強調している", "過去の失敗を一つずつ振り返っている", "次の計画を断念するよう言っている", "後悔しても仕方ないことへの同情を示している", "誰かを責めながら解決策を求めている"],
    "expl": "'Woulda, coulda, shoulda' は決まり文句で「あれができた、これもできたはずなのに（でも今さら遅い）」という後悔を表す。",
    "kp": ["woulda coulda shoulda", "gotta", "figure out the next move"]
  },
  {
    "diff": "lv5", "axis": "reduction",
    "text": "I'da thought by now they'da at least figured out why it keeps happening, but apparently not.",
    "ja": "今頃にはなぜ繰り返し起きるのかくらい分かっていると思っていたのに、まだらしい。",
    "answer": "原因究明がまだできていないことへの呆れ",
    "choices": ["原因究明がまだできていないことへの呆れ", "原因がやっと判明したと安堵している", "問題が再発しないと約束している", "彼らに調査を依頼したと言っている", "問題の原因を説明している"],
    "expl": "I'da は 'I would have'、they'da は 'they would have' の縮約形。繰り返す縮約形が高度な聞き取りを必要とする。",
    "kp": ["I'da", "they'da", "figured out why", "keeps happening"]
  },
  # ── SPEED lv1 (4問) ──────────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "speed",
    "text": "C'mon, we're gonna miss our train. We gotta leave now.",
    "ja": "ほら、電車に乗り遅れる。今すぐ出なきゃ。",
    "answer": "急いで出発するよう促している",
    "choices": ["急いで出発するよう促している", "電車に乗らないことを提案している", "もう電車に乗り遅れたと言っている", "電車の時刻を確認するよう言っている", "急がなくていいと言っている"],
    "expl": "C'mon は 'Come on' の縮約形。fast speechでは連音で素早く発音される。",
    "kp": ["C'mon", "gonna miss", "gotta leave"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Canya do me a favor and forward that email to everyone?",
    "ja": "そのメールを全員に転送してもらえる？",
    "answer": "メール転送を頼んでいる",
    "choices": ["メール転送を頼んでいる", "メールのアドレスを教えてほしいと言っている", "全員に連絡を取るよう言っている", "メールを削除するよう頼んでいる", "自分がメールを転送したと伝えている"],
    "expl": "Canya は 'Can you' の速読み縮約形。fast speechでは 'Can you' が 'canya' と発音される。",
    "kp": ["Canya", "do me a favor", "forward"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Djever try working from home full time? It's really different.",
    "ja": "フルタイムで在宅勤務したことある？全然違うよ。",
    "answer": "フルタイム在宅勤務の経験があるか聞いている",
    "choices": ["フルタイム在宅勤務の経験があるか聞いている", "在宅勤務を始めるよう勧めている", "在宅勤務の欠点を説明しようとしている", "フルタイム勤務に戻るよう言っている", "在宅勤務は予想通りだと言っている"],
    "expl": "Djever は 'Did you ever' の速読み縮約形。経験を尋ねる表現。",
    "kp": ["Djever", "full time", "really different"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "They ready yet? We've been sitting here forever.",
    "ja": "まだ準備できてないの？ずっと待ってるんだけど。",
    "answer": "長い待ち時間への苛立ちと準備の確認",
    "choices": ["長い待ち時間への苛立ちと準備の確認", "準備が終わったと報告している", "少し待つよう言っている", "ここが気に入ったと言っている", "何かを手伝うよう申し出ている"],
    "expl": "fast speechでは 'They are' が 'They're' を超えてさらに短縮される。'sitting here forever' は誇張表現。",
    "kp": ["They ready", "sitting here forever"]
  },
  # ── SPEED lv2 (6問) ──────────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "speed",
    "text": "Howdya manage to finish it so fast? That usually takes me all day.",
    "ja": "どうやってそんなに早く終わらせたの？いつもは一日かかるのに。",
    "answer": "素早く終わらせた方法への驚きと感嘆",
    "choices": ["素早く終わらせた方法への驚きと感嘆", "もっと早く終わるよう促している", "急いでやったから品質が心配だと言っている", "同じくらい早く終わったと言っている", "時間がかかりすぎると批判している"],
    "expl": "Howdya は 'How did you' の速読み縮約形。fast speechでの聞き取りに注意。",
    "kp": ["Howdya", "manage to", "takes me all day"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Whereda you end up putting those files? I've searched everywhere.",
    "ja": "最終的にそのファイルどこに置いたの？どこを探しても見つからない。",
    "answer": "探しているファイルの場所を尋ねている",
    "choices": ["探しているファイルの場所を尋ねている", "ファイルを捨てるよう頼んでいる", "ファイルを全部確認したと報告している", "ファイルがなくなったと知らせている", "ファイルを別の場所に移したと言っている"],
    "expl": "Whereda は 'Where did you' の速読み縮約形。'end up' は「結局〜した」という表現。",
    "kp": ["Whereda", "end up", "searched everywhere"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Whatcha been up to lately? Feels like forever since we caught up.",
    "ja": "最近どうしてる？久しぶりだね。",
    "answer": "近況を聞きながら再会の喜びを示している",
    "choices": ["近況を聞きながら再会の喜びを示している", "最近サボっていたと批判している", "何か報告があると言っている", "相手が連絡してこなかったことへの不満", "仕事の進捗を確認している"],
    "expl": "Whatcha は 'What have you' の速読み縮約形。'been up to' は「何をしていた・最近どう過ごしていた」という表現。",
    "kp": ["Whatcha", "been up to", "caught up"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Toldja it'd work out. You were worried for nothing.",
    "ja": "うまくいくって言ったでしょ。心配してもしょうがなかったね。",
    "answer": "予言通りうまくいったことを確認している",
    "choices": ["予言通りうまくいったことを確認している", "うまくいかなかったことを指摘している", "心配するよう促している", "相手の判断が正しかったと認めている", "次もうまくいくと保証している"],
    "expl": "Toldja は 'Told you' の速読み縮約形。'work out' は「うまくいく・解決する」という表現。",
    "kp": ["Toldja", "work out", "worried for nothing"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Howdja even find out about it? I thought it wasn't public yet.",
    "ja": "どうやって知ったの？まだ公表されていないと思っていたんだけど。",
    "answer": "まだ公表前のことをどう知ったか驚いて聞いている",
    "choices": ["まだ公表前のことをどう知ったか驚いて聞いている", "公表の担当者を確認している", "情報が正確かどうか確認している", "公表する許可をもらったか確認している", "情報を教えてくれたことに感謝している"],
    "expl": "Howdja は 'How did you' の速読み縮約形。'find out' は「知る・情報を得る」。",
    "kp": ["Howdja", "find out", "public yet"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Yagotta be kidding me. Not again.",
    "ja": "冗談でしょ。また？",
    "answer": "繰り返し起きることへの強い驚きと呆れ",
    "choices": ["繰り返し起きることへの強い驚きと呆れ", "冗談を言うよう頼んでいる", "また冗談を言い合おうと提案している", "今度は本当のことを言ってほしいと頼んでいる", "笑えないジョークだと批判している"],
    "expl": "Ya は 'You' の口語形。gotta は 'have got to' の縮約形。'You gotta be kidding me' は強い驚きや呆れを表す慣用句。",
    "kp": ["Yagotta", "kidding me", "not again"]
  },
  # ── SPEED lv3 (4問) ──────────────────────────────────────────────────────
  {
    "diff": "lv3", "axis": "speed",
    "text": "I'm tellincha, if this keeps up, we're gonna have a real problem on our hands.",
    "ja": "言っておくけど、これが続けば、本当に大変なことになるよ。",
    "answer": "状況が続けば深刻な問題になると警告している",
    "choices": ["状況が続けば深刻な問題になると警告している", "今すでに深刻な問題があると報告している", "問題はもうすぐ解決すると安心させている", "自分には関係がないことを伝えている", "問題について話し合うよう提案している"],
    "expl": "I'm tellincha は 'I'm telling you' の速読み縮約形。強調・警告の表現として使われる。",
    "kp": ["tellincha", "keeps up", "on our hands"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "There's noway she found out on her own. Someone must have tipped her off.",
    "ja": "彼女が独力で知ったはずがない。誰かがこっそり教えたに違いない。",
    "answer": "情報が外部から漏れたと確信している",
    "choices": ["情報が外部から漏れたと確信している", "彼女が独力で解決したことに感心している", "誰かを責めるよう促している", "情報の発信者を特定したと言っている", "彼女が知らないと確認している"],
    "expl": "noway は 'no way' の速読み連結。'tip someone off' は「こっそり情報を教える・密告する」という表現。",
    "kp": ["noway", "on her own", "tip her off"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Wouldjabelieve they turned down the whole offer? Just walked away.",
    "ja": "信じられる？彼らはオファーを全て断ったんだよ。そのまま立ち去った。",
    "answer": "予想外にオファーが断られたことへの驚き",
    "choices": ["予想外にオファーが断られたことへの驚き", "オファーを受け入れたことへの安堵", "断ったのは正しい判断だと言っている", "彼らがどこへ行ったか知っているか尋ねている", "オファーの内容を詳しく説明しようとしている"],
    "expl": "Wouldjabelieve は 'Would you believe' の速読み縮約形。驚きを表す冒頭表現として使われる。",
    "kp": ["Wouldjabelieve", "turned down", "walked away"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "By the time she finally got around to it, the deadline had already passed.",
    "ja": "彼女がやっと取り掛かったときには、もう締め切りが過ぎていた。",
    "answer": "対応が遅れて締め切りを逃したことを述べている",
    "choices": ["対応が遅れて締め切りを逃したことを述べている", "締め切りの延長を求めたと言っている", "締め切り前に完了したと言っている", "締め切りを彼女が設定したと言っている", "締め切りは関係ないと言っている"],
    "expl": "fast speechでは 'got around to' が繋がって速く発音される。'get around to' は「やっと〜に取り掛かる」という表現。",
    "kp": ["got around to", "deadline had passed"]
  },
  # ── SPEED lv4 (3問) ──────────────────────────────────────────────────────
  {
    "diff": "lv4", "axis": "speed",
    "text": "I barely caught what she said—something about the merger being put on hold?",
    "ja": "彼女が言ったことをほとんど聞き取れなかった——合併が保留になるとか何とか？",
    "answer": "聞き取れた内容について確認している",
    "choices": ["聞き取れた内容について確認している", "合併が正式に中止になったと伝えている", "彼女の話が意味不明だったと批判している", "もう一度言うよう彼女に頼んでいる", "合併について直接確認する必要はないと言っている"],
    "expl": "fast speechでは 'barely caught' 'put on hold' の部分が特に速く発音される。'put on hold' は「保留にする」というビジネス表現。",
    "kp": ["barely caught", "put on hold"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "He goes through the agenda so fast you'd think he gets paid by the slide.",
    "ja": "彼はアジェンダをあまりに速く進めるから、スライド一枚ごとに給料でも出るのかと思うほど。",
    "answer": "進行が速すぎることをユーモアを交えて批判している",
    "choices": ["進行が速すぎることをユーモアを交えて批判している", "彼の給料が高いことへの嫉妬", "スライドをもっと増やすよう提案している", "アジェンダ通りに進んでいると評価している", "彼のプレゼンが短くて助かると言っている"],
    "expl": "fast speechで 'you'd think he gets paid by the slide' がリズムよく言われる。'get paid by the' は報酬体系のユーモア表現。",
    "kp": ["gets paid by", "goes through so fast"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "She breezed through the entire review in eight minutes—no notes, no stumbles.",
    "ja": "彼女はメモも詰まりもなく、レビュー全体を8分でさらっとやり終えた。",
    "answer": "素晴らしいスピードと流暢さでレビューをこなしたことへの感嘆",
    "choices": ["素晴らしいスピードと流暢さでレビューをこなしたことへの感嘆", "8分で終わらなかったことへの批判", "レビューの内容が薄かったことを心配している", "彼女が急ぎすぎて内容を飛ばしたと言っている", "8分という時間制限があったと説明している"],
    "expl": "fast speechで 'breezed through' 'no notes no stumbles' が流れるように発音される。'breeze through' は「軽々とやり終える」。",
    "kp": ["breezed through", "no stumbles"]
  },
  # ── SPEED lv5 (1問) ──────────────────────────────────────────────────────
  {
    "diff": "lv5", "axis": "speed",
    "text": "She just kept going and going and by the time she wrapped up I'd completely lost track of the main point—she packs in so much it's hard to follow.",
    "ja": "彼女はずっと話し続けて、終わったときには要点を完全に見失ってしまった——盛り込みすぎて追いかけにくい。",
    "answer": "情報量が多すぎて要点を掴めなかったと言っている",
    "choices": ["情報量が多すぎて要点を掴めなかったと言っている", "彼女の話がとても分かりやすかったと言っている", "早口で聞き取れなかったと言っている", "要点のまとめを相手に頼んでいる", "彼女がもっとゆっくり話すべきだと提案している"],
    "expl": "'kept going and going' 'completely lost track' 'packs in so much' など複数の口語表現が連続。速い発話での情報処理能力が試される。",
    "kp": ["kept going and going", "lost track", "packs in so much"]
  },
  # ── VOCAB lv1 (5問) ──────────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "vocab",
    "text": "I'd better call it a night. Big day tomorrow.",
    "ja": "もう寝よう。明日は大事な日だから。",
    "answer": "今夜はここまでにして寝ると言っている",
    "choices": ["今夜はここまでにして寝ると言っている", "夜のイベントをキャンセルしている", "夜中まで働き続けると言っている", "明日は休日だと言っている", "翌朝早起きする必要はないと言っている"],
    "expl": "'call it a night' は「今夜はここまでにする・寝る」という慣用表現。'call it a day' と混同しないこと。",
    "kp": ["call it a night", "big day"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "She's been on cloud nine since she heard about the promotion.",
    "ja": "昇進の話を聞いてから、彼女はずっと有頂天だ。",
    "answer": "昇進の知らせに大喜びしている",
    "choices": ["昇進の知らせに大喜びしている", "昇進のせいでストレスを感じている", "昇進を断ろうと考えている", "昇進がいつになるか待ちわびている", "昇進の条件を確認している"],
    "expl": "'on cloud nine' は「有頂天・非常に幸せな状態」を表す慣用表現。",
    "kp": ["on cloud nine", "promotion"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "He's been under the weather since the weekend. Might be a cold.",
    "ja": "週末から体調が悪い。風邪かもしれない。",
    "answer": "週末から体調不良が続いている",
    "choices": ["週末から体調不良が続いている", "週末に悪天候で困ったと言っている", "週末から気分が落ち込んでいると言っている", "体調は回復したと言っている", "天気のせいで気分が悪いと言っている"],
    "expl": "'under the weather' は「体調が悪い・具合が悪い」という慣用表現。天気と関係なく体調の話に使う。",
    "kp": ["under the weather", "might be a cold"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "I'll give it a shot. If it doesn't work, we'll try something else.",
    "ja": "やってみる。うまくいかなければ、別の方法を試せばいい。",
    "answer": "試してみると前向きに言っている",
    "choices": ["試してみると前向きに言っている", "すでに試したが失敗したと言っている", "射撃の練習をすると言っている", "誰かに実行を依頼している", "別の方法の方が良いと主張している"],
    "expl": "'give it a shot' は「試してみる・挑戦する」という口語表現。",
    "kp": ["give it a shot", "something else"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "The whole deal fell through at the very last minute.",
    "ja": "取引は土壇場で全てダメになってしまった。",
    "answer": "直前で取引が破談になった",
    "choices": ["直前で取引が破談になった", "取引が最後の段階で成立した", "取引の一部を変更した", "取引の担当者が変わった", "土壇場で条件が改善した"],
    "expl": "'fall through' は「（計画・取引などが）破談になる・失敗する」。'at the very last minute' で「土壇場で」という強調。",
    "kp": ["fell through", "last minute"]
  },
  # ── VOCAB lv2 (6問) ──────────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "vocab",
    "text": "After the first approach didn't work, they went back to the drawing board.",
    "ja": "最初のアプローチがうまくいかなかったので、白紙に戻した。",
    "answer": "失敗後に最初からやり直すことにした",
    "choices": ["失敗後に最初からやり直すことにした", "ホワイトボードに戻って議論を続けた", "別の部署に協力を求めた", "問題なく計画が進んでいる", "失敗を認めずに同じ方法を繰り返した"],
    "expl": "'go back to the drawing board' は「一から考え直す・白紙に戻す」という表現。設計図（drawing board）に戻るイメージ。",
    "kp": ["drawing board", "didn't work"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "He always goes the extra mile for his clients. That's what sets him apart.",
    "ja": "彼はいつもクライアントのために一歩余分に進む。それが彼を際立たせている。",
    "answer": "期待以上の努力をすることで差別化している",
    "choices": ["期待以上の努力をすることで差別化している", "長距離を毎日歩いていると言っている", "クライアントに無理な要求をしていると批判している", "クライアントの元に実際に出向くと言っている", "距離的に近いクライアントだけを担当すると言っている"],
    "expl": "'go the extra mile' は「期待以上の努力をする・一歩踏み込む」という慣用表現。'sets him apart' は「他と差をつける・際立たせる」。",
    "kp": ["goes the extra mile", "sets him apart"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "We need to get the ball rolling before the end of the month.",
    "ja": "月末前に動き始めなければならない。",
    "answer": "月末前にプロジェクトを開始する必要がある",
    "choices": ["月末前にプロジェクトを開始する必要がある", "月末にはスポーツ大会がある", "ボールを使ったトレーニングを始める必要がある", "月末前に問題を解決する必要がある", "月末には計画を完成させる必要がある"],
    "expl": "'get the ball rolling' は「物事を開始する・スタートさせる」という慣用表現。",
    "kp": ["get the ball rolling", "end of the month"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "She's a tough cookie—she got back on her feet pretty fast after that setback.",
    "ja": "彼女はなかなかの強者だ——あの挫折からかなり早く立ち直った。",
    "answer": "困難から素早く回復できる精神的に強い人物",
    "choices": ["困難から素早く回復できる精神的に強い人物", "彼女が甘いものが好きだと言っている", "彼女が料理が得意だと言っている", "挫折からまだ立ち直れていないと言っている", "挫折から立ち直るのに時間がかかったと言っている"],
    "expl": "'tough cookie' は「タフな人物・精神的に強い人」という慣用表現。'get back on one's feet' は「立ち直る・復活する」。",
    "kp": ["tough cookie", "get back on her feet", "setback"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "Don't rock the boat right now. Things are finally starting to settle down.",
    "ja": "今は波風を立てないでくれ。ようやく落ち着いてきたところなんだから。",
    "answer": "状況が安定しているのを乱さないよう求めている",
    "choices": ["状況が安定しているのを乱さないよう求めている", "ボートの修理をするよう頼んでいる", "早く結論を出すよう急かしている", "変化を積極的に進めるよう励ましている", "揺れる船に乗るのをやめるよう言っている"],
    "expl": "'rock the boat' は「波風を立てる・現状を乱す」という慣用表現。「ボートを揺らす＝不安定にする」から。",
    "kp": ["rock the boat", "settle down"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "They went all in on one strategy, and when it failed, they had nothing left.",
    "ja": "一つの戦略に全てをつぎ込んで、失敗したら何も残らなかった。",
    "answer": "一点集中の戦略が失敗してリカバリー不能になった",
    "choices": ["一点集中の戦略が失敗してリカバリー不能になった", "多角的な戦略で成功したと言っている", "戦略を変更したことで状況が改善したと言っている", "失敗しても別の手があると言っている", "リスクを分散させるべきだと学んだと言っている"],
    "expl": "'go all in' は「全てをかける・一点集中する」。ポーカーの 'all in' から来た表現。",
    "kp": ["went all in", "nothing left"]
  },
  # ── VOCAB lv3 (5問) ──────────────────────────────────────────────────────
  {
    "diff": "lv3", "axis": "vocab",
    "text": "He played his cards right and ended up with the best deal on the table.",
    "ja": "彼はうまく立ち回って、最終的に最も有利な条件を手にした。",
    "answer": "賢く行動して最良の結果を得た",
    "choices": ["賢く行動して最良の結果を得た", "トランプゲームで勝ったと言っている", "テーブルの上に置かれたカードを取ったと言っている", "有利な条件を無視したと言っている", "最良の条件を提示したが断られたと言っている"],
    "expl": "'play one's cards right' は「上手く立ち回る・うまくやる」という表現。カードゲームで手札を上手く使うイメージ。",
    "kp": ["played his cards right", "best deal on the table"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "It's a long shot, but it might be the only realistic option we have.",
    "ja": "可能性は低いけど、現実的に考えるとそれしか選択肢がないかもしれない。",
    "answer": "成功率は低いが他に選択肢がない",
    "choices": ["成功率は低いが他に選択肢がない", "遠い場所に行く必要があると言っている", "最もリスクの低い選択肢を選んでいる", "成功は間違いないと確信している", "別の良い選択肢があると言っている"],
    "expl": "'long shot' は「可能性が低いこと・大穴」という表現。遠くから撃つ「ロングショット」は当たりにくいことから。",
    "kp": ["long shot", "realistic option"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "She tends to sugarcoat things, so it's hard to know if there's actually a problem.",
    "ja": "彼女は物事を甘く言いがちなので、実際に問題があるのか判断しにくい。",
    "answer": "本当の問題の深刻さが分かりにくいと述べている",
    "choices": ["本当の問題の深刻さが分かりにくいと述べている", "彼女が砂糖を使った料理が好きだと言っている", "彼女が問題を過大に伝える傾向があると言っている", "彼女の判断は常に正確だと言っている", "彼女は問題について率直に話すと言っている"],
    "expl": "'sugarcoat' は「（悪い情報を）和らげて伝える・甘くする」という表現。砂糖でコーティングして苦さを隠すイメージ。",
    "kp": ["sugarcoat", "hard to know if"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "We can't keep sweeping this issue under the rug. It needs to be addressed.",
    "ja": "この問題をずっと隠し続けるわけにはいかない。対処しなければならない。",
    "answer": "問題を隠し続けることをやめて向き合うべきだと言っている",
    "choices": ["問題を隠し続けることをやめて向き合うべきだと言っている", "問題をどこかに移動させるよう言っている", "問題が表面化したと報告している", "問題は既に解決されたと言っている", "問題をもう少し様子見するよう提案している"],
    "expl": "'sweep under the rug' は「問題を隠す・なかったことにする」という慣用表現。ゴミを絨毯の下に掃き込むイメージ。",
    "kp": ["sweeping under the rug", "addressed"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "Whether the deal goes through is still up in the air. Nothing's been confirmed.",
    "ja": "取引がまとまるかどうかはまだ未定だ。何も確定していない。",
    "answer": "取引の行方がまだ決まっていない",
    "choices": ["取引の行方がまだ決まっていない", "取引は既に成立したと言っている", "取引は成功しないと予測している", "取引について空中で議論していると言っている", "取引の確定を後日決めると言っている"],
    "expl": "'up in the air' は「未決定・宙ぶらりん」という慣用表現。何も地に足がついていない状態のイメージ。",
    "kp": ["up in the air", "confirmed"]
  },
  # ── VOCAB lv4 (3問) ──────────────────────────────────────────────────────
  {
    "diff": "lv4", "axis": "vocab",
    "text": "He's been sitting on that decision for three weeks. Everything's on hold because of it.",
    "ja": "彼はその決断を3週間も先延ばしにしている。それのせいで全てが止まっている。",
    "answer": "決断の先送りが全体の進行を停滞させている",
    "choices": ["決断の先送りが全体の進行を停滞させている", "3週間で決断が下されたと言っている", "彼が3週間休暇中だと言っている", "決断は彼の仕事ではないと言っている", "3週間後に決断すると約束している"],
    "expl": "'sit on' は「（決定・情報などを）先延ばしにする・保留にする」という表現。'on hold' は「保留・停止中」。",
    "kp": ["sitting on", "on hold", "because of it"]
  },
  {
    "diff": "lv4", "axis": "vocab",
    "text": "That concept has real legs. Let's develop it further before we take it to the client.",
    "ja": "そのコンセプトには本物の可能性がある。クライアントに持っていく前にもっと肉付けしよう。",
    "answer": "アイデアに実現可能性があるので発展させようと提案している",
    "choices": ["アイデアに実現可能性があるので発展させようと提案している", "コンセプトが脚に関係していると言っている", "クライアントに今すぐ提案するよう言っている", "アイデアは使い物にならないと批判している", "クライアントがアイデアを断ったと言っている"],
    "expl": "'has legs' は「（アイデアや計画が）長続きする可能性がある・実現可能性がある」という表現。",
    "kp": ["has legs", "develop further"]
  },
  {
    "diff": "lv4", "axis": "vocab",
    "text": "She'll bend over backwards to make sure the client is satisfied. That's her thing.",
    "ja": "彼女はクライアントが満足するよう全力を尽くす。それが彼女のスタイルだ。",
    "answer": "クライアント満足のために全力を尽くす人物",
    "choices": ["クライアント満足のために全力を尽くす人物", "柔軟な体を持つ人だと言っている", "クライアントに対して腰を低くしすぎると批判している", "クライアントの要求が無理難題だと言っている", "クライアントとの関係を断ちたいと言っている"],
    "expl": "'bend over backwards' は「全力を尽くす・最大限の努力をする」という表現。無理な体勢をとるほど努力するイメージ。",
    "kp": ["bend over backwards", "satisfied", "that's her thing"]
  },
  # ── VOCAB lv5 (1問) ──────────────────────────────────────────────────────
  {
    "diff": "lv5", "axis": "vocab",
    "text": "The client seemed mollified for now, but reading between the lines, I think we're still on precarious ground.",
    "ja": "クライアントは今のところ落ち着いたように見えるが、行間を読むと、まだ不安定な状況だと思う。",
    "answer": "表面上は解決したように見えるが根本的な不安が残っている",
    "choices": ["表面上は解決したように見えるが根本的な不安が残っている", "クライアントが全て解決したと言っている", "クライアントが怒っていることを報告している", "地盤が不安定な場所での作業について話している", "行間にある内容を読むよう依頼している"],
    "expl": "'mollified' は「宥められた・落ち着いた」という語。'reading between the lines' は「行間を読む・言外の意味を汲む」。'precarious' は「不安定な・危うい」。",
    "kp": ["mollified", "reading between the lines", "precarious ground"]
  },
  # ── DISTRACTOR lv1 (7問) ─────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "distractor",
    "text": "Can you please turn it down? I'm on a call.",
    "ja": "音量を下げてもらえる？電話中なんだ。",
    "answer": "音量を下げてほしいと頼んでいる",
    "choices": ["音量を下げてほしいと頼んでいる", "電話を切るよう言っている", "音量を上げてほしいと頼んでいる", "別の部屋に行くよう言っている", "電話に出るよう頼んでいる"],
    "expl": "'turn it down' は「音量を下げる」。電話中という文脈から、声や音楽の音量を下げるよう頼んでいることが分かる。distractor: 'turn it up（上げる）' や 'hang up（切る）'。",
    "kp": ["turn it down", "on a call"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "She said she'd come by sometime this afternoon.",
    "ja": "彼女は今日の午後に立ち寄ると言っていた。",
    "answer": "今日の午後に訪ねてくると言っている",
    "choices": ["今日の午後に訪ねてくると言っている", "今日の午後まで待つよう言っている", "今日の午後は来られないと言っている", "今日の午後に出発すると言っている", "来るかどうかはまだ分からないと言っている"],
    "expl": "'come by' は「立ち寄る・ちょっと来る」という意味。'sometime' は「いつか・そのうち」。distractor: 来ない・出発するの選択肢と混同しやすい。",
    "kp": ["come by", "sometime this afternoon"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "I'll take the same thing as last time, please.",
    "ja": "前回と同じものをお願いします。",
    "answer": "前回と同じ注文をしている",
    "choices": ["前回と同じ注文をしている", "何か違うものを試したいと言っている", "前回の注文に間違いがあったと言っている", "注文をやめると言っている", "前回より多い量を頼んでいる"],
    "expl": "'the same thing as last time' は「前回と同じもの」。飲食店や注文の場面でよく使われる。",
    "kp": ["same thing as last time"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "Could you scoot over just a little? I need a bit more room.",
    "ja": "少しずれてもらえる？もう少し場所が必要なんだ。",
    "answer": "少し横にずれてほしいと頼んでいる",
    "choices": ["少し横にずれてほしいと頼んでいる", "立ち上がるよう頼んでいる", "荷物を置く場所を作るよう頼んでいる", "もっと大きな部屋に移るよう言っている", "部屋から出るよう頼んでいる"],
    "expl": "'scoot over' は「少し横にずれる・動く」という口語表現。座席などで使われる。",
    "kp": ["scoot over", "a bit more room"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "You go on ahead. I'll catch up with you in a few minutes.",
    "ja": "先に行って。数分後に追いつくから。",
    "answer": "先に行ってもらい後から追いつくと伝えている",
    "choices": ["先に行ってもらい後から追いつくと伝えている", "自分が先に行くから待つよう言っている", "数分後に戻ってくると言っている", "今すぐ行く必要はないと言っている", "一緒に行くのをやめると言っている"],
    "expl": "'go on ahead' は「先に行く」。'catch up with' は「追いつく・追いかけて合流する」という表現。",
    "kp": ["go on ahead", "catch up with"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "I'm doing a quick grocery run. Can I pick anything up for you?",
    "ja": "ちょっとスーパーに行ってくるんだけど、何か買ってくる？",
    "answer": "買い物に行くついでに何か頼みがあるか聞いている",
    "choices": ["買い物に行くついでに何か頼みがあるか聞いている", "食料が切れたと報告している", "誰かに買い物を頼もうとしている", "急いで走って戻ると言っている", "何も買わないと伝えている"],
    "expl": "'grocery run' は「食料品の買い物に行く」という口語表現。'pick anything up for you' は「何か買ってきてあげる」という申し出。",
    "kp": ["grocery run", "pick anything up"]
  },
  {
    "diff": "lv1", "axis": "distractor",
    "text": "He said he'd take care of it, so I figured I'd leave it to him.",
    "ja": "彼が対処すると言ったので、彼に任せることにした。",
    "answer": "相手に任せることにした",
    "choices": ["相手に任せることにした", "相手がうまく対処できるか心配している", "自分が代わりにやると申し出た", "彼が対処しなかったことに怒っている", "二人で一緒にやることにした"],
    "expl": "'take care of it' は「対処する・処理する」。'leave it to' は「〜に任せる」という表現。",
    "kp": ["take care of it", "leave it to him"]
  },
  # ── DISTRACTOR lv2 (6問) ─────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "distractor",
    "text": "She said she'd look into it and get back to us by end of week.",
    "ja": "彼女は調べて今週中に折り返すと言っていた。",
    "answer": "調査して今週中に連絡してくれると言っている",
    "choices": ["調査して今週中に連絡してくれると言っている", "今週中に問題を解決すると言っている", "週末に会う約束をしたと言っている", "すぐに答えを出せると言っている", "彼女に折り返しの電話を要求していると言っている"],
    "expl": "'look into' は「調査する・確認する」。'get back to' は「〜に折り返す・後で連絡する」というビジネス表現。",
    "kp": ["look into", "get back to", "end of week"]
  },
  {
    "diff": "lv2", "axis": "distractor",
    "text": "It's a bit rich coming from him—he's the one who's always late.",
    "ja": "彼に言われてもねえ——いつも遅刻しているのは彼の方じゃない。",
    "answer": "当事者がそれを言うのは説得力がないと皮肉を言っている",
    "choices": ["当事者がそれを言うのは説得力がないと皮肉を言っている", "彼はいつも豊かな経験談を話すと言っている", "遅刻のせいで彼が怒ったと言っている", "彼の収入が多いと言っている", "彼が時間通りに来たことを褒めている"],
    "expl": "'a bit rich' は「よく言えるね・どの口が言うの」という皮肉表現。'coming from him' で「彼がそれを言うとは」という含みがある。",
    "kp": ["a bit rich", "coming from him"]
  },
  {
    "diff": "lv2", "axis": "distractor",
    "text": "Any chance you could cover for me on Friday? I have a thing.",
    "ja": "金曜日、代わりに対応してもらえる？ちょっと用事があって。",
    "answer": "金曜日に自分の代わりを頼んでいる",
    "choices": ["金曜日に自分の代わりを頼んでいる", "金曜日に一緒に出かけようと誘っている", "金曜日は休みにするよう言っている", "金曜日のカバーを外すよう頼んでいる", "金曜日は自分が対応すると申し出ている"],
    "expl": "'cover for me' は「私の代わりにやってもらう・私の不在中に対応してもらう」。'I have a thing' は「用事がある」という曖昧な口語表現。",
    "kp": ["cover for me", "I have a thing"]
  },
  {
    "diff": "lv2", "axis": "distractor",
    "text": "He seemed a bit put out when the idea got shot down. I think it hit a nerve.",
    "ja": "アイデアが却下されたとき、彼は少し不満そうだった。何か触れてはいけないことに触れたのかもしれない。",
    "answer": "アイデアの却下が彼の感情的な部分に触れたようだ",
    "choices": ["アイデアの却下が彼の感情的な部分に触れたようだ", "彼がプレゼン中に倒れたと言っている", "彼のアイデアが採用されたと言っている", "銃で何かを撃ち落としたと言っている", "彼は不満を全く感じていなかったと言っている"],
    "expl": "'put out' は「不機嫌な・不満な」という意味。'hit a nerve' は「神経に触る・痛いところをつく」。'shot down' は「却下する」。",
    "kp": ["put out", "hit a nerve", "shot down"]
  },
  {
    "diff": "lv2", "axis": "distractor",
    "text": "We're stretched a bit thin right now, but we should be fine once the new hire starts.",
    "ja": "今は少し人手不足だけど、新しい人が入ったら大丈夫なはずだ。",
    "answer": "現在は人手不足だが新入社員が来れば改善する",
    "choices": ["現在は人手不足だが新入社員が来れば改善する", "今は十分な人員がいると言っている", "採用活動を中止すると言っている", "薄い素材を使っているため問題があると言っている", "新入社員が多すぎると言っている"],
    "expl": "'stretched thin' は「人員・リソースが薄く広がっている＝人手不足・余裕がない」状態。'new hire' は「新入社員」。",
    "kp": ["stretched thin", "new hire"]
  },
  {
    "diff": "lv2", "axis": "distractor",
    "text": "She's always been straight with me, so I take her word for it.",
    "ja": "彼女はいつも私に正直だから、彼女の言葉を信じることにする。",
    "answer": "相手の誠実さを信頼してその言葉を信じる",
    "choices": ["相手の誠実さを信頼してその言葉を信じる", "彼女が直線上にいるから見える", "彼女に近づくよう言っている", "彼女の言葉が正確かどうか確認している", "信じてはいけないと警告している"],
    "expl": "'straight' には「正直な・率直な」という意味がある。'take someone's word for it' は「〜の言葉を信じる・〜を信頼する」という表現。",
    "kp": ["been straight", "take her word for it"]
  },
  # ── DISTRACTOR lv3 (5問) ─────────────────────────────────────────────────
  {
    "diff": "lv3", "axis": "distractor",
    "text": "I nearly walked right past him—he's lost so much weight since I last saw him.",
    "ja": "危うく見過ごすところだった——前回会ったときよりかなり痩せていた。",
    "answer": "体型の変化で見分けがつきにくくなっていたと述べている",
    "choices": ["体型の変化で見分けがつきにくくなっていたと述べている", "彼がすれ違いざまに歩き去ったと言っている", "彼が急いで通り過ぎたと言っている", "体重が増えて気づかなかったと言っている", "彼に会いに行くのをやめたと言っている"],
    "expl": "'nearly walked right past' は「危うく見過ごすところだった」。'lost weight' は「体重が減った・痩せた」。文脈から外見の変化が原因だと分かる。",
    "kp": ["walked right past", "lost weight"]
  },
  {
    "diff": "lv3", "axis": "distractor",
    "text": "She wrapped it up in exactly ten minutes, just like she said she would.",
    "ja": "彼女は言った通り、ちょうど10分でまとめた。",
    "answer": "約束した時間通りに終わらせた",
    "choices": ["約束した時間通りに終わらせた", "10分後にプレゼンを始めると言っている", "10分を大幅に超えてしまったと言っている", "プレゼンが10分では短すぎたと言っている", "彼女の言い通りにならなかったと言っている"],
    "expl": "'wrap it up' は「まとめる・終わらせる」。'just like she said' は「彼女が言った通り」で、予告との一致を強調。",
    "kp": ["wrapped it up", "just like she said"]
  },
  {
    "diff": "lv3", "axis": "distractor",
    "text": "He was so close to pulling it off. It's a shame it didn't come together in the end.",
    "ja": "あと少しでやり遂げるところだった。最終的にうまくいかなくて残念だ。",
    "answer": "もう少しで成功できたのに惜しかったと述べている",
    "choices": ["もう少しで成功できたのに惜しかったと述べている", "最終的に成功したことへの安堵", "最初からうまくいかないと分かっていたと言っている", "彼が途中で諦めたことを批判している", "努力が足りなかったと言っている"],
    "expl": "'pull it off' は「成し遂げる・やり遂げる」。'come together' は「まとまる・うまくいく」。文脈から失敗したことが分かる。",
    "kp": ["pulling it off", "come together in the end"]
  },
  {
    "diff": "lv3", "axis": "distractor",
    "text": "We were supposed to have until next Friday, but they moved it up to Wednesday.",
    "ja": "来週金曜まであるはずだったのに、水曜日に前倒しになった。",
    "answer": "締め切りが前倒しになったと言っている",
    "choices": ["締め切りが前倒しになったと言っている", "来週金曜まで延期になったと言っている", "水曜日から金曜日に変更になったと言っている", "締め切りはまだ決まっていないと言っている", "自分たちが締め切りを変更したと言っている"],
    "expl": "'move up' は「（日程を）前倒しにする・早める」。'supposed to have until' は「〜まであるはずだった」という期待との差。",
    "kp": ["moved it up", "supposed to have until"]
  },
  {
    "diff": "lv3", "axis": "distractor",
    "text": "I thought it was still mine to handle, but apparently it had already been sorted out.",
    "ja": "まだ自分が対処するものだと思っていたが、どうやら既に解決していたらしい。",
    "answer": "自分の仕事だと思っていたが既に別の誰かが対処済みだった",
    "choices": ["自分の仕事だと思っていたが既に別の誰かが対処済みだった", "自分が対処して問題を解決したと言っている", "問題がまだ解決していないと言っている", "誰かに勝手に対処されて怒っていると言っている", "これから対処すると言っている"],
    "expl": "'mine to handle' は「自分が担当すること」。'sorted out' は「解決された・片付けられた」という表現。",
    "kp": ["mine to handle", "sorted out", "apparently"]
  },
  # ── DISTRACTOR lv4 (3問) ─────────────────────────────────────────────────
  {
    "diff": "lv4", "axis": "distractor",
    "text": "It's not that I have an issue with the direction—I'm just not sure the timeline is realistic.",
    "ja": "方向性に問題があるということではない——ただタイムラインが現実的かどうか分からない。",
    "answer": "計画自体ではなくタイムラインに懸念がある",
    "choices": ["計画自体ではなくタイムラインに懸念がある", "計画全体に反対していると言っている", "タイムラインは問題ないと言っている", "方向性もタイムラインも問題ないと言っている", "タイムラインを自分で決めたいと言っている"],
    "expl": "'it's not that' は「〜というわけではない」という否定・限定の表現。似た言葉で異なる意味を区別する力が問われる。",
    "kp": ["it's not that", "direction", "timeline", "realistic"]
  },
  {
    "diff": "lv4", "axis": "distractor",
    "text": "She didn't say she wouldn't do it—she said she couldn't have it done by Thursday.",
    "ja": "やらないとは言っていない——木曜日までには終わらせられないと言ったのだ。",
    "answer": "拒否ではなく期日内の完了が難しいと言っている",
    "choices": ["拒否ではなく期日内の完了が難しいと言っている", "木曜日までにやると約束していると言っている", "仕事を断ったと言っている", "期日は問題ないと言っている", "木曜日以降に完了すると言っている"],
    "expl": "'wouldn't' と 'couldn't' の意味の違いが焦点。won't = 意志的な拒否、can't = 能力的・状況的な不可能。",
    "kp": ["wouldn't", "couldn't", "have it done by"]
  },
  {
    "diff": "lv4", "axis": "distractor",
    "text": "He approved it, which is great, but I'd be surprised if he actually went through the whole thing.",
    "ja": "彼が承認してくれたのはいいことだが、本当に全部読んだとは思えない。",
    "answer": "形式的に承認したが内容を精読したか疑わしいと述べている",
    "choices": ["形式的に承認したが内容を精読したか疑わしいと述べている", "彼が全部読んで承認したことを評価している", "彼が承認を拒否したと言っている", "全部読んだうえで修正を求めたと言っている", "承認が必要なかったと言っている"],
    "expl": "'went through the whole thing' は「全体を精読した・通読した」という意味。'I'd be surprised if' で懐疑的な見方を表す。",
    "kp": ["approved it", "went through the whole thing", "I'd be surprised if"]
  },
  # ── DISTRACTOR lv5 (1問) ─────────────────────────────────────────────────
  {
    "diff": "lv5", "axis": "distractor",
    "text": "She seemed genuinely on board with the changes, but she's known for going along with things in the moment and raising concerns later.",
    "ja": "彼女は変更に本当に賛成しているように見えた。でも彼女はその場では同意しておいて後で懸念を持ち出すことで知られている。",
    "answer": "表面上の同意が後で覆る可能性があると懸念している",
    "choices": ["表面上の同意が後で覆る可能性があると懸念している", "彼女が変更に完全に反対していると言っている", "彼女が変更を提案したと言っている", "彼女は常に最初から懸念を明確にすると言っている", "彼女が最終的に同意したことへの安堵"],
    "expl": "'on board' は「賛成している・同意している」。'going along with' は「（とりあえず）同意する・従う」。後から 'concerns' を出す人物像との対比が複雑。",
    "kp": ["on board", "going along with", "raising concerns later"]
  },
  # ── CONTEXT lv1 (2問) ────────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "context",
    "text": "Oh, you're still here? I thought you'd have left by now.",
    "ja": "あれ、まだいたの？もう帰っていると思っていた。",
    "answer": "まだいることへの驚きを示している",
    "choices": ["まだいることへの驚きを示している", "帰るよう促している", "来てくれたことへの喜びを表している", "いつ帰るか尋ねている", "遅くまでいたことを叱っている"],
    "expl": "語句の意味ではなく、トーンと状況から「驚き」が読み取れる。'I thought you'd have left' は「もう帰ったと思っていた」で驚きを表す。",
    "kp": ["you're still here", "thought you'd have left"]
  },
  {
    "diff": "lv1", "axis": "context",
    "text": "Well, let's just say things didn't exactly go to plan.",
    "ja": "まあ、計画通りとは言えない展開になったとだけ言っておこう。",
    "answer": "計画通りにいかなかったことを婉曲に伝えている",
    "choices": ["計画通りにいかなかったことを婉曲に伝えている", "計画が完璧に実行されたと言っている", "別の計画を立てたほうが良かったと後悔している", "計画の詳細を説明しようとしている", "計画を立てなかったことへの批判"],
    "expl": "'let's just say' は「一言で言えば・簡単に言うと」という婉曲表現。'didn't exactly go to plan' は「計画通りではなかった」という控えめな表現。",
    "kp": ["let's just say", "didn't go to plan"]
  },
  # ── CONTEXT lv2 (1問) ────────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "context",
    "text": "Yeah, sure. I'll believe that when I see it.",
    "ja": "ええ、そうですね。実際に見てから信じますよ。",
    "answer": "懐疑的で信じていないことを示している",
    "choices": ["懐疑的で信じていないことを示している", "見せてもらいたいと積極的に頼んでいる", "すでに信じていると言っている", "証拠を集める約束をしている", "相手の言葉が正しいと認めている"],
    "expl": "'I'll believe it when I see it' は「実際に見るまで信じない・懐疑的」という慣用表現。表面上は同意しているように聞こえるが、皮肉なトーン。",
    "kp": ["I'll believe it when I see it"]
  },
  # ── CONTEXT lv3 (1問) ────────────────────────────────────────────────────
  {
    "diff": "lv3", "axis": "context",
    "text": "You know what? Forget it. I'll just handle it myself.",
    "ja": "もういい。自分でやる。",
    "answer": "相手を諦めて自分でやると決めている",
    "choices": ["相手を諦めて自分でやると決めている", "自分が担当するべきではないと言っている", "相手に全て任せると言っている", "また今度話し合おうと言っている", "喜んで協力すると申し出ている"],
    "expl": "'You know what?' は「もういい・ちょっと待って」という気持ちの切り替えを示す表現。'Forget it' と組み合わさり、諦めや苛立ちのトーンが出る。",
    "kp": ["You know what", "Forget it", "handle it myself"]
  },
  # ── CONTEXT lv4 (1問) ────────────────────────────────────────────────────
  {
    "diff": "lv4", "axis": "context",
    "text": "No pressure, but this is essentially the moment that could define the whole quarter.",
    "ja": "プレッシャーをかけるつもりはないけど、これはこの四半期全体を決定づけ得る瞬間だよ。",
    "answer": "プレッシャーをかけないと言いながら実際にはプレッシャーをかけている",
    "choices": ["プレッシャーをかけないと言いながら実際にはプレッシャーをかけている", "プレッシャーが全くないと保証している", "この四半期はもう終わったと言っている", "今は重要な瞬間ではないと言っている", "四半期の目標を変更すると言っている"],
    "expl": "'No pressure, but' のパターンは逆説的で、実際には大きなプレッシャーをかけている皮肉表現。'define the quarter' は「四半期の成果を左右する」。",
    "kp": ["no pressure but", "define the quarter"]
  },
]


def main():
    # 既存問題を読み込み
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    existing_texts = set(re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content))
    print(f"既存問題数: {len(existing_texts)}")

    # バリデーション & 重複チェック
    VALID_DIFFS = {"lv1", "lv2", "lv3", "lv4", "lv5"}
    VALID_AXES = {"vocab", "speed", "reduction", "context", "distractor"}
    REQUIRED = {"diff", "axis", "text", "ja", "answer", "choices", "expl", "kp"}

    errors = []
    duplicates = []
    for i, q in enumerate(QUESTIONS):
        missing = REQUIRED - set(q.keys())
        if missing:
            errors.append(f"[{i}] フィールド不足: {missing}")
        if q.get("diff") not in VALID_DIFFS:
            errors.append(f"[{i}] diff不正: {q.get('diff')}")
        if q.get("axis") not in VALID_AXES:
            errors.append(f"[{i}] axis不正: {q.get('axis')}")
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            errors.append(f"[{i}] choicesは5要素必要")
        if q.get("answer") != q.get("choices", [None])[0]:
            errors.append(f"[{i}] answer != choices[0]: '{q.get('answer')}' vs '{q.get('choices', [None])[0]}'")
        if not isinstance(q.get("kp"), list) or len(q["kp"]) == 0:
            errors.append(f"[{i}] kpは1要素以上必要")
        # 重複チェック
        txt = q.get("text", "")
        if txt in existing_texts:
            duplicates.append(f"[{i}] 重複: {txt[:60]}")
        # 新規問題同士の重複チェック
        for j, q2 in enumerate(QUESTIONS[:i]):
            if q.get("text") == q2.get("text"):
                duplicates.append(f"[{i}] 新規内重複 with [{j}]: {txt[:60]}")

    if errors:
        print("\n❌ バリデーションエラー:")
        for e in errors: print(f"  {e}")
    if duplicates:
        print("\n❌ 重複チェック:")
        for d in duplicates: print(f"  {d}")

    if not errors and not duplicates:
        print("✅ バリデーション・重複チェック: すべてOK")

        # diff分布確認
        from collections import Counter
        diff_dist = Counter(q["diff"] for q in QUESTIONS)
        axis_dist = Counter(q["axis"] for q in QUESTIONS)
        print(f"\ndiff分布: {dict(diff_dist)}")
        print(f"axis分布: {dict(axis_dist)}")

        # staging.jsonに書き出し
        STAGING_JSON.write_text(json.dumps(QUESTIONS, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ staging.json に {len(QUESTIONS)}問を保存しました")
    else:
        print("\n⛔ エラーがあるため staging.json への書き込みをスキップしました")
        return 1


if __name__ == "__main__":
    exit(main() or 0)
