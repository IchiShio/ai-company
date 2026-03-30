export type LoomMode = 'drift' | 'breathing' | 'night' | 'custom'

export interface LoomConfig {
  mode: LoomMode
  speed: number       // 0.1 - 1.0
  fontSize: number    // 16 - 24
  bgmEnabled: boolean
  whisperEnabled: boolean
}

export interface WordRect {
  rawWord: string
  x: number
  y: number
  width: number
  height: number
  lineIndex: number
  alpha: number       // 0-1 for fade effects
  offsetX: number     // drift offset applied during render
  offsetY: number
}

export interface FloatingPhrase {
  text: string
  x: number
  y: number
  alpha: number
  speed: number       // px per second
  fontSize: number
}

export interface WaveRipple {
  x: number
  y: number
  radius: number
  strength: number
  born: number        // timestamp
}

export interface TextPreset {
  id: string
  title: string
  titleJa: string
  text: string
  phrases: string[]   // key phrases to float
}
