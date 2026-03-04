'use client'

import { useState, useCallback } from 'react'
import { useApp } from '@/app/providers'
import { THEMES } from '@/lib/themes'

export default function ThemePage() {
  const { settings, send } = useApp()
  const [selectedTheme, setSelectedTheme] = useState(settings.theme || '')
  const [selectedMode, setSelectedMode] = useState<string>(settings.display_mode || 'big')
  const [saving, setSaving] = useState(false)

  const hasChanges =
    selectedTheme !== (settings.theme || '') ||
    selectedMode !== (settings.display_mode || 'big')

  const handleSave = useCallback(() => {
    setSaving(true)
    // Send both updates to the server
    if (selectedTheme !== (settings.theme || '')) {
      send({ type: 'settings_update', key: 'theme', value: selectedTheme })
    }
    if (selectedMode !== (settings.display_mode || 'big')) {
      send({ type: 'settings_update', key: 'display_mode', value: selectedMode })
    }
    // Reload after a short delay to let the server persist
    setTimeout(() => {
      window.location.reload()
    }, 500)
  }, [selectedTheme, selectedMode, settings.theme, settings.display_mode, send])

  return (
    <div className="max-w-lg">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xl font-body font-semibold text-white">Theme</h2>
        {hasChanges && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 rounded-xl text-sm font-body font-semibold transition-all"
            style={{
              background: saving ? 'rgba(34,197,94,0.3)' : 'rgba(34,197,94,0.2)',
              border: '1px solid rgba(34,197,94,0.5)',
              color: '#22c55e',
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? 'Saving...' : 'Save & Apply'}
          </button>
        )}
      </div>
      <p className="text-sm font-body text-white/40 mb-6">
        Choose your visual theme
      </p>

      {/* Theme grid */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        {THEMES.map((t) => {
          const isActive = selectedTheme === t.name
          return (
            <button
              key={t.name}
              onClick={() => setSelectedTheme(t.name)}
              className="flex flex-col items-center p-3 rounded-xl transition-all"
              style={{
                background: t.bg,
                border: isActive ? `2px solid ${t.accent}` : '1px solid rgba(255,255,255,0.08)',
                boxShadow: isActive ? `0 0 16px ${t.accent}40` : 'none',
              }}
            >
              <div
                className="w-8 h-8 rounded-full mb-2"
                style={{ background: t.accent, boxShadow: `0 0 12px ${t.accent}60` }}
              />
              <span
                className="text-[10px] font-body text-center leading-tight"
                style={{ color: isActive ? t.accent : 'rgba(255,255,255,0.6)' }}
              >
                {t.label}
              </span>
            </button>
          )
        })}
      </div>

      {/* Display Mode */}
      <label className="text-xs font-body text-white/50 uppercase tracking-wider mb-3 block">
        Display Mode
      </label>
      <div className="grid grid-cols-2 gap-3">
        {[
          { key: 'big', label: 'Big Display', desc: 'Split view with graph' },
          { key: 'compact', label: 'Compact', desc: 'Centered, graph hidden' },
        ].map((m) => (
          <button
            key={m.key}
            onClick={() => setSelectedMode(m.key)}
            className="flex flex-col items-center p-4 rounded-xl transition-all"
            style={{
              background: selectedMode === m.key ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
              border: selectedMode === m.key ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <span className="text-sm font-body" style={{ color: selectedMode === m.key ? '#3b82f6' : 'rgba(255,255,255,0.6)' }}>
              {m.label}
            </span>
            <span className="text-[10px] font-body text-white/30 mt-1">{m.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
