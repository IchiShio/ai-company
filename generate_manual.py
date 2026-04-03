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
# 手動生成問題 50問
# vocab 25問 / speed 25問
# diff分布: lv1×11, lv2×14, lv3×13, lv4×7, lv5×5
# ──────────────────────────────────────────────
QUESTIONS = [
  # ── VOCAB ─────────────────────────────────────────────────────────────────
  {
    "diff": "lv2", "axis": "vocab",
    "text": "I know it's tough, but we need to bite the bullet and make the announcement.",
    "ja": "大変なのはわかってるけど、歯を食いしばって発表するしかない。",
    "answer": "困難を覚悟して決断する",
    "choices": ["困難を覚悟して決断する", "後退して様子を見る", "問題を先送りにする", "誰かに助けを求める", "計画を白紙に戻す"],
    "expl": "bite the bullet は「歯を食いしばって耐える・困難を覚悟して前進する」という慣用表現。",
    "kp": ["bite the bullet", "make the announcement"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "She's still on the fence about accepting the offer. The relocation is really putting her off.",
    "ja": "彼女はまだそのオファーを受けるか迷っている。転居が本当にネックで。",
    "answer": "迷っている・決断できずにいる",
    "choices": ["迷っている・決断できずにいる", "断ろうとしている", "前向きに検討している", "既に断った", "上司に相談している"],
    "expl": "on the fence は「まだ決断できずにいる・二択で迷っている」状態を指す。",
    "kp": ["on the fence", "putting her off"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "Just give me a ballpark figure. I don't need the exact breakdown right now.",
    "ja": "おおよその数字でいいよ。今は詳細な内訳はいらない。",
    "answer": "おおよその見積もり",
    "choices": ["おおよその見積もり", "正確な計算結果", "最終的な請求額", "過去の売上データ", "競合他社の価格"],
    "expl": "ballpark figure は「おおよその数字・概算」を意味するビジネス表現。",
    "kp": ["ballpark figure", "exact breakdown"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "We're already behind, but please don't cut corners on quality. It'll cost us more later.",
    "ja": "すでに遅れているけど、品質で手を抜かないで。後でもっとコストがかかるから。",
    "answer": "手を抜く・品質を犠牲にして近道をする",
    "choices": ["手を抜く・品質を犠牲にして近道をする", "締め切りを延ばす", "予算を増やす", "担当者を変える", "プロジェクトを中止する"],
    "expl": "cut corners は「手を抜く・品質を犠牲にして近道をする」という否定的な表現。",
    "kp": ["cut corners", "quality"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "He really bit off more than he could chew by taking on three clients at once.",
    "ja": "3社のクライアントを一度に引き受けて、完全に手に余る状態になってしまった。",
    "answer": "自分の能力を超えたことを引き受ける",
    "choices": ["自分の能力を超えたことを引き受ける", "几帳面に仕事をこなす", "上司に反発する", "同僚に仕事を押し付ける", "ストレスで倒れる"],
    "expl": "bite off more than one can chew は「処理しきれないほど多くを引き受ける」慣用句。",
    "kp": ["bit off more than he could chew", "three clients at once"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "I got cold feet right before the speech and almost backed out.",
    "ja": "スピーチの直前に怖気づいて、危うくやめるところだった。",
    "answer": "直前に尻込みする・急に不安になる",
    "choices": ["直前に尻込みする・急に不安になる", "体調不良になる", "遅刻する", "内容を変更する", "自信が出てくる"],
    "expl": "get cold feet は「直前に怖気づく・不安になって躊躇する」表現。",
    "kp": ["cold feet", "backed out"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "You really hit the nail on the head. That's exactly what I've been thinking.",
    "ja": "まさにそれだよ。私がずっと考えていたことをずばり言い当ててくれた。",
    "answer": "ずばり核心をついている",
    "choices": ["ずばり核心をついている", "問題を大げさに言っている", "的外れなことを言っている", "遠まわしに批判している", "うまく話をそらしている"],
    "expl": "hit the nail on the head は「ずばり核心をつく・正確に言い当てる」慣用句。",
    "kp": ["hit the nail on the head", "exactly what I've been thinking"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "Don't spill the beans, okay? It's supposed to be a surprise birthday party.",
    "ja": "秘密をばらしちゃダメだよ。サプライズの誕生日パーティーのはずだから。",
    "answer": "秘密を漏らす",
    "choices": ["秘密を漏らす", "パーティーを断る", "食べ物を持ってくる", "遅れてくる", "場所を間違える"],
    "expl": "spill the beans は「秘密を漏らす・うっかりバラしてしまう」というカジュアルな表現。",
    "kp": ["spill the beans", "surprise birthday party"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "I'd rather just walk away than burn bridges over something like this.",
    "ja": "こんなことで橋を焼くくらいなら引き下がる方がいい。",
    "answer": "関係を壊して後戻りできなくする",
    "choices": ["関係を壊して後戻りできなくする", "新しい人脈を作る", "過去を忘れて前に進む", "競合他社に乗り換える", "交渉を有利に進める"],
    "expl": "burn bridges は「関係を完全に断ち切る・後戻りできない状況を作る」という表現。",
    "kp": ["burn bridges", "walk away"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "He says the market's going to bounce back, but I'd take it with a grain of salt.",
    "ja": "彼は市場が持ち直すと言っているけど、話半分に聞いておいた方がいいと思う。",
    "answer": "話半分に聞く・疑ってかかる",
    "choices": ["話半分に聞く・疑ってかかる", "そのまま信じる", "専門家の意見を聞く", "データを確認する", "強く賛同する"],
    "expl": "take with a grain of salt は「半信半疑で聞く・割り引いて受け取る」という表現。",
    "kp": ["take it with a grain of salt", "bounce back"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "I'm totally wiped out. I think I'm going to hit the sack early.",
    "ja": "もうヘトヘトだ。早めに寝ることにする。",
    "answer": "寝る",
    "choices": ["寝る", "シャワーを浴びる", "食事をする", "外出する", "テレビを見る"],
    "expl": "hit the sack は「寝る」という口語表現。hit the bed / hit the hay とも言う。",
    "kp": ["hit the sack", "wiped out"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "She gave me the cold shoulder the entire time at the office today.",
    "ja": "今日は職場でずっと彼女に無視された。",
    "answer": "冷たく無視する・そっけなくする",
    "choices": ["冷たく無視する・そっけなくする", "激しく言い争う", "公然と批判する", "話しかけすぎる", "仕事を押し付ける"],
    "expl": "give someone the cold shoulder は「冷たくあしらう・無視する」という表現。",
    "kp": ["cold shoulder", "the entire time"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "We're really under the gun here. The client wants a response by end of day.",
    "ja": "ここは本当にプレッシャーだ。クライアントが今日中に返答を求めている。",
    "answer": "厳しい締め切りや圧力にさらされている",
    "choices": ["厳しい締め切りや圧力にさらされている", "武装して準備ができている", "クライアントと対立している", "目標を達成した", "予算が超過している"],
    "expl": "under the gun は「タイトな締め切りや強いプレッシャーにさらされている」状態。",
    "kp": ["under the gun", "end of day"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "Keep me in the loop once you hear back from the client.",
    "ja": "クライアントから返事があったら知らせてね。",
    "answer": "最新情報を知らせ続ける",
    "choices": ["最新情報を知らせ続ける", "すぐに判断する", "会議に呼ぶ", "結果を公表する", "相談に乗る"],
    "expl": "keep someone in the loop は「常に情報共有する・最新状況を知らせる」というビジネス表現。",
    "kp": ["in the loop", "hear back from"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "They've been dragging their feet on the contract for weeks. I'm starting to get worried.",
    "ja": "何週間も契約をぐずぐず先延ばしにしている。心配になってきた。",
    "answer": "わざとゆっくりやる・ぐずぐずする",
    "choices": ["わざとゆっくりやる・ぐずぐずする", "迅速に処理する", "契約を拒否する", "条件を変更する", "担当者を変える"],
    "expl": "drag one's feet は「故意に遅らせる・ぐずぐずする」という表現。",
    "kp": ["dragging their feet", "weeks"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "I've got a lot on my plate this week. Can we push the meeting to next Monday?",
    "ja": "今週はやることが山積みで。打ち合わせを来週月曜に延ばせる？",
    "answer": "仕事が山積みで手がいっぱい",
    "choices": ["仕事が山積みで手がいっぱい", "お腹いっぱいで食べられない", "仕事に飽きている", "会議が嫌いだ", "今日は体調が悪い"],
    "expl": "have a lot on one's plate は「仕事が山積みで忙しい」という慣用表現。",
    "kp": ["a lot on my plate", "push the meeting"]
  },
  {
    "diff": "lv4", "axis": "vocab",
    "text": "After three failed attempts, the team was ready to throw in the towel. Then management stepped in.",
    "ja": "3度失敗した後、チームはあきらめかけていた。そこで経営陣が介入した。",
    "answer": "あきらめる・降参する",
    "choices": ["あきらめる・降参する", "さらに力を入れる", "チームを解散する", "新しい予算を申請する", "外部コンサルを雇う"],
    "expl": "throw in the towel はボクシング由来で「タオルを投げる＝試合放棄」から「あきらめる」を意味する。",
    "kp": ["throw in the towel", "stepped in"]
  },
  {
    "diff": "lv4", "axis": "vocab",
    "text": "If you read between the lines, she was basically asking to be reassigned.",
    "ja": "行間を読めば、彼女は基本的に配置換えを求めていた。",
    "answer": "言外の意味を読み取る",
    "choices": ["言外の意味を読み取る", "文章を丁寧に校正する", "細かい条件を確認する", "噂を信じる", "感情的に反応する"],
    "expl": "read between the lines は「表面に書かれていない本当の意味を読み取る」表現。",
    "kp": ["read between the lines", "reassigned"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "The sudden announcement really caught everyone off guard. Nobody expected it.",
    "ja": "突然の発表は誰もの不意をついた。誰も予想していなかった。",
    "answer": "不意をつく・準備のない状態で驚かせる",
    "choices": ["不意をつく・準備のない状態で驚かせる", "全員を怒らせる", "安心させる", "期待に応える", "注目を集める"],
    "expl": "catch someone off guard は「不意をつく・準備のできていないところを驚かせる」表現。",
    "kp": ["caught everyone off guard", "nobody expected it"]
  },
  {
    "diff": "lv4", "axis": "vocab",
    "text": "We're on thin ice with this client after missing two deadlines. One more mistake could end it.",
    "ja": "2回締め切りを守れず、このクライアントとの関係は薄氷の上に乗っている。もう一度失敗すれば終わりかもしれない。",
    "answer": "危険な状況にある・一歩間違えるとまずい",
    "choices": ["危険な状況にある・一歩間違えるとまずい", "信頼関係が深まっている", "予算の交渉中である", "競合他社と比較されている", "新しいプロジェクトを提案された"],
    "expl": "on thin ice は「薄い氷の上＝危険な状況、一歩間違えれば大変なことになる」比喩表現。",
    "kp": ["on thin ice", "missing two deadlines"]
  },
  {
    "diff": "lv3", "axis": "vocab",
    "text": "After the investment fell through, the startup was basically back to square one.",
    "ja": "投資が失敗して、そのスタートアップは基本的に振り出しに戻ってしまった。",
    "answer": "振り出しに戻る・最初からやり直す",
    "choices": ["振り出しに戻る・最初からやり直す", "新しいパートナーを見つける", "規模を縮小する", "投資家を訴える", "海外に市場を移す"],
    "expl": "back to square one は「振り出しに戻る・最初からやり直す」意味のイディオム。",
    "kp": ["back to square one", "fell through"]
  },
  {
    "diff": "lv2", "axis": "vocab",
    "text": "Not everyone is pulling their weight on this project. It's starting to show.",
    "ja": "このプロジェクトで全員が自分の役割を果たしているわけじゃない。目に見えてきた。",
    "answer": "自分の役割・責任をきちんと果たす",
    "choices": ["自分の役割・責任をきちんと果たす", "残業を避ける", "昇進を狙う", "リーダーに媚びる", "仕事を断る"],
    "expl": "pull one's weight は「自分に割り当てられた仕事をきちんとこなす」というイディオム。",
    "kp": ["pulling their weight", "starting to show"]
  },
  {
    "diff": "lv1", "axis": "vocab",
    "text": "Alright, let's call it a day. We'll pick this up fresh in the morning.",
    "ja": "よし、今日はここまでにしよう。明朝に新鮮な気持ちで再開しよう。",
    "answer": "今日の作業を終える",
    "choices": ["今日の作業を終える", "会議を予約する", "全員に連絡する", "一休みしてから続ける", "担当者を変更する"],
    "expl": "call it a day は「今日の仕事・作業はここで終わりにする」という表現。",
    "kp": ["call it a day", "pick this up"]
  },
  {
    "diff": "lv5", "axis": "vocab",
    "text": "Look, we can't keep kicking the can down the road on this. The board wants a decision.",
    "ja": "結局のところ、この問題を先送りし続けることはできない。取締役会は決断を求めている。",
    "answer": "問題を先送りにし続ける",
    "choices": ["問題を先送りにし続ける", "迅速に対応する", "情報を隠す", "責任者を処罰する", "外部に助けを求める"],
    "expl": "kick the can down the road は「問題を先送りにする」という政治・ビジネスでよく使われる表現。",
    "kp": ["kicking the can down the road", "board wants a decision"]
  },
  {
    "diff": "lv5", "axis": "vocab",
    "text": "The merger looked disastrous at first, but it turned out to be a blessing in disguise — revenue doubled.",
    "ja": "合併は最初は失敗に見えたが、結果的には災い転じて福となった。収益が倍になったのだ。",
    "answer": "一見不運に見えて実は幸運なこと",
    "choices": ["一見不運に見えて実は幸運なこと", "予想通りの成功", "計画的な戦略の成果", "短期的な損失で終わった", "競合他社を驚かせた"],
    "expl": "a blessing in disguise は「表向きは不運・失敗に見えるが、実は良い結果をもたらすもの」。",
    "kp": ["blessing in disguise", "turned out to be"]
  },

  # ── SPEED ─────────────────────────────────────────────────────────────────
  {
    "diff": "lv1", "axis": "speed",
    "text": "Whatcha doin' later? Wanna grab a coffee?",
    "ja": "後で何するの？コーヒーでも飲みに行かない？",
    "answer": "後での予定を聞いている",
    "choices": ["後での予定を聞いている", "今すぐ来るよう誘っている", "コーヒーを注文している", "昨日の話をしている", "天気の話をしている"],
    "expl": "Whatcha = What are you、Wanna = want to。連音変化した口語表現。",
    "kp": ["Whatcha doin'", "Wanna grab"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Lemme grab my coat and I'll be right with ya.",
    "ja": "コートを取ってきたらすぐ行くよ。",
    "answer": "コートを取ってきたらすぐ戻ると言っている",
    "choices": ["コートを取ってきたらすぐ戻ると言っている", "先に行くよう伝えている", "コートを探している", "外は寒いと言っている", "準備ができていないと言っている"],
    "expl": "Lemme = Let me、ya = you。",
    "kp": ["Lemme grab", "be right with ya"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Didja finish the report? Boss is gonna want it by noon.",
    "ja": "レポート終わった？上司が正午までに欲しいって言うと思う。",
    "answer": "レポートが完成したか確認している",
    "choices": ["レポートが完成したか確認している", "上司の指示に反論している", "締め切りを変更しようとしている", "報告書の内容を質問している", "手伝いを申し出ている"],
    "expl": "Didja = Did you、gonna = going to。",
    "kp": ["Didja finish", "gonna want it"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "I dunno about this one. It's kinda risky, don'tcha think?",
    "ja": "これはどうだろうな。ちょっとリスクがあると思わない？",
    "answer": "提案に対して懸念を示している",
    "choices": ["提案に対して懸念を示している", "強く賛成している", "詳細を確認している", "別の案を出している", "賛否を問うている"],
    "expl": "I dunno = I don't know、kinda = kind of、don'tcha = don't you。",
    "kp": ["I dunno", "kinda risky", "don'tcha think"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Gonna be a bit late. Save me a seat!",
    "ja": "少し遅れる。席取っておいて！",
    "answer": "遅れることを伝えている",
    "choices": ["遅れることを伝えている", "今向かっていると言っている", "キャンセルを伝えている", "場所を確認している", "先に行くよう促している"],
    "expl": "Gonna = going to。主語 I が省略された速い口語。",
    "kp": ["Gonna be a bit late", "Save me a seat"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Couldya turn down the TV? Tryna get some work done in here.",
    "ja": "テレビの音を下げてくれない？ここで仕事しようとしてるんだけど。",
    "answer": "テレビの音量を下げてほしいと頼んでいる",
    "choices": ["テレビの音量を下げてほしいと頼んでいる", "チャンネルを変えてほしいと頼んでいる", "テレビを消してほしいと言っている", "仕事の邪魔をしていると非難している", "一緒にテレビを見たいと誘っている"],
    "expl": "Couldya = Could you、Tryna = trying to。連音・短縮の典型例。",
    "kp": ["Couldya", "Tryna get some work done"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Wouldja mind helping me carry this upstairs? It's pretty heavy.",
    "ja": "これを上に運ぶの手伝ってくれない？かなり重いんだよね。",
    "answer": "荷物を運ぶのを手伝ってほしいと頼んでいる",
    "choices": ["荷物を運ぶのを手伝ってほしいと頼んでいる", "一緒に階段を使うよう誘っている", "重い荷物の中身を尋ねている", "荷物を持ってどこかに行くと言っている", "エレベーターを使うよう提案している"],
    "expl": "Wouldja = Would you。丁寧な依頼表現の短縮形。",
    "kp": ["Wouldja mind", "pretty heavy"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Shoulda texted me before you left. I woulda waited for ya.",
    "ja": "出発前にメッセージしてくれれば良かったのに。待っていたのに。",
    "answer": "事前に連絡してほしかったと後悔を述べている",
    "choices": ["事前に連絡してほしかったと後悔を述べている", "もう帰ってしまったと伝えている", "次回は自分が連絡すると約束している", "メッセージが届かなかったと言っている", "なぜ待てなかったか説明している"],
    "expl": "Shoulda = should have、woulda = would have、ya = you。仮定法過去完了の短縮形。",
    "kp": ["Shoulda texted", "woulda waited", "ya"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Hafta say, I wasn't expecting much, but that movie totally blew me away.",
    "ja": "正直言って、あまり期待していなかったけど、あの映画は本当に驚かせてくれた。",
    "answer": "映画が予想以上に良かったと言っている",
    "choices": ["映画が予想以上に良かったと言っている", "映画が期待通りだったと言っている", "映画をすすめられたと言っている", "映画が期待外れだったと言っている", "映画について何も知らなかったと言っている"],
    "expl": "Hafta = have to。blew me away = 驚かせた・感動させた。",
    "kp": ["Hafta say", "blew me away"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Issat your jacket on the chair? Someone almost sat on it.",
    "ja": "あれ、椅子の上の上着あなたのもの？誰かが危うく座るところだったよ。",
    "answer": "上着を確認しながら注意を促している",
    "choices": ["上着を確認しながら注意を促している", "上着を探している", "落し物だと伝えている", "椅子を譲るよう頼んでいる", "席を確保しようとしている"],
    "expl": "Issat = Is that。",
    "kp": ["Issat", "almost sat on it"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Yknow what, I'm just gonna cancel. I'm not really feelin' it tonight.",
    "ja": "やっぱりキャンセルする。今夜はあまり気乗りしない。",
    "answer": "予定をキャンセルしようとしている",
    "choices": ["予定をキャンセルしようとしている", "別の場所に変更しようとしている", "遅れることを伝えている", "早めに帰ろうとしている", "誰かに代わりに行くよう頼んでいる"],
    "expl": "Yknow = You know、feelin' it = feeling like going / feeling motivated。",
    "kp": ["Yknow what", "not really feelin' it"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "I hadda stay and clean the whole thing up 'cause everyone else just bailed on us.",
    "ja": "他の全員がさっさと逃げたから、全部一人で片付けるはめになった。",
    "answer": "他の人が帰ったために一人で後片付けをした",
    "choices": ["他の人が帰ったために一人で後片付けをした", "全員で協力して後片付けをした", "帰宅を許可されなかった", "残業を志願した", "後片付けの担当だった"],
    "expl": "hadda = had to、'cause = because、bailed = 急に逃げる・さっさと帰る。",
    "kp": ["hadda stay", "'cause", "bailed on us"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Doncha have soccer today? I thought it was every Tuesday.",
    "ja": "今日はサッカーじゃないの？毎週火曜だと思ってたけど。",
    "answer": "サッカーの練習があるか確認している",
    "choices": ["サッカーの練習があるか確認している", "練習をサボるよう誘っている", "練習の場所を聞いている", "一緒に行こうと誘っている", "練習が終わったか確認している"],
    "expl": "Doncha = Don't you。",
    "kp": ["Doncha have", "every Tuesday"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "I dunno whatcher so worked up about. S'not like I said it on purpose.",
    "ja": "何がそんなに頭にくるの。わざと言ったわけじゃないんだから。",
    "answer": "故意ではなかったと弁明している",
    "choices": ["故意ではなかったと弁明している", "謝罪して理解を求めている", "相手の言動を批判している", "感情的な話し合いを避けている", "その場を立ち去ろうとしている"],
    "expl": "whatcher = what you're、S'not = It's not、worked up = 怒っている・興奮している。",
    "kp": ["whatcher", "S'not like", "on purpose"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Gonna be honest, I kinda regret bringing it up. Everyone got so weird about it.",
    "ja": "正直に言うと、あれを話題にしたことをちょっと後悔してる。みんな変な反応をしてきて。",
    "answer": "話題を持ち出したことを後悔している",
    "choices": ["話題を持ち出したことを後悔している", "誰かに謝ろうとしている", "話題を変えようとしている", "周りの人を批判している", "もっと早く話すべきだったと言っている"],
    "expl": "Gonna = going to、kinda = kind of。got weird about it = 変な反応をした。",
    "kp": ["Gonna be honest", "kinda regret", "got so weird"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "Whaddya mean you didn't get the invite? I sent it to everyone on the list.",
    "ja": "招待状が届かなかったってどういうこと？リストにいる全員に送ったのに。",
    "answer": "招待状が届かなかったことに困惑している",
    "choices": ["招待状が届かなかったことに困惑している", "招待を断られたことに怒っている", "招待状を再送すると言っている", "送信先を間違えたと謝っている", "パーティーを中止にすると言っている"],
    "expl": "Whaddya = What do you。驚きや困惑を含んだ速い口語表現。",
    "kp": ["Whaddya mean", "didn't get the invite"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Wanna come over tonight? We're watching the game.",
    "ja": "今夜うちに来ない？試合を見るつもりだよ。",
    "answer": "試合を一緒に見るよう誘っている",
    "choices": ["試合を一緒に見るよう誘っている", "スタジアムに行こうと誘っている", "試合について感想を聞いている", "一人で試合を見ると伝えている", "チケットを買ってほしいと頼んでいる"],
    "expl": "Wanna = want to。",
    "kp": ["Wanna come over", "watching the game"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "We were s'posed to wrap up by three, but now we're lookin' at five, maybe six.",
    "ja": "3時に終わる予定だったのに、今は5時、ひょっとすれば6時になりそう。",
    "answer": "予定よりかなり遅くなりそうだと伝えている",
    "choices": ["予定よりかなり遅くなりそうだと伝えている", "早めに終わりそうだと喜んでいる", "待ち合わせ場所を変更している", "3時の会議を確認している", "仕事をやめると言っている"],
    "expl": "s'posed = supposed、lookin' at = expect/anticipate（見込みを表す口語）。",
    "kp": ["s'posed to wrap up", "lookin' at five"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Gotta be somewhere by six. Think we can speed this up a little?",
    "ja": "6時までにどこかに行かないといけない。少し急ぎめにできる？",
    "answer": "急いでほしいと頼んでいる",
    "choices": ["急いでほしいと頼んでいる", "6時に待ち合わせを提案している", "先に帰ると伝えている", "時間を確認している", "予定を変えたいと言っている"],
    "expl": "Gotta = got to（have to）。",
    "kp": ["Gotta be somewhere", "speed this up"]
  },
  {
    "diff": "lv2", "axis": "speed",
    "text": "I'm so hungry I could eat a horse. Whatcha feel like having?",
    "ja": "めちゃくちゃお腹空いた。何食べたい？",
    "answer": "非常にお腹が空いていると伝えている",
    "choices": ["非常にお腹が空いていると伝えている", "夕食の予算を決めている", "健康的な食事を提案している", "レストランを予約しようとしている", "料理の種類を質問している"],
    "expl": "I could eat a horse =「馬一頭食べられるくらい空腹」という誇張表現。Whatcha = what do you。",
    "kp": ["eat a horse", "Whatcha feel like"]
  },
  {
    "diff": "lv1", "axis": "speed",
    "text": "Hang on, gonna grab my keys. Two secs.",
    "ja": "ちょっと待って、鍵を取ってくる。すぐだから。",
    "answer": "鍵を取ってくるのですぐ戻ると言っている",
    "choices": ["鍵を取ってくるのですぐ戻ると言っている", "鍵を探すのを手伝ってほしいと頼んでいる", "鍵を誰かに渡すと言っている", "ドアを開けてほしいと頼んでいる", "鍵を忘れたと言っている"],
    "expl": "gonna = going to、Two secs = two seconds（すぐ戻る）。",
    "kp": ["gonna grab", "Two secs"]
  },
  {
    "diff": "lv5", "axis": "speed",
    "text": "Aight, so basically what hadda happen was, we hadda loop the CFO in early 'cause the numbers weren't addin' up.",
    "ja": "つまり、結局何が起きたかというと、数字が合わなかったからCFOを早めに巻き込まなきゃいけなかったんだ。",
    "answer": "数字の不整合のためCFOを早期に関与させた",
    "choices": ["数字の不整合のためCFOを早期に関与させた", "CFOが突然会議に割り込んできた", "数字が合わなかったのでプロジェクトを中止した", "CFOの承認を後から取り付けた", "会計処理のミスを誰かに報告した"],
    "expl": "Aight = alright、hadda = had to、loop in = 巻き込む、addin' up = 合計が合う。複数の短縮・連音が重なった高速発話。",
    "kp": ["hadda", "loop the CFO in", "addin' up"]
  },
  {
    "diff": "lv5", "axis": "speed",
    "text": "Yknow, if she'da just told me upfront, we coulda avoided this whole mess. Now I dunno whatcha gonna do.",
    "ja": "最初からちゃんと話してくれていれば、この混乱全部避けられたのに。今となっては、どうするつもりなのかわからない。",
    "answer": "最初に正直に話してくれれば問題は起きなかったと言っている",
    "choices": ["最初に正直に話してくれれば問題は起きなかったと言っている", "状況がさらに悪化することを予告している", "誰かに責任を取るよう求めている", "問題を解決する方法を提案している", "相手を励まして支援を約束している"],
    "expl": "she'da = she would have、coulda = could have、whatcha = what you're。複数の仮定法短縮が連続する上級レベル。",
    "kp": ["she'da", "coulda avoided", "whatcha gonna do"]
  },
  {
    "diff": "lv4", "axis": "speed",
    "text": "I'm not tryna start anything, but the way she said it kinda rubbed me the wrong way.",
    "ja": "揉め事を起こしたいわけじゃないけど、彼女の言い方がちょっと気に障った。",
    "answer": "相手の言い方が気に入らなかったと言っている",
    "choices": ["相手の言い方が気に入らなかったと言っている", "誰かに謝罪を求めようとしている", "冷静に状況を説明している", "喧嘩を売ろうとしている", "相手を褒めようとしている"],
    "expl": "tryna = trying to、kinda = kind of、rubbed me the wrong way = 気に障る・嫌な感じを受ける。",
    "kp": ["tryna start anything", "rubbed me the wrong way"]
  },
  {
    "diff": "lv3", "axis": "speed",
    "text": "Doncha worry about it. I'll take care of it. Just send it over when you're done.",
    "ja": "気にしないで。私がやっておくから。終わったら送ってくれるだけでいいよ。",
    "answer": "自分が対応するから心配しないよう伝えている",
    "choices": ["自分が対応するから心配しないよう伝えている", "今すぐ資料を送るよう急かしている", "仕事を断っている", "締め切りを確認している", "相手を批判している"],
    "expl": "Doncha = Don't you。take care of it = 処理する・対応する。",
    "kp": ["Doncha worry", "I'll take care of it", "send it over"]
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
