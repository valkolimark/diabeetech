'use client'

import { useState, useCallback } from 'react'
import { useApp } from '@/app/providers'

const WAKE_WORDS = [
  { file: 'Hey-Buzz.ppn', label: 'Hey Buzz' },
  { file: 'Bee-tech.ppn', label: 'Bee-tech' },
  { file: 'GlucoCom.ppn', label: 'GlucoCom' },
  { file: 'Gludi.ppn', label: 'Gludi' },
  { file: 'Bumble-Bee.ppn', label: 'Bumble Bee' },
  { file: 'Hive-One.ppn', label: 'Hive One' },
  { file: 'Queen-Bee.ppn', label: 'Queen Bee' },
]

const TTS_VOICES = [
  'en-US-JennyNeural',
  'en-US-GuyNeural',
  'en-US-AriaNeural',
  'en-US-DavisNeural',
  'en-US-SaraNeural',
]

export default function VoicePage() {
  const { settings, send } = useApp()
  const [wakeWord, setWakeWord] = useState(settings.wake_word || 'Hey-Buzz.ppn')
  const [ttsVoice, setTtsVoice] = useState(settings.tts_voice || 'en-US-JennyNeural')
  const [autoAnnounce, setAutoAnnounce] = useState(settings.auto_announce_enabled || false)
  const [announceInterval, setAnnounceInterval] = useState(settings.auto_announce_interval || 15)

  const saveWakeWord = useCallback((file: string) => {
    setWakeWord(file)
    send({ type: 'settings_update', key: 'wake_word', value: file })
  }, [send])

  const saveTtsVoice = useCallback((voice: string) => {
    setTtsVoice(voice)
    send({ type: 'settings_update', key: 'tts_voice', value: voice })
  }, [send])

  const toggleAutoAnnounce = useCallback((enabled: boolean) => {
    setAutoAnnounce(enabled)
    send({ type: 'settings_update', key: 'auto_announce_enabled', value: enabled })
  }, [send])

  const saveAnnounceInterval = useCallback((minutes: number) => {
    setAnnounceInterval(minutes)
    send({ type: 'settings_update', key: 'auto_announce_interval', value: minutes })
  }, [send])

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Voice</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Configure wake word, voice, and auto-announce
      </p>

      {/* Wake Word */}
      <div className="mb-6">
        <label className="text-xs font-body text-white/50 uppercase tracking-wider mb-3 block">
          Wake Word
        </label>
        <div className="grid grid-cols-2 gap-2">
          {WAKE_WORDS.map((ww) => (
            <button
              key={ww.file}
              onClick={() => saveWakeWord(ww.file)}
              className="px-4 py-2.5 rounded-xl text-sm font-body text-left transition-colors"
              style={{
                background: wakeWord === ww.file ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
                border: wakeWord === ww.file ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
                color: wakeWord === ww.file ? '#3b82f6' : 'rgba(255,255,255,0.6)',
              }}
            >
              {ww.label}
            </button>
          ))}
        </div>
      </div>

      {/* TTS Voice */}
      <div className="mb-6">
        <label className="text-xs font-body text-white/50 uppercase tracking-wider mb-3 block">
          TTS Voice
        </label>
        <div className="space-y-2">
          {TTS_VOICES.map((v) => (
            <button
              key={v}
              onClick={() => saveTtsVoice(v)}
              className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-sm font-body transition-colors"
              style={{
                background: ttsVoice === v ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
                border: ttsVoice === v ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
                color: ttsVoice === v ? '#3b82f6' : 'rgba(255,255,255,0.6)',
              }}
            >
              {v.replace('en-US-', '').replace('Neural', '')}
              {ttsVoice === v && <span className="text-xs">✓</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Auto-Announce */}
      <div className="mb-6">
        <label className="text-xs font-body text-white/50 uppercase tracking-wider mb-3 block">
          Auto-Announce Glucose
        </label>
        <div
          className="flex items-center justify-between px-4 py-3 rounded-xl mb-3"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <div>
            <div className="text-sm font-body text-white/80">Enable Auto-Announce</div>
            <div className="text-xs font-body text-white/30">Periodically speak glucose reading aloud</div>
          </div>
          <button
            onClick={() => toggleAutoAnnounce(!autoAnnounce)}
            className="w-12 h-7 rounded-full transition-colors relative"
            style={{ background: autoAnnounce ? '#3b82f6' : 'rgba(255,255,255,0.15)' }}
          >
            <div
              className="w-5 h-5 bg-white rounded-full absolute top-1 transition-all"
              style={{ left: autoAnnounce ? 26 : 4 }}
            />
          </button>
        </div>

        {autoAnnounce && (
          <div>
            <div className="text-xs font-body text-white/40 mb-2">Announce every</div>
            <div className="flex gap-2">
              {[5, 10, 15, 30, 60].map((m) => (
                <button
                  key={m}
                  onClick={() => saveAnnounceInterval(m)}
                  className="px-3 py-2 rounded-lg text-sm font-body transition-colors"
                  style={{
                    background: announceInterval === m ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
                    border: announceInterval === m ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
                    color: announceInterval === m ? '#3b82f6' : 'rgba(255,255,255,0.5)',
                  }}
                >
                  {m < 60 ? `${m}m` : '1h'}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
