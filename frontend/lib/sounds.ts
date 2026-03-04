/**
 * Web Audio API sound player for browser-side UI feedback sounds.
 * Safety-critical alert sounds are played by the server via aplay.
 */

let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  return audioContext
}

const soundCache: Record<string, AudioBuffer> = {}

async function loadSound(url: string): Promise<AudioBuffer> {
  if (soundCache[url]) return soundCache[url]

  const ctx = getAudioContext()
  const response = await fetch(url)
  const arrayBuffer = await response.arrayBuffer()
  const audioBuffer = await ctx.decodeAudioData(arrayBuffer)
  soundCache[url] = audioBuffer
  return audioBuffer
}

export async function playSound(url: string, volume: number = 1.0): Promise<void> {
  try {
    const ctx = getAudioContext()
    if (ctx.state === 'suspended') {
      await ctx.resume()
    }
    const buffer = await loadSound(url)
    const source = ctx.createBufferSource()
    const gainNode = ctx.createGain()
    gainNode.gain.value = volume
    source.buffer = buffer
    source.connect(gainNode)
    gainNode.connect(ctx.destination)
    source.start(0)
  } catch {
    // Silently fail — UI sounds are non-critical
  }
}
