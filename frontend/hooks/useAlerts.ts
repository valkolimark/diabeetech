'use client'

import { useState, useCallback } from 'react'
import { AlertState } from '@/lib/types'

const DEFAULT_ALERT: AlertState = {
  level: 'normal',
  pulsing: false,
  addressed: false,
  muted: false,
  countdown_remaining: null,
}

export function useAlerts() {
  const [alert, setAlert] = useState<AlertState>(DEFAULT_ALERT)

  const handleAlertState = useCallback((data: AlertState) => {
    setAlert(data)
  }, [])

  const isAlerting = (alert.level === 'low' || alert.level === 'urgent_low' || alert.level === 'trending_low') && !alert.muted

  return {
    alert,
    isAlerting,
    handleAlertState,
  }
}
