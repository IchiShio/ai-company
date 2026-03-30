export type Level = 'lv1' | 'lv2' | 'lv3' | 'lv4' | 'lv5'

export interface Passage {
  pid: string
  wc: number
  text: string
}

export interface WordTiming {
  word: string
  start: number
  end: number
}

export interface WordRect {
  rawWord: string
  x: number
  y: number
  width: number
  height: number
  lineIndex: number
}

export interface VocabCard {
  word: string
  phonetic: string
  definition: string
  partOfSpeech: string
  // obstacle geometry
  x: number
  y: number
  width: number
  height: number
}
