import type { TextPreset } from './types'

export const PRESETS: TextPreset[] = [
  // ── Original creative presets ────────────────────────────
  {
    id: 'morning-light',
    title: 'Morning Light',
    titleJa: '朝の光',
    text: `The morning light filtered through the curtains, casting warm golden patterns across the wooden floor. She picked up her coffee, still steaming, and smiled at the thought of the day ahead. Outside, the birds had already begun their familiar chorus, a gentle reminder that the world was waking up alongside her. There was something deeply comforting about these quiet moments before the rush began — a pocket of stillness that belonged entirely to her. She took a slow sip, letting the warmth spread through her hands, and watched the dust motes dance in the sunbeams. Today, she decided, would be a good day. Not because anything extraordinary was planned, but because she had chosen to see it that way. And sometimes, that simple choice was all it took to change everything.`,
    phrases: [
      'casting warm golden patterns',
      'a pocket of stillness',
      'dust motes dance in the sunbeams',
      'the world was waking up alongside her',
      'that simple choice was all it took',
    ],
  },
  {
    id: 'ocean-thoughts',
    title: 'Ocean Thoughts',
    titleJa: '海の思考',
    text: `The ocean has a way of putting things into perspective. Standing at the shore, watching waves roll in and retreat in their endless rhythm, you begin to feel the smallness of your worries against the vastness of the water. Each wave carries something — a memory, a wish, a fragment of a story told by someone a thousand miles away. The salt air fills your lungs, and for a moment, the noise in your head quiets down. You notice the way the light breaks on the surface, how it scatters into a thousand tiny diamonds that vanish as quickly as they appear. There is beauty in impermanence, you think. The wave that just touched your feet will never return in exactly the same form. And yet the ocean remains, constant and patient, as though it has all the time in the world.`,
    phrases: [
      'the smallness of your worries',
      'a thousand tiny diamonds',
      'beauty in impermanence',
      'constant and patient',
      'the noise in your head quiets down',
    ],
  },
  {
    id: 'city-rain',
    title: 'City in the Rain',
    titleJa: '雨の街',
    text: `Rain in the city transforms everything. The streets, usually loud and rushed, take on a softer quality — footsteps muffled, voices hushed, the whole world wrapped in a gentle gray blanket. Neon signs reflect off wet pavement, stretching into long, wavering ribbons of color that ripple when someone steps through a puddle. People hurry past with umbrellas, their faces hidden, each one carrying their own private universe of thoughts. A cafe window glows amber from within, and through the glass you can see a woman reading, completely absorbed, as though the rain has built a wall between her and the outside world. The sound of it is everywhere — a constant, whispering percussion on rooftops and awnings, on leaves and on the shoulders of strangers. It asks for nothing. It simply falls, and in falling, it makes the city new again.`,
    phrases: [
      'a gentle gray blanket',
      'long wavering ribbons of color',
      'their own private universe of thoughts',
      'whispering percussion on rooftops',
      'it makes the city new again',
    ],
  },

  // ── From SyncReader passages (lv3) ───────────────────────
  {
    id: 'renaissance',
    title: 'The Renaissance',
    titleJa: 'ルネサンスの芸術',
    text: `The Renaissance marked a profound shift in artistic philosophy as artists began to move away from purely religious subjects. Figures like Michelangelo and Leonardo da Vinci explored human anatomy and perspective with scientific precision, bridging the gap between art and science. This period of cultural renewal not only revolutionized visual arts but also influenced literature, philosophy, and human thought more broadly. The legacy of this era continues to shape how we perceive creativity and innovation today.`,
    phrases: [
      'a profound shift in artistic philosophy',
      'bridging the gap between art and science',
      'the legacy of this era',
      'how we perceive creativity and innovation',
    ],
  },
  {
    id: 'silk-road',
    title: 'The Silk Road',
    titleJa: 'シルクロード',
    text: `The Silk Road was not a single road but rather a vast network of trade routes that connected East Asia with the Mediterranean region. For over 1,500 years, merchants, pilgrims, and adventurers traveled these routes, exchanging not only goods but also ideas, religions, and technologies. The Silk Road facilitated cultural interactions that profoundly influenced the development of civilizations across Asia, Europe, and the Middle East.`,
    phrases: [
      'a vast network of trade routes',
      'merchants, pilgrims, and adventurers',
      'exchanging not only goods but also ideas',
      'profoundly influenced the development of civilizations',
    ],
  },
  {
    id: 'vinyl-records',
    title: 'The Return of Vinyl',
    titleJa: 'レコードの復活',
    text: `The resurgence of vinyl records among younger generations has intrigued music industry observers. Nostalgia alone cannot account for this phenomenon; the tactile experience of playing records and the deliberate pace of listening foster a deeper connection to music. Unlike digital streaming, which prioritizes convenience and instant gratification, vinyl ownership demands intentionality and rewards attentiveness.`,
    phrases: [
      'the tactile experience of playing records',
      'a deeper connection to music',
      'prioritizes convenience and instant gratification',
      'demands intentionality and rewards attentiveness',
    ],
  },
  {
    id: 'sustainable-fashion',
    title: 'Sustainable Fashion',
    titleJa: '持続可能なファッション',
    text: `Sustainable fashion has evolved from a niche concern into a mainstream movement, yet the journey toward truly ethical consumption remains fraught with complexities. While consumers increasingly demand transparency from brands regarding their supply chains, the gap between intention and action persists. Many individuals find themselves trapped between their values and the convenience of fast fashion, revealing the tension between aspirational identity and practical lifestyle constraints.`,
    phrases: [
      'from a niche concern into a mainstream movement',
      'fraught with complexities',
      'the gap between intention and action',
      'aspirational identity and practical lifestyle constraints',
    ],
  },
  {
    id: 'dark-matter',
    title: 'Dark Matter',
    titleJa: '暗黒物質',
    text: `The concept of dark matter emerged when astronomers observed that galaxies rotate too quickly to be held together by visible matter alone. The gravitational force required to maintain such velocities suggested the existence of unseen mass. Despite decades of research, dark matter remains one of the universe's greatest mysteries. Scientists estimate that dark matter comprises approximately 27% of the total mass-energy content of the universe, while ordinary matter makes up only about 5%.`,
    phrases: [
      'too quickly to be held together',
      'the existence of unseen mass',
      'one of the universe\'s greatest mysteries',
      'the total mass-energy content of the universe',
    ],
  },
  {
    id: 'mindfulness',
    title: 'Mindfulness',
    titleJa: 'マインドフルネス',
    text: `Mindfulness, defined as the practice of maintaining non-judgmental awareness of the present moment, has gained considerable attention in psychological research. Studies indicate that regular mindfulness meditation can reduce symptoms of anxiety and depression, improve emotional regulation, and enhance cognitive flexibility. These benefits suggest that cultivating present-moment awareness may serve as a preventive measure against various mental health challenges.`,
    phrases: [
      'non-judgmental awareness of the present moment',
      'improve emotional regulation',
      'enhance cognitive flexibility',
      'cultivating present-moment awareness',
    ],
  },
  {
    id: 'keystone-species',
    title: 'Keystone Species',
    titleJa: 'キーストーン種',
    text: `The concept of keystone species refers to organisms whose ecological impact is disproportionate to their abundance. The sea otter exemplifies this principle; although they comprise a small fraction of marine ecosystems, their predation on sea urchins prevents overgrazing of kelp forests, which serve as critical habitats for numerous species. The disappearance of sea otters would trigger a cascade of ecological consequences, fundamentally altering the structure of coastal ecosystems.`,
    phrases: [
      'disproportionate to their abundance',
      'prevents overgrazing of kelp forests',
      'a cascade of ecological consequences',
      'fundamentally altering the structure',
    ],
  },
  {
    id: 'tea-ceremony',
    title: 'Japanese Tea Ceremony',
    titleJa: '茶道',
    text: `Japanese tea ceremony, known as chanoyu, is a ritualized practice of preparing and serving green tea. Developed in the 15th and 16th centuries, this ceremony embodies principles of harmony, respect, purity, and tranquility. Beyond the simple act of drinking tea, the chanoyu represents a philosophical approach to life that emphasizes aesthetic appreciation and mindfulness, influenced by Zen Buddhism.`,
    phrases: [
      'a ritualized practice',
      'harmony, respect, purity, and tranquility',
      'a philosophical approach to life',
      'aesthetic appreciation and mindfulness',
    ],
  },
]
