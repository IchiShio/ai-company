import type { ThoughtScenario } from './types'

export const SCENARIOS: ThoughtScenario[] = [
  {
    id: 'casual-plans',
    title: 'Making Weekend Plans',
    titleJa: '週末の予定を立てる',
    text: "I was thinking we could grab brunch somewhere downtown this Saturday. There's this new place that just opened up on Main Street — apparently they do amazing pancakes. After that, we could swing by the bookstore if you're up for it. I've been meaning to pick up that novel you recommended. What do you say?",
    particles: [
      { type: 'connector', label: 'flow', explanation: '"I was thinking" is a soft opener — it suggests an idea without being pushy. Natives use this instead of "I want to" to sound collaborative.', relX: 0.15, relY: 0.08 },
      { type: 'nuance', label: 'casual', explanation: '"grab brunch" uses "grab" instead of "eat" or "have" — this single word choice signals the whole tone is relaxed and informal.', relX: 0.82, relY: 0.15 },
      { type: 'idea', label: 'vague+', explanation: '"somewhere downtown" is intentionally vague. Natives often leave details loose to give the other person room to suggest alternatives.', relX: 0.75, relY: 0.35 },
      { type: 'cultural', label: 'hedge', explanation: '"if you\'re up for it" is a classic hedge — it gives the listener an easy way to say no without awkwardness. Very common in native speech.', relX: 0.2, relY: 0.55 },
      { type: 'connector', label: 'bridge', explanation: '"After that, we could" smoothly bridges two activities. "could" (not "should" or "will") keeps it as a suggestion, not a plan.', relX: 0.5, relY: 0.7 },
    ],
    wordNotes: {
      'grab': 'Casual verb for "eat/get" — signals informal register',
      'apparently': 'Hedging word — "I heard but haven\'t confirmed myself"',
      'swing': '"swing by" = casually visit, implies no pressure',
      'meaning': '"been meaning to" = intended but haven\'t done yet',
      'say': '"What do you say?" = friendly way to ask for agreement',
    },
  },
  {
    id: 'work-feedback',
    title: 'Giving Feedback at Work',
    titleJa: '職場でフィードバックする',
    text: "I really appreciate the effort you put into this report. The data analysis section is particularly strong. One thing I noticed, though, is that the executive summary could be a bit more concise. Maybe we could try leading with the key findings first? I think that would make a bigger impact on the stakeholders. Overall, though, great work.",
    particles: [
      { type: 'cultural', label: 'sandwich', explanation: 'This follows the "feedback sandwich" pattern: positive → constructive → positive. Natives use this structure instinctively in professional settings.', relX: 0.8, relY: 0.1 },
      { type: 'nuance', label: 'soften', explanation: '"One thing I noticed" is a softener. Instead of "The problem is...", it frames criticism as a personal observation, reducing defensiveness.', relX: 0.15, relY: 0.3 },
      { type: 'connector', label: 'though', explanation: '"though" at the end of a clause is a native English pivot — it signals "but here\'s a different angle" without the harshness of "but" or "however".', relX: 0.65, relY: 0.45 },
      { type: 'idea', label: 'we not you', explanation: '"Maybe we could try" uses "we" instead of "you should". This collaborative framing makes feedback feel like teamwork rather than criticism.', relX: 0.3, relY: 0.65 },
      { type: 'nuance', label: 'hedge', explanation: '"a bit more concise" — "a bit" downplays the critique. Removing it would sound much more direct and potentially harsh.', relX: 0.75, relY: 0.75 },
    ],
    wordNotes: {
      'appreciate': 'Stronger than "like" — shows genuine recognition',
      'particularly': 'Adds specificity to praise, making it feel sincere',
      'noticed': 'Frames criticism as observation, not judgment',
      'Maybe': 'Softener before a suggestion — leaves room for disagreement',
      'impact': 'Business-appropriate word for "effect/impression"',
    },
  },
  {
    id: 'storytelling',
    title: 'Telling a Story to Friends',
    titleJa: '友達に面白い話をする',
    text: "So get this — I was waiting for the train yesterday, minding my own business, when this guy just walks up to me and goes, 'Excuse me, are you famous?' I'm like, 'What? No!' And he goes, 'You sure? You look exactly like someone from TV.' Turns out he thought I was some actor from a Netflix show. I couldn't stop laughing.",
    particles: [
      { type: 'connector', label: 'hook', explanation: '"So get this" is a story-opener that immediately grabs attention. It signals "something interesting happened" and makes the listener lean in.', relX: 0.2, relY: 0.05 },
      { type: 'cultural', label: 'present', explanation: '"walks up" and "goes" are in present tense even though this happened yesterday. Natives switch to "historic present" in stories to make them feel more vivid and immediate.', relX: 0.8, relY: 0.2 },
      { type: 'nuance', label: 'quotative', explanation: '"I\'m like" and "he goes" are informal ways to quote speech. "Said" sounds too formal in casual storytelling. "Goes" and "I\'m like" are the native default.', relX: 0.15, relY: 0.45 },
      { type: 'idea', label: 'detail', explanation: '"minding my own business" adds a scene-setting detail that contrasts with the unexpected event. Good storytellers always set up the "normal" before the "surprising".', relX: 0.65, relY: 0.55 },
      { type: 'connector', label: 'reveal', explanation: '"Turns out" is a reveal phrase — it introduces the punchline or explanation. It\'s punchier than "It turned out that" or "Apparently".', relX: 0.4, relY: 0.8 },
    ],
    wordNotes: {
      'get': '"get this" = "listen to this surprising thing"',
      'minding': '"minding my own business" = doing nothing special (sets the scene)',
      'goes': 'Informal speech quotation — more natural than "said"',
      'like': '"I\'m like" = informal quote marker, very common in spoken English',
      'Turns': '"Turns out" = dramatic reveal of the explanation',
    },
  },

  // ── Scenarios from listening quiz expressions ─────────────
  {
    id: 'body-idioms',
    title: 'Body Idioms in Daily Life',
    titleJa: '体にまつわる日常イディオム',
    text: "My back is killing me — I think I slept in a weird position. And on top of that, I completely blanked during this morning's presentation. My mind just went empty. I've been on hold with tech support for forty minutes now because the Wi-Fi keeps cutting out. This is ridiculous. I can't get anything done working from home today.",
    particles: [
      { type: 'nuance', label: 'killing me', explanation: '"is killing me" doesn\'t mean literal death — it\'s a dramatic exaggeration (hyperbole) to express intense pain or annoyance. Extremely common in casual English.', relX: 0.2, relY: 0.05 },
      { type: 'idea', label: 'blanked', explanation: '"completely blanked" = mind went empty, forgot everything. Related to "drawing a blank." The adverb "completely" intensifies the embarrassment.', relX: 0.75, relY: 0.15 },
      { type: 'connector', label: 'on top of', explanation: '"on top of that" stacks complaints — it says "and if that wasn\'t bad enough..." It builds narrative momentum in a sequence of problems.', relX: 0.15, relY: 0.35 },
      { type: 'cultural', label: 'on hold', explanation: '"on hold" is a phone-specific idiom. Combined with "for forty minutes" and "This is ridiculous," it paints a universally relatable frustration picture.', relX: 0.8, relY: 0.5 },
      { type: 'nuance', label: 'keeps -ing', explanation: '"keeps cutting out" uses "keep + -ing" to express annoying repetition. It conveys that the problem isn\'t one-time but ongoing frustration.', relX: 0.4, relY: 0.7 },
    ],
    wordNotes: {
      'killing': '"is killing me" = extreme informal exaggeration for pain/annoyance',
      'blanked': '"blanked" = mind went empty (from listening quiz: "completely blanked during the presentation")',
      'hold': '"on hold" = waiting on a phone line',
      'cutting': '"cutting out" = intermittent disconnection (Wi-Fi, phone signal)',
      'ridiculous': 'Expression of frustration — stronger than "annoying," weaker than "outrageous"',
    },
  },
  {
    id: 'polite-requests',
    title: 'The Art of Polite Requests',
    titleJa: '丁寧なお願いの技術',
    text: "Could I get an extra blanket? It's a bit cold in here. Oh, and do you have this in a size medium? I can't find it on the rack. Also, table for two, please — do you have anything near the window? Sorry, one more thing: could you turn that down a little? I'm trying to get some sleep.",
    particles: [
      { type: 'nuance', label: 'could I', explanation: '"Could I" is softer than "Can I" — it adds a layer of politeness by using the conditional. "Can I get" is acceptable but more casual. Natives switch between them based on formality.', relX: 0.2, relY: 0.08 },
      { type: 'idea', label: 'a bit', explanation: '"a bit cold" uses "a bit" as a classic British-influenced understatement. Saying "It\'s very cold" would sound like a complaint; "a bit" makes it a gentle observation.', relX: 0.8, relY: 0.2 },
      { type: 'connector', label: 'Oh, and', explanation: '"Oh, and" is a casual connector that makes an additional request feel like an afterthought rather than a demand. It softens the accumulation of requests.', relX: 0.15, relY: 0.4 },
      { type: 'cultural', label: 'sorry', explanation: '"Sorry, one more thing" — English speakers apologize before imposing. This isn\'t a real apology; it\'s a social lubricant that acknowledges you\'re asking a lot.', relX: 0.7, relY: 0.6 },
      { type: 'nuance', label: 'a little', explanation: '"turn that down a little" — "a little" minimizes the request. Without it, "turn that down" sounds like a command. This tiny phrase transforms an order into a favor.', relX: 0.4, relY: 0.8 },
    ],
    wordNotes: {
      'Could': '"Could I" = polite request form (conditional mood)',
      'extra': '"extra blanket" — "extra" implies one more, not a replacement',
      'rack': '"on the rack" = display shelf in a clothing store',
      'turn': '"turn down" = reduce volume (phrasal verb)',
      'trying': '"trying to get some sleep" = attempting but being prevented',
    },
  },

  // ── Scenario from words/vocab nuance data ─────────────────
  {
    id: 'nuance-look-see-watch',
    title: 'Nuance: Look, See, Watch',
    titleJa: 'ニュアンス: look / see / watch の違い',
    text: "I looked out the window and saw a bird building a nest. I watched it for about ten minutes — it was fascinating. Then I noticed something else: a cat was watching the bird from below. The bird didn't seem to see the cat at all. I kept looking, hoping the cat would lose interest. Eventually it wandered off, and I could see the bird was safe.",
    particles: [
      { type: 'idea', label: 'look', explanation: '"look" = intentional, active — you direct your eyes somewhere on purpose. "Looked out the window" = chose to direct attention there.', relX: 0.15, relY: 0.08 },
      { type: 'idea', label: 'see', explanation: '"see" = passive perception — something enters your vision without effort. "Saw a bird" = it appeared in my field of vision naturally.', relX: 0.8, relY: 0.15 },
      { type: 'idea', label: 'watch', explanation: '"watch" = sustained, intentional observation over time. "Watched it for ten minutes" = continuously gave it attention.', relX: 0.5, relY: 0.35 },
      { type: 'nuance', label: 'notice', explanation: '"noticed something else" — "notice" bridges look and see. It means becoming aware of something, often unexpectedly. More active than "see" but less deliberate than "look."', relX: 0.2, relY: 0.55 },
      { type: 'connector', label: 'kept -ing', explanation: '"kept looking" = continued the action over time. "Keep + -ing" emphasizes persistence and adds emotional investment to the scene.', relX: 0.65, relY: 0.75 },
    ],
    wordNotes: {
      'looked': 'Active, intentional direction of eyes (from words quiz: look/see/watch distinction)',
      'saw': 'Passive perception — "it came into view"',
      'watched': 'Prolonged, focused observation — implies interest or concern',
      'noticed': 'Became aware of — between active "look" and passive "see"',
      'seem': '"didn\'t seem to see" = appeared not to notice (perception + judgment)',
    },
  },
  {
    id: 'emotion-at-work',
    title: 'Emotional Reactions at Work',
    titleJa: '仕事での感情表現',
    text: "I passed! I can't believe it. Three attempts and I finally got my certification! Honestly, I was hesitant about even trying again after failing twice. But my manager was really supportive — she kept saying, 'Don't hesitate to ask if you need help.' I'm so grateful for that. The whole team seems genuinely curious about how I pulled it off.",
    particles: [
      { type: 'nuance', label: 'can\'t believe', explanation: '"I can\'t believe it" is a joy/surprise expression. It doesn\'t mean literal disbelief — it\'s an emotional amplifier that says "this feels too good to be real."', relX: 0.75, relY: 0.05 },
      { type: 'idea', label: 'hesitant', explanation: '"hesitant about trying" — hesitant (adjective) vs. hesitate (verb). The adjective form conveys a state of mind, the verb conveys an action. Both from the same root but used differently.', relX: 0.2, relY: 0.25 },
      { type: 'cultural', label: 'supportive', explanation: 'English workplace culture values explicit verbal support. "Really supportive" + specific example ("kept saying...") is more convincing than just "she was nice."', relX: 0.8, relY: 0.4 },
      { type: 'connector', label: 'Honestly', explanation: '"Honestly" as a sentence opener signals vulnerability — the speaker is about to admit something they might not usually say. It builds trust and authenticity.', relX: 0.15, relY: 0.55 },
      { type: 'nuance', label: 'pulled it off', explanation: '"pulled it off" = succeeded at something difficult. This phrasal verb implies the success was impressive or unlikely. More vivid than just "did it."', relX: 0.55, relY: 0.75 },
    ],
    wordNotes: {
      'passed': '"I passed" = succeeded on an exam/test (from listening quiz)',
      'hesitant': 'Adjective form of "hesitate" — reluctant, unsure (from words quiz)',
      'grateful': '"grateful for" = feeling thankful — stronger than "happy about" (from words quiz)',
      'curious': '"curious about" = wanting to know more (from words quiz)',
      'pulled': '"pulled it off" = accomplished something difficult (idiom)',
    },
  },
]
