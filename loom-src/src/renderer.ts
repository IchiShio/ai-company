import { getFont, LINE_HEIGHT } from './text-engine'
import type { WordRect, FloatingPhrase, LoomMode } from './types'

interface ModeColors {
  bgGrad1: string
  bgGrad2: string
  text: string
  accent: string
  phraseBg: string
}

const MODE_COLORS: Record<LoomMode, ModeColors> = {
  drift: {
    bgGrad1: '#0a0e1a',
    bgGrad2: '#141b2d',
    text: '#b0b8d0',
    accent: '#7eb8da',
    phraseBg: 'rgba(126, 184, 218, 0.06)',
  },
  breathing: {
    bgGrad1: '#0d1117',
    bgGrad2: '#161d2b',
    text: '#c0c8de',
    accent: '#a8c4e0',
    phraseBg: 'rgba(168, 196, 224, 0.06)',
  },
  night: {
    bgGrad1: '#060810',
    bgGrad2: '#0c0f1a',
    text: '#6a7090',
    accent: '#4a5578',
    phraseBg: 'rgba(74, 85, 120, 0.05)',
  },
  custom: {
    bgGrad1: '#0f1117',
    bgGrad2: '#1a1d2e',
    text: '#c8cce0',
    accent: '#8892b8',
    phraseBg: 'rgba(136, 146, 184, 0.06)',
  },
}

export class LoomRenderer {
  readonly canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private dpr = window.devicePixelRatio || 1

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')!
  }

  resize(cssW: number, cssH: number): void {
    const dpr = this.dpr
    this.canvas.width = cssW * dpr
    this.canvas.height = cssH * dpr
    this.canvas.style.width = cssW + 'px'
    this.canvas.style.height = cssH + 'px'
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  render(
    wordRects: WordRect[],
    floatingPhrases: FloatingPhrase[],
    mode: LoomMode,
    fontSize: number,
    time: number,
    scrollY: number,
  ): void {
    const ctx = this.ctx
    const cssW = this.canvas.width / this.dpr
    const cssH = this.canvas.height / this.dpr
    const colors = MODE_COLORS[mode]
    const font = getFont(fontSize)

    // 1. Background gradient
    const grad = ctx.createLinearGradient(0, 0, 0, cssH)
    grad.addColorStop(0, colors.bgGrad1)
    grad.addColorStop(1, colors.bgGrad2)
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, cssW, cssH)

    // 2. Main text
    const baseline = LINE_HEIGHT * 0.72
    ctx.font = font
    ctx.textBaseline = 'alphabetic'

    for (const wr of wordRects) {
      const renderY = wr.y + wr.offsetY - scrollY
      if (renderY + LINE_HEIGHT < -20 || renderY > cssH + 20) continue

      const renderX = wr.x + wr.offsetX

      // Subtle per-word alpha variation
      const wordPhase = Math.sin(time * 0.3 + wr.lineIndex * 0.12 + wr.x * 0.005)
      const alphaVar = mode === 'night' ? wordPhase * 0.1 : wordPhase * 0.05
      const alpha = Math.max(0.1, Math.min(1, wr.alpha + alphaVar))

      ctx.globalAlpha = alpha
      ctx.fillStyle = colors.text
      ctx.fillText(wr.rawWord, renderX, renderY + baseline)
    }

    // 3. Floating phrases
    ctx.globalAlpha = 1
    for (const fp of floatingPhrases) {
      if (fp.alpha < 0.01) continue
      ctx.globalAlpha = fp.alpha * 0.5
      ctx.font = `italic ${fp.fontSize}px Georgia, "Noto Serif", serif`
      ctx.fillStyle = colors.accent

      // Gentle glow
      ctx.shadowColor = colors.accent
      ctx.shadowBlur = 12
      ctx.fillText(fp.text, fp.x, fp.y)
      ctx.shadowBlur = 0
    }

    ctx.globalAlpha = 1
    ctx.font = font

    // 4. Subtle vignette effect
    const vignette = ctx.createRadialGradient(
      cssW / 2, cssH / 2, cssH * 0.3,
      cssW / 2, cssH / 2, cssH * 0.8,
    )
    vignette.addColorStop(0, 'transparent')
    vignette.addColorStop(1, mode === 'night' ? 'rgba(0,0,0,0.4)' : 'rgba(0,0,0,0.2)')
    ctx.fillStyle = vignette
    ctx.fillRect(0, 0, cssW, cssH)
  }
}
