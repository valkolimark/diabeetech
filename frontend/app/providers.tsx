'use client'

import React, { createContext, useContext, useCallback, useMemo } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useGlucose } from '@/hooks/useGlucose'
import { useVoice } from '@/hooks/useVoice'
import { useAlerts } from '@/hooks/useAlerts'
import { useTimers } from '@/hooks/useTimers'
import { useSettings } from '@/hooks/useSettings'
import type {
  WSMessage,
  GlucoseUpdate,
  GlucoseHistory,
  VoiceStateData,
  VoiceTranscript,
  VoiceResponse,
  AlertState,
  TimerUpdate,
  Settings,
  ServerStatus,
} from '@/lib/types'

interface AppContextType {
  // Connection
  connected: boolean
  reconnecting: boolean
  send: (data: object) => void

  // Glucose
  glucose: GlucoseUpdate | null
  history: import('@/lib/types').GlucoseHistoryReading[]
  rangeHours: number
  setRangeHours: (hours: number) => void
  requestHistory: (hours: number) => void

  // Voice
  voiceState: VoiceStateData
  transcript: VoiceTranscript | null
  response: VoiceResponse | null

  // Alerts
  alert: AlertState
  isAlerting: boolean
  addressSituation: () => void
  problemAverted: () => void

  // Timers
  timers: import('@/lib/types').InsulinTimer[]
  deleteTimer: (id: string) => void
  deleteAllTimers: () => void

  // Settings
  settings: Settings
  updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => void
}

const AppContext = createContext<AppContextType | null>(null)

export function useApp(): AppContextType {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const {
    glucose, history, rangeHours, setRangeHours,
    handleGlucoseUpdate, handleGlucoseHistory,
  } = useGlucose()

  const {
    voiceState, transcript, response,
    handleVoiceState, handleVoiceTranscript, handleVoiceResponse,
  } = useVoice()

  const { alert, isAlerting, handleAlertState } = useAlerts()
  const { timers, handleTimerUpdate } = useTimers()
  const { settings, handleSettings, updateSetting } = useSettings()

  // Route incoming WebSocket messages to appropriate handlers
  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'glucose_update':
        handleGlucoseUpdate(message.data as GlucoseUpdate)
        break
      case 'glucose_history':
        handleGlucoseHistory(message.data as GlucoseHistory)
        break
      case 'voice_state':
        handleVoiceState(message.data as VoiceStateData)
        break
      case 'voice_transcript':
        handleVoiceTranscript(message.data as VoiceTranscript)
        break
      case 'voice_response':
        handleVoiceResponse(message.data as VoiceResponse)
        break
      case 'alert_state':
        handleAlertState(message.data as AlertState)
        break
      case 'timer_update':
        handleTimerUpdate(message.data as TimerUpdate)
        break
      case 'settings':
        handleSettings(message.data as Settings)
        break
      case 'server_status':
        // Could track this in its own hook if needed
        break
    }
  }, [
    handleGlucoseUpdate, handleGlucoseHistory,
    handleVoiceState, handleVoiceTranscript, handleVoiceResponse,
    handleAlertState, handleTimerUpdate, handleSettings,
  ])

  const { send, connected, reconnecting } = useWebSocket(handleMessage)

  // Action helpers
  const requestHistory = useCallback((hours: number) => {
    setRangeHours(hours)
    send({ type: 'request', action: 'glucose_history', payload: { range_hours: hours } })
  }, [send, setRangeHours])

  const addressSituation = useCallback(() => {
    send({ type: 'touch_command', action: 'address_situation' })
  }, [send])

  const problemAverted = useCallback(() => {
    send({ type: 'touch_command', action: 'problem_averted' })
  }, [send])

  const deleteTimer = useCallback((id: string) => {
    send({ type: 'touch_command', action: 'delete_timer', payload: { timer_id: id } })
  }, [send])

  const deleteAllTimers = useCallback(() => {
    send({ type: 'touch_command', action: 'delete_all_timers' })
  }, [send])

  const value = useMemo<AppContextType>(() => ({
    connected, reconnecting, send,
    glucose, history, rangeHours, setRangeHours, requestHistory,
    voiceState, transcript, response,
    alert, isAlerting, addressSituation, problemAverted,
    timers, deleteTimer, deleteAllTimers,
    settings,
    updateSetting,
  }), [
    connected, reconnecting, send,
    glucose, history, rangeHours, setRangeHours, requestHistory,
    voiceState, transcript, response,
    alert, isAlerting, addressSituation, problemAverted,
    timers, deleteTimer, deleteAllTimers,
    settings,
    updateSetting,
  ])

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}
