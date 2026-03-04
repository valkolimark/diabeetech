'use client'

import { useState, useEffect } from 'react'
import { useApp } from '@/app/providers'

export default function AboutPage() {
  const { settings, connected } = useApp()
  const [systemInfo, setSystemInfo] = useState<any>(null)

  useEffect(() => {
    fetch('/api/system/info')
      .then((r) => r.json())
      .then(setSystemInfo)
      .catch(() => {})
  }, [])

  const rows = [
    { label: 'Version', value: 'Diabeetech Web v2.0 — Phase 2' },
    { label: 'Device', value: systemInfo?.platform || 'Loading...' },
    { label: 'Subdomain', value: systemInfo?.subdomain || '—' },
    { label: 'Display Name', value: settings.display_name || '—' },
    { label: 'Server Status', value: connected ? 'Connected' : 'Disconnected' },
    { label: 'CGM Provider', value: 'Nightscout' },
    { label: 'Voice Engine', value: systemInfo?.dev_mode ? 'DEV_MODE (disabled)' : 'Picovoice' },
    { label: 'Timezone', value: settings.timezone || 'America/Chicago' },
  ]

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">About</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        System information and version details
      </p>

      <div className="rounded-xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.03)' }}>
        {rows.map((row, i) => (
          <div
            key={row.label}
            className="flex items-center justify-between px-4 py-3"
            style={{ borderBottom: i < rows.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}
          >
            <span className="text-sm font-body text-white/50">{row.label}</span>
            <span className="text-sm font-body text-white/80">{row.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
