/**
 * BGM audio sync — plays ambient audio and provides amplitude data
 * for wave animation intensity.
 */
export class AudioSync {
  private actx: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private audioEl: HTMLAudioElement | null = null
  private source: MediaElementAudioSourceNode | null = null
  private dataArray: Uint8Array<ArrayBuffer> | null = null
  private _isPlaying = false

  get isPlaying(): boolean { return this._isPlaying }

  private getCtx(): AudioContext {
    if (!this.actx) {
      this.actx = new AudioContext()
      this.analyser = this.actx.createAnalyser()
      this.analyser.fftSize = 256
      this.analyser.connect(this.actx.destination)
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount) as Uint8Array<ArrayBuffer>
    }
    return this.actx
  }

  /** Get current amplitude (0-1) for wave sync */
  getAmplitude(): number {
    if (!this.analyser || !this.dataArray) return 0
    this.analyser.getByteTimeDomainData(this.dataArray)
    let sum = 0
    for (let i = 0; i < this.dataArray.length; i++) {
      const v = (this.dataArray[i] - 128) / 128
      sum += v * v
    }
    return Math.sqrt(sum / this.dataArray.length)
  }

  async play(url: string): Promise<void> {
    const ctx = this.getCtx()
    if (ctx.state === 'suspended') await ctx.resume()

    if (this.audioEl) {
      this.audioEl.pause()
    }

    this.audioEl = new Audio(url)
    this.audioEl.loop = true
    this.audioEl.volume = 0.3

    if (!this.source) {
      this.source = ctx.createMediaElementSource(this.audioEl)
      this.source.connect(this.analyser!)
    }

    await this.audioEl.play()
    this._isPlaying = true
  }

  pause(): void {
    if (this.audioEl) {
      this.audioEl.pause()
      this._isPlaying = false
    }
  }

  toggle(url: string): void {
    if (this._isPlaying) {
      this.pause()
    } else {
      this.play(url)
    }
  }

  setVolume(v: number): void {
    if (this.audioEl) this.audioEl.volume = Math.max(0, Math.min(1, v))
  }
}
