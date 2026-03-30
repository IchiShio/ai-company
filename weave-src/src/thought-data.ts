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
]
