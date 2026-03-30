import { FONT, LINE_HEIGHT } from './text-engine'
import type { WordRect, Particle } from './types'

const C = {
  bg:          '#0f1117',
  bgGrad1:     '#0f1117',
  bgGrad2:     '#1a1d2e',
  text:        '#c8cce0',
  textHighlight: '#ffffff',
  textDim:     '#5a5f7a',
  particleBg:  'rgba(255,255,255,0.08)',
  tooltipBg:   '#1e2233',
  tooltipBorder: '#2e3450',
}

export class ThoughtWeaveRenderer {
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
    particles: Particle[],
    hoveredWordIdx: number,
    selectedParticle: Particle | null,
    time: number,
  ): void {
    const ctx = this.ctx
    const cssW = this.canvas.width / this.dpr
    const cssH = this.canvas.height / this.dpr

    // 1. Background gradient
    const grad = ctx.createLinearGradient(0, 0, 0, cssH)
    grad.addColorStop(0, C.bgGrad1)
    grad.addColorStop(1, C.bgGrad2)
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, cssW, cssH)

    // 2. Particle influence radius (subtle glow)
    for (const p of particles) {
      const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.influenceRadius)
      gradient.addColorStop(0, hexToRgba(p.color, 0.12))
      gradient.addColorStop(0.6, hexToRgba(p.color, 0.04))
      gradient.addColorStop(1, 'transparent')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.influenceRadius, 0, Math.PI * 2)
      ctx.fill()
    }

    // 3. Text
    const baseline = LINE_HEIGHT * 0.72
    ctx.font = FONT
    ctx.textBaseline = 'alphabetic'

    for (let i = 0; i < wordRects.length; i++) {
      const wr = wordRects[i]
      if (i === hoveredWordIdx) {
        ctx.fillStyle = '#ffffff'
        // Underline
        ctx.fillRect(wr.x, wr.y + LINE_HEIGHT - 4, wr.width, 2)
      } else if (wr.highlighted && wr.particleType) {
        // Get color from matching particle
        const matchP = particles.find(p => p.type === wr.particleType)
        ctx.fillStyle = matchP ? matchP.color : C.textHighlight
      } else {
        ctx.fillStyle = C.text
      }
      ctx.fillText(wr.rawWord, wr.x, wr.y + baseline)
    }

    // 4. Particles
    for (const p of particles) {
      const pulse = 1 + Math.sin(time * 2 + p.id) * 0.05
      const r = p.radius * pulse

      // Outer ring
      ctx.beginPath()
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2)
      ctx.fillStyle = hexToRgba(p.color, 0.2)
      ctx.fill()
      ctx.strokeStyle = hexToRgba(p.color, 0.6)
      ctx.lineWidth = 2
      ctx.stroke()

      // Inner circle
      ctx.beginPath()
      ctx.arc(p.x, p.y, r * 0.6, 0, Math.PI * 2)
      ctx.fillStyle = hexToRgba(p.color, 0.4)
      ctx.fill()

      // Label
      ctx.fillStyle = '#ffffff'
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(p.label, p.x, p.y)
      ctx.textAlign = 'start'
      ctx.textBaseline = 'alphabetic'
      ctx.font = FONT
    }

    // 5. Selected particle tooltip
    if (selectedParticle) {
      this.drawTooltip(ctx, selectedParticle, cssW)
    }
  }

  private drawTooltip(ctx: CanvasRenderingContext2D, p: Particle, canvasW: number): void {
    const maxW = 260
    const pad = 12
    const tipX = Math.min(p.x + p.radius + 12, canvasW - maxW - 20)
    const tipY = Math.max(p.y - 40, 10)

    // Measure text for height
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    const lines = wrapText(ctx, p.explanation, maxW - pad * 2)
    const h = pad * 2 + 20 + lines.length * 18

    // Background
    ctx.fillStyle = C.tooltipBg
    roundRect(ctx, tipX, tipY, maxW, h, 8)
    ctx.fill()
    ctx.strokeStyle = C.tooltipBorder
    ctx.lineWidth = 1
    roundRect(ctx, tipX, tipY, maxW, h, 8)
    ctx.stroke()

    // Title
    ctx.fillStyle = p.color
    ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    ctx.fillText(p.label, tipX + pad, tipY + pad + 12)

    // Body
    ctx.fillStyle = '#c8cce0'
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    let ly = tipY + pad + 32
    for (const line of lines) {
      ctx.fillText(line, tipX + pad, ly)
      ly += 18
    }

    ctx.font = FONT
  }
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
): void {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y, x + w, y + r, r)
  ctx.lineTo(x + w, y + h - r)
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h)
  ctx.arcTo(x, y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r)
  ctx.arcTo(x, y, x + r, y, r)
  ctx.closePath()
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxW: number): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let line = ''
  for (const word of words) {
    const test = line ? line + ' ' + word : word
    if (ctx.measureText(test).width > maxW && line) {
      lines.push(line)
      line = word
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  return lines
}
