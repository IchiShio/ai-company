import './style.css'
import { SCENARIOS } from './thought-data'
import { ParticleSystem } from './particles'
import { ThoughtWeaveRenderer } from './renderer'
import { computeLayout, LINE_HEIGHT } from './text-engine'
import type { WordRect, Particle, ParticleType, ThoughtScenario } from './types'

// ── DOM refs ────────────────────────────────────────────────
const canvasEl    = document.getElementById('tw-canvas') as HTMLCanvasElement
const canvasWrap  = document.getElementById('canvas-wrap')!
const scenarioSel = document.getElementById('scenario-select') as HTMLSelectElement
const notePanel   = document.getElementById('note-panel')!
const footerInfo  = document.getElementById('footer-info')!

// ── State ───────────────────────────────────────────────────
const ps       = new ParticleSystem()
const renderer = new ThoughtWeaveRenderer(canvasEl)
let raf        = 0
let time       = 0

let currentScenario: ThoughtScenario = SCENARIOS[0]
let wordRects: WordRect[] = []
let hoveredWordIdx = -1
let selectedParticle: Particle | null = null

// ── Init ────────────────────────────────────────────────────
function init(): void {
  populateScenarioSelect()
  setupEvents()
  loadScenario(currentScenario)
  startLoop()
}

function populateScenarioSelect(): void {
  for (const s of SCENARIOS) {
    const opt = document.createElement('option')
    opt.value = s.id
    opt.textContent = s.title + ' — ' + s.titleJa
    scenarioSel.appendChild(opt)
  }
  scenarioSel.addEventListener('change', () => {
    const s = SCENARIOS.find(sc => sc.id === scenarioSel.value)
    if (s) {
      currentScenario = s
      loadScenario(s)
    }
  })
}

function loadScenario(s: ThoughtScenario): void {
  const w = canvasWrap.clientWidth || 700
  const h = canvasWrap.clientHeight || 500
  ps.setBounds(w, h)
  ps.loadFromInits(s.particles, w, h)
  selectedParticle = null
  hoveredWordIdx = -1
  resizeCanvas()
  renderNotes(s)
  footerInfo.textContent = `${s.particles.length} particles — click words for notes, drag particles to reshape text`
}

function renderNotes(s: ThoughtScenario): void {
  notePanel.innerHTML = ''
  const entries = Object.entries(s.wordNotes)
  if (entries.length === 0) {
    notePanel.innerHTML = '<div class="empty-note">Click a word for notes</div>'
    return
  }
  for (const [word, note] of entries) {
    const div = document.createElement('div')
    div.className = 'word-note'
    div.innerHTML = `<div class="word">${word}</div><div class="note">${note}</div>`
    notePanel.appendChild(div)
  }
}

// ── Canvas sizing ───────────────────────────────────────────
function resizeCanvas(): void {
  const w = canvasWrap.clientWidth || 700
  const h = canvasWrap.clientHeight || 500
  renderer.resize(w, h)
  ps.setBounds(w, h)
  recomputeLayout()
}

function recomputeLayout(): void {
  const w = canvasWrap.clientWidth || 700
  const obstacles = ps.toObstacles()
  wordRects = computeLayout(currentScenario.text, w, obstacles)
  markInfluencedWords()
}

function markInfluencedWords(): void {
  for (const wr of wordRects) {
    wr.highlighted = false
    wr.particleType = null
    const wx = wr.x + wr.width / 2
    const wy = wr.y + LINE_HEIGHT / 2
    for (const p of ps.particles) {
      const dx = wx - p.x
      const dy = wy - p.y
      if (dx * dx + dy * dy < p.influenceRadius * p.influenceRadius) {
        wr.highlighted = true
        wr.particleType = p.type
        break
      }
    }
  }
}

// ── Events ──────────────────────────────────────────────────
function setupEvents(): void {
  window.addEventListener('resize', resizeCanvas)

  // Mouse events on canvas
  canvasEl.addEventListener('mousedown', onPointerDown)
  canvasEl.addEventListener('mousemove', onPointerMove)
  canvasEl.addEventListener('mouseup', onPointerUp)
  canvasEl.addEventListener('mouseleave', onPointerUp)

  // Touch events
  canvasEl.addEventListener('touchstart', e => {
    e.preventDefault()
    const t = e.touches[0]
    onPointerDown(toMouseEvent(t))
  }, { passive: false })
  canvasEl.addEventListener('touchmove', e => {
    e.preventDefault()
    const t = e.touches[0]
    onPointerMove(toMouseEvent(t))
  }, { passive: false })
  canvasEl.addEventListener('touchend', e => {
    e.preventDefault()
    onPointerUp()
  }, { passive: false })

  // Particle buttons
  document.querySelectorAll<HTMLElement>('.particle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.type as ParticleType
      const w = canvasWrap.clientWidth || 700
      const h = canvasWrap.clientHeight || 500
      ps.add(type, w / 2 + Math.random() * 60 - 30, h / 2 + Math.random() * 60 - 30, type, `Custom ${type} particle`)
    })
  })
}

function toMouseEvent(t: Touch): MouseEvent {
  return { clientX: t.clientX, clientY: t.clientY } as MouseEvent
}

function getCanvasPos(e: MouseEvent): { x: number; y: number } {
  const rect = canvasEl.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function onPointerDown(e: MouseEvent): void {
  const { x, y } = getCanvasPos(e)
  const dragId = ps.startDrag(x, y)
  if (dragId !== null) {
    canvasEl.classList.add('dragging')
    selectedParticle = ps.particles.find(p => p.id === dragId) ?? null
    return
  }

  // Check word hit
  const wordIdx = hitTestWord(x, y)
  if (wordIdx >= 0) {
    const word = wordRects[wordIdx].rawWord.replace(/[^a-zA-Z']/g, '')
    const note = currentScenario.wordNotes[word]
    if (note) {
      highlightNoteInPanel(word)
    }
  }
}

function onPointerMove(e: MouseEvent): void {
  const { x, y } = getCanvasPos(e)
  if (ps.isDragging()) {
    ps.moveDrag(x, y)
    return
  }
  // Hover detection
  hoveredWordIdx = hitTestWord(x, y)
  canvasEl.style.cursor = hoveredWordIdx >= 0 ? 'pointer' : 'default'
}

function onPointerUp(): void {
  if (ps.isDragging()) {
    ps.endDrag()
    canvasEl.classList.remove('dragging')
  }
}

function hitTestWord(mx: number, my: number): number {
  for (let i = 0; i < wordRects.length; i++) {
    const w = wordRects[i]
    if (mx >= w.x - 2 && mx <= w.x + w.width + 2 && my >= w.y && my <= w.y + w.height) {
      return i
    }
  }
  return -1
}

function highlightNoteInPanel(word: string): void {
  const notes = notePanel.querySelectorAll('.word-note')
  notes.forEach(n => {
    const w = n.querySelector('.word')?.textContent
    if (w === word) {
      n.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      ;(n as HTMLElement).style.background = 'var(--surface2)'
      setTimeout(() => { (n as HTMLElement).style.background = '' }, 1500)
    }
  })
}

// ── Render loop ─────────────────────────────────────────────
function startLoop(): void {
  cancelAnimationFrame(raf)
  const loop = () => {
    time += 1 / 60
    ps.update(1)
    recomputeLayout()
    renderer.render(wordRects, ps.particles, hoveredWordIdx, selectedParticle, time)
    raf = requestAnimationFrame(loop)
  }
  raf = requestAnimationFrame(loop)
}

// ── Go ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init)
