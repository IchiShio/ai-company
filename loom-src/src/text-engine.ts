import { prepareWithSegments, layoutWithLines, layoutNextLine } from '@chenglou/pretext'
import type { WordRect } from './types'

export const BASE_FONT_SIZE = 19
export const LINE_HEIGHT = 36
export const PADDING = 48

let measureCanvas: HTMLCanvasElement | null = null
let measureCtx: CanvasRenderingContext2D | null = null

export function getFont(size: number = BASE_FONT_SIZE): string {
  return `${size}px Georgia, "Noto Serif", "Hiragino Mincho ProN", serif`
}

function getMeasureCtx(font: string): CanvasRenderingContext2D {
  if (!measureCtx) {
    measureCanvas = document.createElement('canvas')
    measureCtx = measureCanvas.getContext('2d')!
  }
  measureCtx.font = font
  return measureCtx
}

function extractWordsFromLine(
  lineText: string,
  startX: number,
  lineIndex: number,
  lineY: number,
  font: string,
): WordRect[] {
  const ctx = getMeasureCtx(font)
  const rects: WordRect[] = []
  const parts = lineText.split(/(\s+)/)
  let x = startX

  for (const part of parts) {
    const w = ctx.measureText(part).width
    if (part && !/^\s+$/.test(part)) {
      rects.push({
        rawWord: part,
        x, y: lineY,
        width: w, height: LINE_HEIGHT,
        lineIndex,
        alpha: 1,
        offsetX: 0,
        offsetY: 0,
      })
    }
    x += w
  }
  return rects
}

/**
 * Standard layout (no wave offsets).
 */
export function computeLayout(
  text: string,
  containerWidth: number,
  fontSize: number = BASE_FONT_SIZE,
): { rects: WordRect[]; lineCount: number } {
  const font = getFont(fontSize)
  const prepared = prepareWithSegments(text, font)
  const maxWidth = containerWidth - PADDING * 2
  const result = layoutWithLines(prepared, maxWidth, LINE_HEIGHT)

  const rects: WordRect[] = []
  result.lines.forEach((line, lineIndex) => {
    const lineY = lineIndex * LINE_HEIGHT
    rects.push(...extractWordsFromLine(line.text, PADDING, lineIndex, lineY, font))
  })

  return { rects, lineCount: result.lineCount }
}

/**
 * Wavy layout: each line gets a slightly different width, creating a subtle wave effect.
 */
export function computeWavyLayout(
  text: string,
  containerWidth: number,
  waveOffsets: number[],
  fontSize: number = BASE_FONT_SIZE,
): { rects: WordRect[]; lineCount: number } {
  const font = getFont(fontSize)
  const prepared = prepareWithSegments(text, font)
  const rects: WordRect[] = []
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  let lineIndex = 0
  const baseWidth = containerWidth - PADDING * 2

  while (true) {
    const offset = waveOffsets[lineIndex] ?? 0
    const maxWidth = Math.max(baseWidth + offset, 100)
    const line = layoutNextLine(prepared, cursor, maxWidth)
    if (!line) break

    const lineY = lineIndex * LINE_HEIGHT
    const startX = PADDING - offset / 2
    rects.push(...extractWordsFromLine(line.text, startX, lineIndex, lineY, font))
    cursor = line.end
    lineIndex++

    if (lineIndex > 500) break
  }

  return { rects, lineCount: lineIndex }
}
