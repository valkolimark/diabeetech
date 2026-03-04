'use client'

import { useState, useCallback } from 'react'
import { VoiceStateData, VoiceTranscript, VoiceResponse } from '@/lib/types'

interface VoiceInfo {
  state: VoiceStateData
  transcript: VoiceTranscript | null
  response: VoiceResponse | null
}

export function useVoice() {
  const [info, setInfo] = useState<VoiceInfo>({
    state: { state: 'idle', amplitude: null, wake_word: null },
    transcript: null,
    response: null,
  })

  const handleVoiceState = useCallback((data: VoiceStateData) => {
    setInfo(prev => ({ ...prev, state: data }))
  }, [])

  const handleVoiceTranscript = useCallback((data: VoiceTranscript) => {
    setInfo(prev => ({ ...prev, transcript: data }))
  }, [])

  const handleVoiceResponse = useCallback((data: VoiceResponse) => {
    setInfo(prev => ({ ...prev, response: data }))
  }, [])

  return {
    voiceState: info.state,
    transcript: info.transcript,
    response: info.response,
    handleVoiceState,
    handleVoiceTranscript,
    handleVoiceResponse,
  }
}
