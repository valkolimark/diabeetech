'use client'

import { useState, useMemo, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useApp } from './providers'
import BigLayout from '@/components/layouts/BigLayout'
import CompactLayout from '@/components/layouts/CompactLayout'
// AlertPanel is now inline inside GlucoseDisplay, not an overlay
import HeaderBar from '@/components/HeaderBar'
import SettingsOverlay from '@/components/settings/SettingsOverlay'
import ClarityOverlay from '@/components/clarity/ClarityOverlay'
import ShutdownDialog from '@/components/ShutdownDialog'
import LoginScreen from '@/components/LoginScreen'
import { getTheme, lightenHex } from '@/lib/themes'

// Glucose state tint overlays — subtle, blended with theme bg
// Kept small so the theme color stays dominant
const STATE_TINTS: Record<string, { r: number; g: number; b: number }> = {
  trending_high: { r: 20, g: 10, b: 0 },
  high:          { r: 15, g: 0, b: 20 },
  trending_low:  { r: 18, g: 15, b: 0 },
  low:           { r: 20, g: 5, b: 5 },
  urgent_low:    { r: 25, g: 0, b: 0 },
  no_data:       { r: 5, g: 5, b: 5 },
}

/** Parse a hex color like #0a1628 into {r,g,b} */
function parseHex(hex: string): { r: number; g: number; b: number } {
  return {
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  }
}

/** Convert {r,g,b} back to a hex string */
function toHex(c: { r: number; g: number; b: number }): string {
  const clamp = (v: number) => Math.min(255, Math.max(0, Math.round(v)))
  return `#${clamp(c.r).toString(16).padStart(2, '0')}${clamp(c.g).toString(16).padStart(2, '0')}${clamp(c.b).toString(16).padStart(2, '0')}`
}

/** Blend a theme bg color with a state tint (additive) */
function blendColors(base: string, tint: { r: number; g: number; b: number }): string {
  const b = parseHex(base)
  return toHex({ r: b.r + tint.r, g: b.g + tint.g, b: b.b + tint.b })
}

export default function Home() {
  const { settings, connected, reconnecting, alert, glucose, send } = useApp()
  const isBig = settings.display_mode === 'big'
  const [showSettings, setShowSettings] = useState(false)
  const [showClarity, setShowClarity] = useState(false)
  const [showShutdown, setShowShutdown] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)
  const [authenticated, setAuthenticated] = useState(true) // optimistic

  // Check auth status on mount
  useEffect(() => {
    fetch('/api/auth/status')
      .then((r) => r.json())
      .then((data) => {
        setAuthenticated(data.authenticated)
        setAuthChecked(true)
      })
      .catch(() => {
        setAuthenticated(true) // assume auth on error
        setAuthChecked(true)
      })
  }, [])

  const isPulsing = alert.pulsing && !alert.addressed && !alert.muted
  const isUrgentLow = alert.level === 'urgent_low' && !alert.addressed && !alert.muted

  const glucoseState = glucose?.state || 'no_data'

  // Theme-aware background:
  // - Always uses the selected theme's bg as the base
  // - For alerting states, blends a state tint into the theme bg
  const bgStyle = useMemo(() => {
    const theme = getTheme(settings.theme)
    const baseBg = theme?.bg || '#0a0a0f'

    const tint = glucoseState !== 'normal' ? STATE_TINTS[glucoseState] : null
    const primary = tint ? blendColors(baseBg, tint) : baseBg
    const secondary = lightenHex(primary, 0.08)

    return {
      background: `linear-gradient(135deg, ${primary}, ${secondary})`,
      transition: 'background 1.5s ease',
    }
  }, [glucoseState, settings.theme])

  // Set theme accent as CSS variable
  useEffect(() => {
    const theme = getTheme(settings.theme)
    if (theme) {
      document.documentElement.style.setProperty('--theme-accent', theme.accent)
    }
  }, [settings.theme])

  // Show login screen if not authenticated
  if (authChecked && !authenticated) {
    return (
      <LoginScreen onLogin={() => {
        setAuthenticated(true)
        window.location.reload()
      }} />
    )
  }

  return (
    <main
      className={`w-screen h-screen flex flex-col overflow-hidden ${isPulsing ? 'alert-pulsing' : ''} ${isUrgentLow ? 'urgent-pulsing' : ''}`}
      style={bgStyle}
    >
      <HeaderBar
        onSettingsClick={() => setShowSettings(true)}
        onClarityClick={() => setShowClarity(true)}
        onPowerClick={() => setShowShutdown(true)}
      />
      <div className="flex-1 min-h-0">
        {isBig ? <BigLayout /> : <CompactLayout />}
      </div>

      <AnimatePresence>
        {showSettings && (
          <SettingsOverlay onClose={() => setShowSettings(false)} />
        )}
        {showClarity && (
          <ClarityOverlay onClose={() => setShowClarity(false)} />
        )}
        {showShutdown && (
          <ShutdownDialog
            onCancel={() => setShowShutdown(false)}
            onConfirm={() => {
              send({ type: 'system', action: 'shutdown' })
              setShowShutdown(false)
            }}
          />
        )}
      </AnimatePresence>
    </main>
  )
}
