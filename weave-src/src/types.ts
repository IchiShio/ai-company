export type ParticleType = 'idea' | 'connector' | 'nuance' | 'cultural'
export type AppMode = 'guided' | 'freeflow' | 'replay'

export interface Particle {
  id: number
  type: ParticleType
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  label: string
  explanation: string
  color: string
  alpha: number
  influenceRadius: number
}

export interface WordRect {
  rawWord: string
  x: number
  y: number
  width: number
  height: number
  lineIndex: number
  highlighted: boolean
  particleType: ParticleType | null
}

export interface Obstacle {
  x: number
  y: number
  width: number
  height: number
}

export interface ThoughtScenario {
  id: string
  title: string
  titleJa: string
  text: string
  particles: ParticleInit[]
  wordNotes: Record<string, string>
}

export interface ParticleInit {
  type: ParticleType
  label: string
  explanation: string
  relX: number  // 0-1 relative to canvas width
  relY: number  // 0-1 relative to canvas height
}
