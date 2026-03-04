'use client'

import ClockWidget from './ClockWidget'
import { useApp } from '@/app/providers'

interface HeaderBarProps {
  onSettingsClick?: () => void
  onClarityClick?: () => void
  onPowerClick?: () => void
}

export default function HeaderBar({ onSettingsClick, onClarityClick, onPowerClick }: HeaderBarProps) {
  const { connected } = useApp()

  return (
    <header
      className="w-full flex items-center justify-between px-4"
      style={{
        height: 48,
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      {/* Left: Clock + connection */}
      <div className="flex items-center gap-3">
        <ClockWidget />
        <div
          className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}
          title={connected ? 'Connected' : 'Disconnected'}
        />
      </div>

      {/* Center: Logo */}
      <span className="text-sm font-body uppercase text-white/50" style={{ letterSpacing: 3 }}>
        Diabeetech
      </span>

      {/* Right: Refresh, Clarity, Settings, Power */}
      <div className="flex items-center gap-2">
        {/* Refresh */}
        <button
          onClick={() => window.location.reload()}
          className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 transition-colors text-white/50 hover:text-white/80"
          title="Refresh"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>

        {/* Hive Insights */}
        <button
          onClick={onClarityClick}
          className="px-3 py-1.5 rounded-lg text-xs font-body text-white/50 hover:text-white/80 hover:bg-white/5 transition-colors"
          title="Hive Insights"
        >
          Insights
        </button>

        {/* Settings gear */}
        <button
          onClick={onSettingsClick}
          className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 transition-colors text-white/50 hover:text-white/80"
          title="Settings"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>

        {/* Power */}
        <button
          onClick={onPowerClick}
          className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 transition-colors text-white/50 hover:text-white/80"
          title="Shut Down"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
            <line x1="12" y1="2" x2="12" y2="12" />
          </svg>
        </button>
      </div>
    </header>
  )
}
