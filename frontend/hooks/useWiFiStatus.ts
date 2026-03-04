'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

const POLL_INTERVAL = 10_000
const INITIAL_DELAY = 2_000

export function useWiFiStatus() {
  const [hasInternet, setHasInternet] = useState(true) // optimistic
  const [checking, setChecking] = useState(true)
  const mountedRef = useRef(true)

  const recheckNow = useCallback(async () => {
    try {
      const res = await fetch('/api/wifi/status')
      if (!mountedRef.current) return
      const data = await res.json()
      setHasInternet(data.has_internet)
    } catch {
      if (mountedRef.current) setHasInternet(false)
    } finally {
      if (mountedRef.current) setChecking(false)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    const initialTimer = setTimeout(recheckNow, INITIAL_DELAY)
    const interval = setInterval(recheckNow, POLL_INTERVAL)
    return () => {
      mountedRef.current = false
      clearTimeout(initialTimer)
      clearInterval(interval)
    }
  }, [recheckNow])

  return { hasInternet, checking, recheckNow }
}
