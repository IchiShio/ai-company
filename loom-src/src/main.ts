import './style.css'
import { PRESETS } from './presets'
import { WaveSystem } from './wave-system'
import { LoomRenderer } from './renderer'
import { computeLayout, computeWavyLayout, LINE_HEIGHT, PADDING } from './text-engine'
import type { WordRect, FloatingPhrase, LoomMode, TextPreset } from './types'

// ── DOM refs ────────────────────────────────────────────────
const canvasEl     = document.getElementById('loom-canvas') as HTMLCanvasElement
const settingsBtn  = document.getElementById('settings-btn')!
const fsBtn        = document.getElementById('fs-btn')!
const settingsPanel= document.getElementById('settings-panel')!
const modeRadios   = document.querySelectorAll<HTMLInputElement>('input[name="mode"]')
const speedSlider  = document.getElementById('speed-slider') as HTMLInputElement
const fontSlider   = document.getElementById('font-slider') as HTMLInputElement
const presetSelect = document.getElementById('preset-select') as HTMLSelectElement
const pasteBtn     = document.getElementById('paste-btn')!
const timerEl      = document.getElementById('timer')!

// ── State ───────────────────────────────────────────────────
const wave     = new WaveSystem()
const renderer = new LoomRenderer(canvasEl)
let raf        = 0
let time       = 0
let scrollY    = 0
let startTime  = Date.now()

let mode: LoomMode        = 'breathing'
let speed                 = 0.5
let fontSize              = 19
let currentPreset: TextPreset = PRESETS[0]
let customText: string | null = null

let wordRects: WordRect[]         = []
let floatingPhrases: FloatingPhrase[] = []
let totalTextHeight               = 0
let settingsOpen                  = false

// ── Init ────────────────────────────────────────────────────
function init(): void {
  populatePresets()
  setupEvents()
  resizeCanvas()
  loadText(currentPreset.text, currentPreset.phrases)
  startLoop()
}

function populatePresets(): void {
  for (const p of PRESETS) {
    const opt = document.createElement('option')
    opt.value = p.id
    opt.textContent = p.title + ' — ' + p.titleJa
    presetSelect.appendChild(opt)
  }
}

function loadText(text: string, phrases: string[]): void {
  const w = canvasEl.clientWidth || window.innerWidth
  const result = computeLayout(text, w, fontSize)
  wordRects = result.rects
  totalTextHeight = result.lineCount * LINE_HEIGHT + PADDING * 2
  scrollY = -window.innerHeight / 3

  // Initialize floating phrases
  floatingPhrases = phrases.map((p, i) => ({
    text: p,
    x: -300 - i * 200,
    y: 100 + i * (window.innerHeight / (phrases.length + 1)),
    alpha: 0,
    speed: 8 + Math.random() * 4,
    fontSize: fontSize + 2 + Math.floor(Math.random() * 4),
  }))
}

// ── Canvas sizing ───────────────────────────────────────────
function resizeCanvas(): void {
  const w = window.innerWidth
  const h = window.innerHeight
  renderer.resize(w, h)
}

// ── Events ──────────────────────────────────────────────────
function setupEvents(): void {
  window.addEventListener('resize', () => {
    resizeCanvas()
    recomputeLayout()
  })

  // Mouse proximity ripple
  canvasEl.addEventListener('mousemove', e => {
    wave.addRipple(e.clientX, e.clientY + scrollY)
  })

  canvasEl.addEventListener('touchmove', e => {
    const t = e.touches[0]
    wave.addRipple(t.clientX, t.clientY + scrollY)
  }, { passive: true })

  // Long press to pause (mobile)
  let longPress = 0
  canvasEl.addEventListener('touchstart', () => {
    longPress = window.setTimeout(() => {
      cancelAnimationFrame(raf)
      canvasEl.style.opacity = '0.5'
    }, 800)
  }, { passive: true })
  canvasEl.addEventListener('touchend', () => {
    clearTimeout(longPress)
    if (canvasEl.style.opacity === '0.5') {
      canvasEl.style.opacity = '1'
      startLoop()
    }
  }, { passive: true })

  // Settings toggle
  settingsBtn.addEventListener('click', () => {
    settingsOpen = !settingsOpen
    settingsPanel.classList.toggle('open', settingsOpen)
  })

  // Fullscreen
  fsBtn.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  })

  // Mode
  modeRadios.forEach(r => r.addEventListener('change', () => {
    mode = r.value as LoomMode
  }))

  // Speed
  speedSlider.addEventListener('input', () => {
    speed = parseFloat(speedSlider.value)
  })

  // Font size
  fontSlider.addEventListener('input', () => {
    fontSize = parseInt(fontSlider.value)
    recomputeLayout()
  })

  // Preset
  presetSelect.addEventListener('change', () => {
    const p = PRESETS.find(pr => pr.id === presetSelect.value)
    if (p) {
      currentPreset = p
      customText = null
      loadText(p.text, p.phrases)
    }
  })

  // Paste
  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text.trim()) {
        customText = text.trim()
        loadText(customText, extractPhrases(customText))
      }
    } catch {
      const text = prompt('Paste your English text:')
      if (text?.trim()) {
        customText = text.trim()
        loadText(customText, extractPhrases(customText))
      }
    }
  })

  // Tab visibility: pause when hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(raf)
    } else {
      startLoop()
    }
  })
}

