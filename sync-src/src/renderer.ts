import { FONT, LINE_HEIGHT } from './text-engine'
import type { WordRect, VocabCard } from './types'

const C = {
  upcoming : '#8892b8',
  active   : '#ffffff',
  done     : '#363c57',
  hlFill   : 'rgba(245, 200, 66, 0.20)',
  hlStroke : 'rgba(245, 200, 66, 0.60)',
  cardBg   : '#1a1d27',
  cardBorder: '#2e3347',
  cardTitle : '#f5c842',
  cardPhon  : '#7b82a0',
  cardDef   : '#c8cce0',
}

export class Renderer {
  readonly canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private dpr = window.devicePixelRatio || 1

  // Smooth highlight interpolation state
  private hlX = 0
  private hlY = 0
  private hlW = 0
  private hlSnapped = false   // skip interpolation on first render / word jump

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    this.ctx    = canvas.getContext('2d')!
  }

  resize(cssW: number, cssH: number): void {
    const dpr = this.dpr
    this.canvas.width        = cssW * dpr
    this.canvas.height       = cssH * dpr
    this.canvas.style.width  = cssW + 'px'
    this.canvas.style.height = cssH + 'px'
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  render(
    wordRects   : WordRect[],
    activeIndex : number,
    card        : VocabCard | null,
  ): void {
    const ctx  = this.ctx
    const cssW = this.canvas.width  / this.dpr
    const cssH = this.canvas.height / this.dpr

    ctx.clearRect(0, 0, cssW, cssH)
    ctx.font         = FONT
    ctx.textBaseline = 'alphabetic'

    // ── 1. Highlight pill ────────────────────────────────────────────
    if (activeIndex >= 0 && activeIndex < wordRects.length) {
      const wr  = wordRects[activeIndex]
      const px  = 6, py = 3
      const tx  = wr.x - px
      const ty  = wr.y + py
      const tw  = wr.width + px * 2
      const th  = LINE_HEIGHT - py * 2

      if (!this.hlSnapped) {
        this.hlX = tx; this.hlY = ty; this.hlW = tw
        this.hlSnapped = true
      } else {
        // Smooth lerp toward target
        this.hlX += (tx - this.hlX) * 0.35
        this.hlY += (ty - this.hlY) * 0.35
        this.hlW += (tw - this.hlW) * 0.35
      }

      ctx.fillStyle = C.hlFill
      roundRect(ctx, this.hlX, this.hlY, this.hlW, th, 6)
      ctx.fill()

      ctx.strokeStyle = C.hlStroke
      ctx.lineWidth   = 1
      roundRect(ctx, this.hlX, this.hlY, this.hlW, th, 6)
      ctx.stroke()
    }

    // ── 2. Words ─────────────────────────────────────────────────────
    const baseline = LINE_HEIGHT * 0.73   // offset from rect top to text baseline

    for (let i = 0; i < wordRects.length; i++) {
      const wr = wordRects[i]
      ctx.fillStyle =
        i < activeIndex  ? C.done     :
        i === activeIndex ? C.active  :
        C.upcoming
      ctx.fillText(wr.rawWord, wr.x, wr.y + baseline)
    }

    // ── 3. Vocab card overlay ─────────────────────────────────────────
    if (card) {
      drawVocabCard(ctx, card)
    }
  }

  /** Snap highlight to new word immediately (call on word tap, seek, passage change) */
  resetHighlight(): void {
    this.hlSnapped = false
  }
}

// ─── helpers ──────────────────────────────────────────────────────────────────

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
): void {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y,     x + w, y + r,   r)
  ctx.lineTo(x + w, y + h - r)
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h)
  ctx.arcTo(x,  y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r)
  ctx.arcTo(x,  y,     x + r, y, r)
  ctx.closePath()
}

function drawVocabCard(ctx: CanvasRenderingContext2D, card: VocabCard): void {
  const { x, y, width: w, height: h } = card
  const r = 10

  // Shadow
  ctx.shadowColor   = 'rgba(0,0,0,0.4)'
  ctx.shadowBlur    = 12
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 4

  // Background
  ctx.fillStyle = C.cardBg
  roundRect(ctx, x, y, w, h, r)
  ctx.fill()

  ctx.shadowColor = 'transparent'
  ctx.shadowBlur  = 0

  // Border
  ctx.strokeStyle = C.cardBorder
  ctx.lineWidth   = 1
  roundRect(ctx, x, y, w, h, r)
  ctx.stroke()

  // Content
  const pad = 12
  let ty = y + pad + 14

  ctx.fillStyle = C.cardTitle
  ctx.font      = `600 14px ${FONT.split('px')[1] ?? 'sans-serif'}`
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(card.word, x + pad, ty)
  ty += 4

  if (card.phonetic) {
    ctx.fillStyle = C.cardPhon
    ctx.font      = `12px ${FONT.split('px')[1] ?? 'sans-serif'}`
    ty += 16
    ctx.fillText(card.phonetic, x + pad, ty)
  }

  ty += 18
  ctx.fillStyle = C.cardDef
  ctx.font      = `13px ${FONT.split('px')[1] ?? 'sans-serif'}`
  // Wrap definition text
  wrapText(ctx, card.partOfSpeech ? `${card.partOfSpeech}. ${card.definition}` : card.definition, x + pad, ty, w - pad * 2, 18)
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number, y: number,
  maxW: number, lineH: number,
): void {
  const words = text.split(' ')
  let line = ''
  for (const word of words) {
    const test = line ? line + ' ' + word : word
    if (ctx.measureText(test).width > maxW && line) {
      ctx.fillText(line, x, y)
      line = word
      y   += lineH
    } else {
      line = test
    }
  }
  if (line) ctx.fillText(line, x, y)
}
