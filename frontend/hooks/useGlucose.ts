'use client'

import { useState, useCallback } from 'react'
import { GlucoseUpdate, GlucoseHistory, GlucoseHistoryReading } from '@/lib/types'

interface GlucoseState {
  current: GlucoseUpdate | null
  history: GlucoseHistoryReading[]
  rangeHours: number
}

export function useGlucose() {
  const [state, setState] = useState<GlucoseState>({
    current: null,
    history: [],
    rangeHours: 2,
  })

  const handleGlucoseUpdate = useCallback((data: GlucoseUpdate) => {
    setState(prev => ({ ...prev, current: data }))
  }, [])

  const handleGlucoseHistory = useCallback((data: GlucoseHistory) => {
    setState(prev => ({
      ...prev,
      history: data.readings,
      rangeHours: data.range_hours,
    }))
  }, [])

  const setRangeHours = useCallback((hours: number) => {
    setState(prev => ({ ...prev, rangeHours: hours }))
  }, [])

  return {
    glucose: state.current,
    history: state.history,
    rangeHours: state.rangeHours,
    setRangeHours,
    handleGlucoseUpdate,
    handleGlucoseHistory,
  }
}