function extractPhrases(text: string): string[] {
  // Simple heuristic: pick a few multi-word segments
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20)
  const phrases: string[] = []
  for (const s of sentences.slice(0, 5)) {
    const words = s.trim().split(/\s+/)
    if (words.length >= 4) {
      const start = Math.floor(Math.random() * Math.max(1, words.length - 4))
      phrases.push(words.slice(start, start + 3 + Math.floor(Math.random() * 2)).join(' '))
    }
  }
  return phrases
}

function recomputeLayout(): void {
  const text = customText ?? currentPreset.text
  const w = canvasEl.clientWidth || window.innerWidth
  const offsets = wave.getLineWidthOffsets(100)
  const result = computeWavyLayout(text, w, offsets, fontSize)
  wordRects = result.rects
  totalTextHeight = result.lineCount * LINE_HEIGHT + PADDING * 2
}

// ── Render loop ─────────────────────────────────────────────
function startLoop(): void {
  cancelAnimationFrame(raf)
  const loop = () => {
    const dt = (1 / 60) * speed
    time += dt
    wave.update(dt)

    // Slow auto-scroll
    const maxScroll = totalTextHeight - window.innerHeight + 100
    if (scrollY < maxScroll) {
      scrollY += dt * 8
    } else {
      // Loop back
      scrollY = -window.innerHeight / 3
    }

    // Recompute layout with wave
    recomputeLayout()

    // Apply mode-specific offsets to word rects
    for (const wr of wordRects) {
      const centerX = wr.x + wr.width / 2
      const centerY = wr.y + LINE_HEIGHT / 2
      const ripple = wave.getRippleOffset(centerX, centerY)

      if (mode === 'drift') {
        const drift = wave.getDriftOffset(wr.lineIndex)
        wr.offsetX = drift.dx + ripple.dx
        wr.offsetY = drift.dy + ripple.dy
      } else if (mode === 'breathing') {
        const breath = wave.getBreathingOffset(wr.lineIndex)
        wr.offsetX = ripple.dx
        wr.offsetY = breath + ripple.dy
      } else if (mode === 'night') {
        wr.alpha = wave.getNightAlpha(wr.lineIndex)
        wr.offsetX = ripple.dx * 0.3
        wr.offsetY = ripple.dy * 0.3
      } else {
        wr.offsetX = ripple.dx
        wr.offsetY = ripple.dy
      }
    }

    // Update floating phrases
    const w = canvasEl.clientWidth || window.innerWidth
    for (const fp of floatingPhrases) {
      fp.x += fp.speed * dt
      if (fp.x > w + 100) {
        fp.x = -400
        fp.y = 80 + Math.random() * (window.innerHeight - 160)
      }
      // Fade in/out at edges
      if (fp.x < 0) {
        fp.alpha = Math.max(0, (fp.x + 300) / 300)
      } else if (fp.x > w - 300) {
        fp.alpha = Math.max(0, (w - fp.x) / 300)
      } else {
        fp.alpha = Math.min(fp.alpha + dt * 0.5, 1)
      }
    }

    renderer.render(wordRects, floatingPhrases, mode, fontSize, time, scrollY)

    // Timer
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const min = Math.floor(elapsed / 60)
    const sec = elapsed % 60
    timerEl.textContent = min + ':' + sec.toString().padStart(2, '0')

    raf = requestAnimationFrame(loop)
  }
  raf = requestAnimationFrame(loop)
}

// ── Go ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init)
