import { prepareWithSegments, layoutWithLines, layoutNextLine } from '@chenglou/pretext'
import type { WordRect, VocabCard } from './types'

export const FONT = '17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
export const LINE_HEIGHT = 30
export const PADDING_X = 24

// Measurement canvas reused for word-width queries
let measureCanvas: HTMLCanvasElement | null = null
let measureCtx: CanvasRenderingContext2D | null = null

function getMeasureCtx(): CanvasRenderingContext2D {
  if (!measureCtx) {
    measureCanvas = document.createElement('canvas')
    measureCtx = measureCanvas.getContext('2d')!
    measureCtx.font = FONT
  }
  return measureCtx
}

/**
 * Split a line's text into word + whitespace tokens,
 * returning their x positions and widths.
 */
function extractWordsFromLine(
  lineText: string,
  startX: number,
  lineIndex: number,
  lineY: number,
): WordRect[] {
  const ctx = getMeasureCtx()
  const rects: WordRect[] = []
  const parts = lineText.split(/(\s+)/)
  let x = startX

  for (const part of parts) {
    const w = ctx.measureText(part).width
    if (part && !/^\s+$/.test(part)) {
      rects.push({ rawWord: part, x, y: lineY, width: w, height: LINE_HEIGHT, lineIndex })
    }
    x += w
  }

  return rects
}

/**
 * Layout passage text into word rects, optionally wrapping around a vocab card obstacle.
 *
 * The obstacle is placed in the top-right corner of the text area.
 * Lines whose y range overlaps with the card get a reduced maxWidth.
 */
export function computeWordRects(
  text: string,
  containerWidth: number,
  card?: VocabCard | null,
): WordRect[] {
  const availWidth = containerWidth - PADDING_X * 2
  const prepared = prepareWithSegments(text, FONT)

  if (!card) {
    // Fast path: uniform width for all lines
    const result = layoutWithLines(prepared, availWidth, LINE_HEIGHT)
    const rects: WordRect[] = []
    result.lines.forEach((line, lineIndex) => {
      const lineY = lineIndex * LINE_HEIGHT
      rects.push(...extractWordsFromLine(line.text, PADDING_X, lineIndex, lineY))
    })
    return rects
  }

  // Obstacle path: per-line variable width via layoutNextLine
  const rects: WordRect[] = []
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  let lineIndex = 0
  const cardRight = containerWidth - PADDING_X  // card is flush right
  const cardLeft  = cardRight - card.width

  while (true) {
    const lineY = lineIndex * LINE_HEIGHT

    // Does this line's vertical range overlap the card?
    const overlapsCard =
      lineY < card.y + card.height && lineY + LINE_HEIGHT > card.y

    const maxWidth = overlapsCard ? cardLeft - PADDING_X : availWidth
    const startX   = PADDING_X

    const line = layoutNextLine(prepared, cursor, Math.max(maxWidth, 60))
    if (!line) break

    rects.push(...extractWordsFromLine(line.text, startX, lineIndex, lineY))
    cursor = line.end
    lineIndex++
  }

  return rects
}

/**
 * Total text height for the given container width (used to size the canvas).
 */
export function computeTextHeight(
  text: string,
  containerWidth: number,
  card?: VocabCard | null,
): number {
  if (!card) {
    const prepared = prepareWithSegments(text, FONT)
    const { lineCount } = layoutWithLines(prepared, containerWidth - PADDING_X * 2, LINE_HEIGHT)
    return lineCount * LINE_HEIGHT + LINE_HEIGHT // bottom padding
  }
  // With obstacle: rough estimate (card shrinks some lines → more lines overall)
  const prepared = prepareWithSegments(text, FONT)
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  let lineCount = 0
  const cardRight = containerWidth - PADDING_X
  while (true) {
    const lineY = lineCount * LINE_HEIGHT
    const overlaps = lineY < card.y + card.height && lineY + LINE_HEIGHT > card.y
    const maxWidth = overlaps ? cardRight - card.width - PADDING_X : containerWidth - PADDING_X * 2
    const line = layoutNextLine(prepared, cursor, Math.max(maxWidth, 60))
    if (!line) break
    cursor = line.end
    lineCount++
  }
  return lineCount * LINE_HEIGHT + LINE_HEIGHT
}
