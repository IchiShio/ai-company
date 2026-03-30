import './style.css'
import { PASSAGES }       from './passages'
import { AudioEngine, findWordIndex } from './audio-engine'
import { computeWordRects, computeTextHeight, LINE_HEIGHT } from './text-engine'
import { Renderer }        from './renderer'
import { fetchVocab }      from './vocab'
import type { Level, WordTiming, WordRect, VocabCard } from './types'

// ─── DOM refs ────────────────────────────────────────────────────────────────
const levelTabs   = document.querySelectorAll<HTMLElement>('.level-tab')
const listEl      = document.getElementById('passage-list')!
const listTitle   = document.getElementById('list-title')!
const canvasEl    = document.getElementById('sync-canvas') as HTMLCanvasElement
const playerPanel = document.getElementById('player-panel')!
const playBtn     = document.getElementById('play-btn')!
const speedDown   = document.getElementById('speed-down')!
const speedUp     = document.getElementById('speed-up')!
const speedLabel  = document.getElementById('speed-label')!
const progressBar = document.getElementById('progress-bar')!
const progressFill= document.getElementById('progress-fill')!
const timeCurrent = document.getElementById('time-current')!
const timeTotal   = document.getElementById('time-total')!
const loadingEl   = document.getElementById('loading')!
const passTitle   = document.getElementById('pass-title')!
const hintEl      = document.getElementById('tap-hint')!

// ─── State ────────────────────────────────────────────────────────────────────
const audio    = new AudioEngine()
let renderer   : Renderer | null = null
let raf        = 0

let currentLevel  : Level = 'lv1'
let currentIndex  = 0
let wordRects     : WordRect[]   = []
let timings       : WordTiming[] = []
let activeIndex   = -1
let card          : VocabCard | null = null
let passageLoaded = false

const SPEEDS = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4]
let speedIdx = 3

function currentSpeed() { return SPEEDS[speedIdx] }

const LEVEL_LABELS: Record<Level, string> = {
  lv1: 'Level 1', lv2: 'Level 2', lv3: 'Level 3', lv4: 'Level 4', lv5: 'Level 5',
}

// ─── Init ─────────────────────────────────────────────────────────────────────
function init() {
  renderer = new Renderer(canvasEl)
  setupLevelTabs()
  renderPassageList()
  setupTransport()
  setupCanvasEvents()
  window.addEventListener('resize', onResize)
  loadPassage(currentLevel, 0)
}

function setupLevelTabs() {
  levelTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const lv = tab.dataset.level as Level
      if (lv === currentLevel) return
      currentLevel = lv
      currentIndex = 0
      levelTabs.forEach(t => t.classList.toggle('active', t.dataset.level === lv))
      renderPassageList()
      loadPassage(currentLevel, 0)
    })
  })
}

function renderPassageList() {
  const items = PASSAGES[currentLevel]
  listTitle.textContent = LEVEL_LABELS[currentLevel] + ' — ' + items.length + '本'
  listEl.innerHTML = ''
  items.forEach((p, i) => {
    const el = document.createElement('button')
    el.className = 'passage-item' + (i === currentIndex ? ' active' : '')
    el.innerHTML =
      '<span class="pi-title">' + p.pid.replace(/_/g, ' ') + '</span>' +
      '<span class="pi-wc">' + p.wc + '語</span>'
    el.addEventListener('click', () => {
      if (i === currentIndex) return
      currentIndex = i
      document.querySelectorAll('.passage-item').forEach((e, j) =>
        e.classList.toggle('active', j === i))
      loadPassage(currentLevel, i)
    })
    listEl.appendChild(el)
  })
}

function setupTransport() {
  playBtn.addEventListener('click', togglePlay)
  speedDown.addEventListener('click', () => {
    if (speedIdx > 0) { speedIdx--; applySpeed() }
  })
  speedUp.addEventListener('click', () => {
    if (speedIdx < SPEEDS.length - 1) { speedIdx++; applySpeed() }
  })
  progressBar.addEventListener('click', e => {
    if (!passageLoaded) return
    const r = progressBar.getBoundingClientRect()
    audio.seek((e.clientX - r.left) / r.width * audio.duration)
    renderer?.resetHighlight()
  })
  window.addEventListener('keydown', e => {
    if (e.target instanceof HTMLInputElement) return
    if (e.code === 'Space')      { e.preventDefault(); togglePlay() }
    if (e.code === 'ArrowRight') audio.seek(audio.currentTime + 3)
    if (e.code === 'ArrowLeft')  audio.seek(audio.currentTime - 3)
    if (e.code === 'Escape')     dismissCard()
  })
}

function togglePlay() {
  if (!passageLoaded) return
  if (audio.isPlaying) {
    audio.pause()
    playBtn.textContent = '▶ Play'
    playBtn.classList.remove('playing')
    cancelAnimationFrame(raf)
  } else {
    audio.play(onEnded)
    playBtn.textContent = '⏸ Pause'
    playBtn.classList.add('playing')
    startRaf()
  }
}

