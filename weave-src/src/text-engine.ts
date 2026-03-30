import { prepareWithSegments, layoutNextLine } from '@chenglou/pretext'
import type { WordRect, Obstacle } from './types'

export const FONT = '18px Georgia, "Noto Serif", "Hiragino Mincho ProN", serif'
export const LINE_HEIGHT = 34
export const PADDING = 32

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
      rects.push({
        rawWord: part,
        x, y: lineY,
        width: w, height: LINE_HEIGHT,
        lineIndex,
        highlighted: false,
        particleType: null,
      })
    }
    x += w
  }
  return rects
}

/**
 * Layout text around multiple particle obstacles.
 * Each obstacle reduces available width for lines that overlap it vertically.
 * Obstacles on the left side shift the start position; obstacles on the right reduce width.
 */
export function computeLayout(
  text: string,
  containerWidth: number,
  obstacles: Obstacle[],
): WordRect[] {
  const prepared = prepareWithSegments(text, FONT)
  const rects: WordRect[] = []
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  let lineIndex = 0

  while (true) {
    const lineY = lineIndex * LINE_HEIGHT

    // Calculate available width based on overlapping obstacles
    let leftEdge = PADDING
    let rightEdge = containerWidth - PADDING

    for (const obs of obstacles) {
      const obsTop = obs.y
      const obsBot = obs.y + obs.height
      if (lineY + LINE_HEIGHT <= obsTop || lineY >= obsBot) continue

      const obsCenterX = obs.x + obs.width / 2
      if (obsCenterX < containerWidth / 2) {
        // Obstacle on left side: push left edge right
        leftEdge = Math.max(leftEdge, obs.x + obs.width + 8)
      } else {
        // Obstacle on right side: pull right edge left
        rightEdge = Math.min(rightEdge, obs.x - 8)
      }
    }

    const maxWidth = Math.max(rightEdge - leftEdge, 80)
    const line = layoutNextLine(prepared, cursor, maxWidth)
    if (!line) break

    rects.push(...extractWordsFromLine(line.text, leftEdge, lineIndex, lineY))
    cursor = line.end
    lineIndex++

    // Safety: prevent infinite loop for extremely long text
    if (lineIndex > 500) break
  }

  return rects
}

/**
 * Compute total text height for canvas sizing.
 */
export function computeTextHeight(
  text: string,
  containerWidth: number,
  obstacles: Obstacle[],
): number {
  const prepared = prepareWithSegments(text, FONT)
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  let lineCount = 0

  while (true) {
    const lineY = lineCount * LINE_HEIGHT
    let leftEdge = PADDING
    let rightEdge = containerWidth - PADDING

    for (const obs of obstacles) {
      if (lineY + LINE_HEIGHT <= obs.y || lineY >= obs.y + obs.height) continue
      const cx = obs.x + obs.width / 2
      if (cx < containerWidth / 2) {
        leftEdge = Math.max(leftEdge, obs.x + obs.width + 8)
      } else {
        rightEdge = Math.min(rightEdge, obs.x - 8)
      }
    }

    const maxWidth = Math.max(rightEdge - leftEdge, 80)
    const line = layoutNextLine(prepared, cursor, maxWidth)
    if (!line) break
    cursor = line.end
    lineCount++
    if (lineCount > 500) break
  }

  return lineCount * LINE_HEIGHT + LINE_HEIGHT
}
