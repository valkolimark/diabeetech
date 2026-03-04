'use client'

import { useState, useCallback } from 'react'
import { Settings } from '@/lib/types'

const DEFAULT_SETTINGS: Settings = {
  display_name: '',
  display_mode: 'big',
  threshold_low: 100,
  threshold_trending_low: 120,
  threshold_trending_high: 263,
  threshold_high: 300,
  low_color: '#FF0000',
  trending_low_color: '#FFD700',
  normal_color: '#00FF00',
  trending_high_color: '#FF8C00',
  high_color: '#e100ff',
  wake_word: '',
  tts_voice: 'en-US-JennyNeural',
  timezone: 'America/Chicago',
  auto_announce_enabled: false,
  auto_announce_interval: 15,
  theme: '',
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)

  const handleSettings = useCallback((data: Settings) => {
    setSettings(data)
  }, [])

  const updateSetting = useCallback(<K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }, [])

  return {
    settings,
    handleSettings,
    updateSetting,
  }
}
