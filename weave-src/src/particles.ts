import type { Particle, ParticleType, Obstacle, ParticleInit } from './types'

const PARTICLE_COLORS: Record<ParticleType, string> = {
  idea:      '#4FC3F7',
  connector: '#81C784',
  nuance:    '#FFB74D',
  cultural:  '#CE93D8',
}

const PARTICLE_RADIUS: Record<ParticleType, number> = {
  idea:      28,
  connector: 24,
  nuance:    26,
  cultural:  26,
}

const INFLUENCE_RADIUS: Record<ParticleType, number> = {
  idea:      80,
  connector: 60,
  nuance:    70,
  cultural:  70,
}

export class ParticleSystem {
  particles: Particle[] = []
  private nextId = 0
  private dragId: number | null = null
  private friction = 0.92
  private boundsW = 800
  private boundsH = 600

  setBounds(w: number, h: number): void {
    this.boundsW = w
    this.boundsH = h
  }

  add(type: ParticleType, x: number, y: number, label: string, explanation: string): Particle {
    const p: Particle = {
      id: this.nextId++,
      type,
      x, y,
      vx: 0, vy: 0,
      radius: PARTICLE_RADIUS[type],
      label,
      explanation,
      color: PARTICLE_COLORS[type],
      alpha: 1,
      influenceRadius: INFLUENCE_RADIUS[type],
    }
    this.particles.push(p)
    return p
  }

  remove(id: number): void {
    this.particles = this.particles.filter(p => p.id !== id)
  }

  clear(): void {
    this.particles = []
    this.nextId = 0
  }

  loadFromInits(inits: ParticleInit[], canvasW: number, canvasH: number): void {
    this.clear()
    for (const init of inits) {
      this.add(
        init.type,
        init.relX * canvasW,
        init.relY * canvasH,
        init.label,
        init.explanation,
      )
    }
  }

  update(dt: number): void {
    for (const p of this.particles) {
      if (p.id === this.dragId) continue
      p.vx *= this.friction
      p.vy *= this.friction
      p.x += p.vx * dt
      p.y += p.vy * dt

      // Boundary bounce
      if (p.x - p.radius < 0) { p.x = p.radius; p.vx = Math.abs(p.vx) * 0.5 }
      if (p.x + p.radius > this.boundsW) { p.x = this.boundsW - p.radius; p.vx = -Math.abs(p.vx) * 0.5 }
      if (p.y - p.radius < 0) { p.y = p.radius; p.vy = Math.abs(p.vy) * 0.5 }
      if (p.y + p.radius > this.boundsH) { p.y = this.boundsH - p.radius; p.vy = -Math.abs(p.vy) * 0.5 }
    }
  }

  toObstacles(): Obstacle[] {
    return this.particles.map(p => ({
      x: p.x - p.radius,
      y: p.y - p.radius,
      width: p.radius * 2,
      height: p.radius * 2,
    }))
  }

  /** Returns particle id if hit, null otherwise */
  startDrag(mx: number, my: number): number | null {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i]
      const dx = mx - p.x
      const dy = my - p.y
      if (dx * dx + dy * dy <= p.radius * p.radius) {
        this.dragId = p.id
        p.vx = 0
        p.vy = 0
        return p.id
      }
    }
    return null
  }

  moveDrag(mx: number, my: number): void {
    if (this.dragId === null) return
    const p = this.particles.find(pp => pp.id === this.dragId)
    if (!p) return
    p.vx = (mx - p.x) * 0.3
    p.vy = (my - p.y) * 0.3
    p.x = mx
    p.y = my
  }

  endDrag(): void {
    this.dragId = null
  }

  isDragging(): boolean {
    return this.dragId !== null
  }

  hitTest(mx: number, my: number): Particle | null {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i]
      const dx = mx - p.x
      const dy = my - p.y
      if (dx * dx + dy * dy <= p.influenceRadius * p.influenceRadius) {
        return p
      }
    }
    return null
  }
}
