// Glucose states
export type GlucoseState = 'normal' | 'trending_high' | 'high' | 'trending_low' | 'low' | 'no_data'

// Trend directions (Nightscout format)
export type TrendDirection =
  | 'DoubleUp'
  | 'SingleUp'
  | 'FortyFiveUp'
  | 'Flat'
  | 'FortyFiveDown'
  | 'SingleDown'
  | 'DoubleDown'
  | 'NOT COMPUTABLE'

// Voice states
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking'

// Alert levels
export type AlertLevel = 'normal' | 'trending_low' | 'low' | 'urgent_low' | 'trending_high' | 'high' | 'no_data'

// Insulin timer phases
export type TimerPhase = 'active' | 'peak' | 'waning' | 'expired'

// Display modes
export type DisplayMode = 'compact' | 'big'

// --- Server → Browser event data types ---

export interface GlucoseUpdate {
  sgv: number | null
  trend: TrendDirection
  direction: TrendDirection
  timestamp: string
  delta: number | null
  state: GlucoseState
  color: string
  stale: boolean
  stale_minutes: number
}

export interface VoiceStateData {
  state: VoiceState
  amplitude: number | null
  wake_word: string | null
}

export interface VoiceTranscript {
  text: string
  is_final: boolean
  intent: string | null
  confidence: number | null
}

export interface VoiceResponse {
  text: string
  category: 'glucose' | 'nutrition' | 'insulin_confirm' | 'timer' | 'general' | 'error'
}

export interface AlertState {
  level: AlertLevel
  pulsing: boolean
  addressed: boolean
  muted: boolean
  countdown_remaining: number | null
}

export interface InsulinTimer {
  id: string
  insulin_type: string
  units: number
  start_time: string
  elapsed_seconds: number
  total_seconds: number
  phase: TimerPhase
  phase_color: string
  progress: number
}

export interface TimerUpdate {
  timers: InsulinTimer[]
}

export interface GlucoseHistoryReading {
  sgv: number
  timestamp: string
  trend: string
  state: GlucoseState
  color: string
}

export interface GlucoseHistory {
  readings: GlucoseHistoryReading[]
  range_hours: number
}

export interface Settings {
  display_name: string
  display_mode: DisplayMode
  threshold_low: number
  threshold_trending_low: number
  threshold_trending_high: number
  threshold_high: number
  low_color: string
  trending_low_color: string
  normal_color: string
  trending_high_color: string
  high_color: string
  wake_word: string
  tts_voice: string
  timezone: string
  auto_announce_enabled: boolean
  auto_announce_interval: number
  theme: string
}

export interface ServerStatus {
  connected_to_backend: boolean
  voice_engine_ready: boolean
  cgm_provider: string | null
  last_sync: string | null
}

// --- WebSocket message wrapper ---

export interface WSMessage {
  type: string
  data: any
}

// --- Browser → Server messages ---

export interface TouchCommand {
  type: 'touch_command'
  action: 'address_situation' | 'problem_averted' | 'delete_timer' | 'delete_all_timers'
  payload?: { timer_id?: string }
}

export interface DataRequest {
  type: 'request'
  action: 'glucose_history' | 'settings' | 'timers' | 'status'
  payload?: { range_hours?: number }
}