function applySpeed() {
  audio.setRate(currentSpeed())
  speedLabel.textContent = currentSpeed().toFixed(1) + 'x'
  ;(speedDown as HTMLButtonElement).disabled = speedIdx === 0
  ;(speedUp   as HTMLButtonElement).disabled = speedIdx === SPEEDS.length - 1
}

function onEnded() {
  cancelAnimationFrame(raf)
  activeIndex = wordRects.length
  renderer?.render(wordRects, activeIndex, card)
  playBtn.textContent = '▶ Play'
  playBtn.classList.remove('playing')
  progressFill.style.width = '100%'
  timeCurrent.textContent  = timeTotal.textContent
}

function setupCanvasEvents() {
  canvasEl.addEventListener('click', onCanvasClick)
  canvasEl.addEventListener('touchend', e => {
    e.preventDefault()
    const t = e.changedTouches[0]
    onCanvasClick({ clientX: t.clientX, clientY: t.clientY } as MouseEvent)
  }, { passive: false })
}

async function onCanvasClick(e: MouseEvent) {
  const rect = canvasEl.getBoundingClientRect()
  const scrollTop = canvasEl.parentElement?.scrollTop ?? 0
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top + scrollTop

  if (card) {
    dismissCard()
    return
  }

  const hit = hitTest(mx, my)
  if (hit < 0) return
  const wr = wordRects[hit]

  hintEl.textContent = 'Looking up...'
  hintEl.classList.add('visible')

  const fetched = await fetchVocab(wr.rawWord, wr.x, wr.y, wr.height, canvasEl.clientWidth)
  hintEl.classList.remove('visible')

  card = fetched
  const passage = PASSAGES[currentLevel][currentIndex]
  wordRects = computeWordRects(passage.text, canvasEl.clientWidth, card)
  resizeCanvas()
  renderer?.resetHighlight()
  renderer?.render(wordRects, activeIndex, card)
}

function hitTest(mx: number, my: number): number {
  for (let i = 0; i < wordRects.length; i++) {
    const w = wordRects[i]
    if (mx >= w.x - 4 && mx <= w.x + w.width + 4 && my >= w.y && my <= w.y + w.height)
      return i
  }
  return -1
}

function dismissCard() {
  card = null
  const passage = PASSAGES[currentLevel][currentIndex]
  wordRects = computeWordRects(passage.text, canvasEl.clientWidth, null)
  resizeCanvas()
  renderer?.resetHighlight()
  renderer?.render(wordRects, activeIndex, null)
}

async function loadPassage(level: Level, index: number) {
  passageLoaded = false
  cancelAnimationFrame(raf)
  audio.stop()
  playBtn.textContent = '▶ Play'
  playBtn.classList.remove('playing')
  activeIndex = -1
  card        = null

  const passage = PASSAGES[level][index]
  passTitle.textContent = passage.pid.replace(/_/g, ' ') + ' (' + passage.wc + '語)'
  loadingEl.style.display = 'block'
  playerPanel.classList.remove('ready')

  try {
    const [timingData] = await Promise.all([
      fetch('audio/' + passage.pid + '.json').then(r => r.json() as Promise<WordTiming[]>),
      audio.load(passage.pid),
    ])
    timings   = timingData
    wordRects = computeWordRects(passage.text, Math.max(canvasEl.clientWidth, 300), null)

    timeTotal.textContent   = fmt(audio.duration / currentSpeed())
    timeCurrent.textContent = '0:00'
    progressFill.style.width = '0%'

    resizeCanvas()
    renderer?.resetHighlight()
    renderer?.render(wordRects, -1, null)

    loadingEl.style.display = 'none'
    playerPanel.classList.add('ready')
    passageLoaded = true
    applySpeed()
  } catch (err) {
    loadingEl.textContent = '読み込みエラー'
    console.error(err)
  }
}

function startRaf() {
  cancelAnimationFrame(raf)
  const loop = () => {
    const ct  = audio.currentTime
    activeIndex = findWordIndex(timings, ct)
    renderer?.render(wordRects, activeIndex, card)
    if (audio.duration > 0) {
      progressFill.style.width = (ct / audio.duration * 100) + '%'
      timeCurrent.textContent  = fmt(ct)
    }
    raf = requestAnimationFrame(loop)
  }
  raf = requestAnimationFrame(loop)
}

function resizeCanvas() {
  const passage = PASSAGES[currentLevel][currentIndex]
  const w = Math.max(canvasEl.clientWidth || canvasEl.parentElement?.clientWidth || 600, 300)
  const h = computeTextHeight(passage.text, w, card)
  renderer?.resize(w, Math.max(h, LINE_HEIGHT * 4))
}

function onResize() {
  if (!passageLoaded) return
  const passage = PASSAGES[currentLevel][currentIndex]
  const w = Math.max(canvasEl.clientWidth, 300)
  wordRects = computeWordRects(passage.text, w, card ? { ...card, x: w - card.width - 24, y: card.y } : null)
  resizeCanvas()
  renderer?.render(wordRects, activeIndex, card)
}

function fmt(s: number): string {
  const m   = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return m + ':' + sec.toString().padStart(2, '0')
}

document.addEventListener('DOMContentLoaded', init)
