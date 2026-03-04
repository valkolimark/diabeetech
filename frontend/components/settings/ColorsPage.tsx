'use client'

import { useState, useCallback } from 'react'
import { useApp } from '@/app/providers'

interface ColorPickerRowProps {
  label: string
  settingKey: string
  value: string
  onSave: (key: string, value: string) => void
}

const PRESET_COLORS = [
  '#FF0000', '#FF4444', '#FF8C00', '#FFD700', '#FFFF00',
  '#00FF00', '#00cc44', '#00FFFF', '#3b82f6', '#007AFF',
  '#8B5CF6', '#a855f7', '#e100ff', '#FF69B4', '#FFFFFF',
]

function ColorPickerRow({ label, settingKey, value, onSave }: ColorPickerRowProps) {
  const [color, setColor] = useState(value)

  return (
    <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded-full" style={{ background: color, boxShadow: `0 0 8px ${color}60` }} />
        <span className="text-sm font-body text-white/70">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {PRESET_COLORS.slice(0, 8).map((c) => (
          <button
            key={c}
            onClick={() => { setColor(c); onSave(settingKey, c) }}
            className="w-5 h-5 rounded-full transition-transform hover:scale-125"
            style={{
              background: c,
              border: color === c ? '2px solid white' : '1px solid rgba(255,255,255,0.2)',
            }}
          />
        ))}
        <input
          type="color"
          value={color}
          onChange={(e) => { setColor(e.target.value); onSave(settingKey, e.target.value) }}
          className="w-6 h-6 rounded cursor-pointer"
          style={{ background: 'transparent', border: 'none' }}
        />
      </div>
    </div>
  )
}

export default function ColorsPage() {
  const { settings, send } = useApp()

  const handleSave = useCallback((key: string, value: string) => {
    send({ type: 'settings_update', key, value })
  }, [send])

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Status Colors</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Customize the color for each glucose state
      </p>

      <div>
        <ColorPickerRow label="Normal" settingKey="normal_color" value={settings.normal_color || '#00FF00'} onSave={handleSave} />
        <ColorPickerRow label="Trending High" settingKey="trending_high_color" value={settings.trending_high_color || '#FF8C00'} onSave={handleSave} />
        <ColorPickerRow label="High" settingKey="high_color" value={settings.high_color || '#e100ff'} onSave={handleSave} />
        <ColorPickerRow label="Trending Low" settingKey="trending_low_color" value={settings.trending_low_color || '#FFD700'} onSave={handleSave} />
        <ColorPickerRow label="Low" settingKey="low_color" value={settings.low_color || '#FF0000'} onSave={handleSave} />
      </div>
    </div>
  )
}
