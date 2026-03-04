'use client'

import { useState } from 'react'
import type { SettingsCategory } from './SettingsOverlay'

interface SettingsNavProps {
  active: SettingsCategory
  onChange: (category: SettingsCategory) => void
}

const NAV_ITEMS: { key: SettingsCategory; label: string }[] = [
  { key: 'display_name', label: 'Display Name' },
  { key: 'thresholds', label: 'Thresholds' },
  { key: 'colors', label: 'Colors' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'wifi', label: 'WiFi' },
  { key: 'voice', label: 'Voice' },
  { key: 'theme', label: 'Theme' },
  { key: 'timezone', label: 'Timezone' },
  { key: 'speaker', label: 'Speaker' },
  { key: 'about', label: 'About' },
]

export default function SettingsNav({ active, onChange }: SettingsNavProps) {
  const [loggingOut, setLoggingOut] = useState(false)

  const handleLogout = async () => {
    setLoggingOut(true)
    try {
      await fetch('/api/auth/logout', { method: 'POST' })
      window.location.reload()
    } catch {
      setLoggingOut(false)
    }
  }

  return (
    <nav
      className="flex flex-col py-2 overflow-y-auto"
      style={{
        width: 200,
        background: 'rgba(0, 0, 0, 0.3)',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      {NAV_ITEMS.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className="flex items-center justify-between px-4 py-3 text-sm font-body transition-colors text-left"
          style={{
            color: active === key ? '#ffffff' : 'rgba(255,255,255,0.5)',
            background: active === key ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
            borderLeft: active === key ? '3px solid #3b82f6' : '3px solid transparent',
          }}
        >
          {label}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3 }}>
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      ))}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Log Out */}
      <button
        onClick={handleLogout}
        disabled={loggingOut}
        className="flex items-center gap-2 px-4 py-3 text-sm font-body transition-colors text-left mx-2 mb-2 rounded-lg"
        style={{
          color: '#ef4444',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.15)',
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        {loggingOut ? 'Logging out...' : 'Log Out'}
      </button>
    </nav>
  )
}
