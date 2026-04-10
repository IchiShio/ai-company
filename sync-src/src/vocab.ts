import type { VocabCard } from './types'

const cache = new Map<string, VocabCard | null>()

export async function fetchVocab(
  rawWord: string,
  _wordX: number,
  wordY: number,
  _wordHeight: number,
  containerWidth: number,
): Promise<VocabCard | null> {
  const word = rawWord.replace(/[^a-zA-Z'-]/g, '').toLowerCase()
  if (!word || word.length < 2) return null

  if (cache.has(word)) {
    const cached = cache.get(word)!
    return cached ? positionCard(cached, wordY, containerWidth) : null
  }

  try {
    const res  = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`)
    if (!res.ok) { cache.set(word, null); return null }
    const data = await res.json() as DictionaryEntry[]
    const entry = data[0]
    if (!entry) { cache.set(word, null); return null }

    const meaning = entry.meanings?.[0]
    const defObj  = meaning?.definitions?.[0]

    const partial: Omit<VocabCard, 'x'|'y'|'width'|'height'> = {
      word      : entry.word,
      phonetic  : entry.phonetic ?? entry.phonetics?.[0]?.text ?? '',
      partOfSpeech: meaning?.partOfSpeech ?? '',
      definition: defObj?.definition ?? '',
    }

    // Trim long definitions
    if (partial.definition.length > 120) {
      partial.definition = partial.definition.slice(0, 117) + '…'
    }

    const base: VocabCard = { ...partial, x: 0, y: 0, width: 0, height: 0 }
    cache.set(word, base)
    return positionCard(base, wordY, containerWidth)
  } catch {
    cache.set(word, null)
    return null
  }
}

function positionCard(
  base: VocabCard,
  wordY: number,
  containerWidth: number,
): VocabCard {
  const CARD_W  = 220
  const CARD_H  = estimateCardHeight(base.definition, base.phonetic)
  const PADDING = 24

  // Try to place card in top-right corner (obstacle area)
  const x = containerWidth - CARD_W - PADDING
  const y = Math.max(0, wordY - CARD_H / 2)

  return { ...base, x, y, width: CARD_W, height: CARD_H }
}

function estimateCardHeight(definition: string, phonetic: string): number {
  const defLines = Math.ceil(definition.length / 28) // ~28 chars/line at card width
  return 16 + 14 + (phonetic ? 16 : 0) + 18 + defLines * 18 + 16
}

// ─── Free Dictionary API shape ────────────────────────────────────────────────
interface DictionaryEntry {
  word     : string
  phonetic?: string
  phonetics?: { text?: string }[]
  meanings?: {
    partOfSpeech: string
    definitions : { definition: string }[]
  }[]
}
