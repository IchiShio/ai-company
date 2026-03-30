import type { WaveRipple } from './types'

export class WaveSystem {
  private ripples: WaveRipple[] = []
  private time = 0

  update(dt: number): void {
    this.time += dt
    // Decay ripples
    this.ripples = this.ripples.filter(r => {
      r.radius += dt * 40
      r.strength *= 0.97
      return r.strength > 0.01
    })
  }

  addRipple(x: number, y: number): void {
    if (this.ripples.length > 5) return
    this.ripples.push({ x, y, radius: 0, strength: 0.4, born: this.time })
  }

  /** Breathing mode: gentle vertical oscillation per line */
  getBreathingOffset(lineIndex: number): number {
    return Math.sin(this.time * 0.4 + lineIndex * 0.15) * 2.5
  }

  /** Drift mode: slow horizontal wave per line */
  getDriftOffset(lineIndex: number): { dx: number; dy: number } {
    return {
      dx: Math.sin(this.time * 0.2 + lineIndex * 0.35) * 5,
      dy: Math.cos(this.time * 0.15 + lineIndex * 0.25) * 1.5,
    }
  }

  /** Night mode: very subtle slow pulse */
  getNightAlpha(lineIndex: number): number {
    const base = 0.6
    const wave = Math.sin(this.time * 0.1 + lineIndex * 0.08) * 0.15
    return base + wave
  }

  /** Get ripple displacement at a given point */
  getRippleOffset(x: number, y: number): { dx: number; dy: number } {
    let dx = 0
    let dy = 0
    for (const r of this.ripples) {
      const dist = Math.sqrt((x - r.x) ** 2 + (y - r.y) ** 2)
      if (dist < r.radius + 50 && dist > r.radius - 50) {
        const angle = Math.atan2(y - r.y, x - r.x)
        const wave = Math.sin((dist - r.radius) * 0.1) * r.strength * 3
        dx += Math.cos(angle) * wave
        dy += Math.sin(angle) * wave
      }
    }
    return { dx, dy }
  }

  /**
   * Compute per-line width offsets for Pretext layout.
   * Returns small values (±3px) to create subtle wavy text.
   */
  getLineWidthOffsets(lineCount: number): number[] {
    const offsets: number[] = []
    for (let i = 0; i < lineCount; i++) {
      offsets.push(Math.sin(this.time * 0.3 + i * 0.4) * 3)
    }
    return offsets
  }

  getTime(): number {
    return this.time
  }
}
