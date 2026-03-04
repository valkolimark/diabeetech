'use client'

import { useState, useCallback } from 'react'
import { useApp } from '@/app/providers'

const COMMON_TIMEZONES = [
  { value: 'America/New_York', label: 'Eastern (ET)' },
  { value: 'America/Chicago', label: 'Central (CT)' },
  { value: 'America/Denver', label: 'Mountain (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific (PT)' },
  { value: 'America/Anchorage', label: 'Alaska (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii (HT)' },
  { value: 'America/Phoenix', label: 'Arizona (no DST)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
]

export default function TimezonePage() {
  const { settings, send } = useApp()
  const [tz, setTz] = useState(settings.timezone || 'America/Chicago')

  const handleSelect = useCallback((value: string) => {
    setTz(value)
    send({ type: 'settings_update', key: 'timezone', value })
  }, [send])

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Timezone</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Set your local timezone for clock and timestamps
      </p>

      <div className="space-y-2">
        {COMMON_TIMEZONES.map((zone) => (
          <button
            key={zone.value}
            onClick={() => handleSelect(zone.value)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-body transition-colors"
            style={{
              background: tz === zone.value ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
              border: tz === zone.value ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
              color: tz === zone.value ? '#3b82f6' : 'rgba(255,255,255,0.6)',
            }}
          >
            {zone.label}
            {tz === zone.value && <span className="text-xs">✓</span>}
          </button>
        ))}
      </div>
    </div>
  )
}
