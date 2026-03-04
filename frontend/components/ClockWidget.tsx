'use client'

import { useState, useEffect } from 'react'
import { useApp } from '@/app/providers'

export default function ClockWidget() {
  const { settings } = useApp()
  const [time, setTime] = useState('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      try {
        setTime(now.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          timeZone: settings.timezone || 'America/Chicago',
        }))
      } catch {
        setTime(now.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
        }))
      }
    }

    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [settings.timezone])

  return (
    <span className="text-sm text-white/80 font-body tabular-nums">
      {time}
    </span>
  )
}
