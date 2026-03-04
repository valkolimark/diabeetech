'use client'

import { useState, useCallback } from 'react'
import { TimerUpdate, InsulinTimer } from '@/lib/types'

export function useTimers() {
  const [timers, setTimers] = useState<InsulinTimer[]>([])

  const handleTimerUpdate = useCallback((data: TimerUpdate) => {
    setTimers(data.timers)
  }, [])

  return {
    timers,
    handleTimerUpdate,
  }
}
