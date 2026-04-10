import type { WordTiming } from './types'

export class AudioEngine {
  private actx: AudioContext | null = null
  private source: AudioBufferSourceNode | null = null
  private buffer: AudioBuffer | null = null
  private startCtxTime = 0   // AudioContext.currentTime when playback began
  private startOffset  = 0   // track position (seconds) at last play()
  private _rate        = 0.9
  private _isPlaying   = false
  private endedCb: (() => void) | null = null

  get isPlaying() { return this._isPlaying }
  get rate()      { return this._rate }

  get currentTime(): number {
    if (!this.actx || !this._isPlaying) return this.startOffset
    const elapsed = (this.actx.currentTime - this.startCtxTime) * this._rate
    return Math.min(this.startOffset + elapsed, this.duration)
  }

  get duration(): number {
    return this.buffer?.duration ?? 0
  }

  private getCtx(): AudioContext {
    if (!this.actx) this.actx = new AudioContext()
    return this.actx
  }

  async load(pid: string): Promise<void> {
    this.stop()
    const ctx = this.getCtx()
    const res = await fetch(`audio/${pid}.mp3`)
    const ab  = await res.arrayBuffer()
    this.buffer      = await ctx.decodeAudioData(ab)
    this.startOffset = 0
  }

  play(onEnded?: () => void): void {
    if (!this.buffer) return
    const ctx = this.getCtx()
    if (ctx.state === 'suspended') ctx.resume()

    this._stop()
    this.endedCb = onEnded ?? null

    this.source = ctx.createBufferSource()
    this.source.buffer          = this.buffer
    this.source.playbackRate.value = this._rate
    this.source.connect(ctx.destination)
    this.source.start(0, this.startOffset)
    this.startCtxTime = ctx.currentTime
    this._isPlaying   = true

    this.source.onended = () => {
      if (this._isPlaying) {           // natural end (not stop/pause)
        this._isPlaying   = false
        this.startOffset  = 0
        this.endedCb?.()
      }
    }
  }

  pause(): void {
    if (!this._isPlaying) return
    this.startOffset = this.currentTime
    this._stop()
  }

  stop(): void {
    this._stop()
    this.startOffset = 0
  }

  seek(time: number): void {
    const was = this._isPlaying
    this._stop()
    this.startOffset = Math.max(0, Math.min(time, this.duration))
    if (was) this.play(this.endedCb ?? undefined)
  }

  setRate(rate: number): void {
    this._rate = rate
    if (this.source) this.source.playbackRate.value = rate
  }

  private _stop(): void {
    if (this.source) {
      try { this.source.stop() } catch (_) {}
      this.source.onended = null
      this.source = null
    }
    this._isPlaying = false
  }
}

/** Binary-search the current word index from a timings array */
export function findWordIndex(timings: WordTiming[], currentTime: number): number {
  if (!timings.length) return -1

  // Forward scan is actually fast for typical passage lengths (< 120 words)
  let best = -1
  for (let i = 0; i < timings.length; i++) {
    if (currentTime >= timings[i].start) {
      best = i
    } else {
      break
    }
  }
  return best
}
