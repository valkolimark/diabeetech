'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useApp } from '@/app/providers'
import { useKeyboard } from '@/components/VirtualKeyboard'

export default function DisplayNamePage() {
  const { settings, send } = useApp()
  const { openKeyboard } = useKeyboard()
  const [name, setName] = useState(settings.display_name || '')
  const [saved, setSaved] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Sync input value from virtual keyboard
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    const handler = () => setName(el.value.slice(0, 30))
    el.addEventListener('input', handler)
    return () => el.removeEventListener('input', handler)
  }, [])

  const handleSave = useCallback(() => {
    send({ type: 'settings_update', key: 'display_name', value: name })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }, [name, send])

  return (
    <div className="max-w-md">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Display Name</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Shown above your glucose reading
      </p>

      <div className="space-y-4">
        <div>
          <label className="text-xs font-body text-white/50 uppercase tracking-wider mb-2 block">
            Name
          </label>
          <input
            ref={inputRef}
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value.slice(0, 30))}
            onFocus={() => openKeyboard(inputRef as React.RefObject<HTMLInputElement>)}
            placeholder="Enter display name"
            maxLength={30}
            className="w-full px-4 py-3 rounded-xl text-white font-body text-sm outline-none transition-colors"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          />
          <div className="flex justify-end mt-1">
            <span className="text-xs font-body" style={{ color: name.length > 25 ? '#FF9500' : 'rgba(255,255,255,0.3)' }}>
              {name.length}/30
            </span>
          </div>
        </div>

        {/* Suggestions */}
        <div className="flex gap-2">
          {['Jordan', 'Mark', 'Ari'].map((s) => (
            <button
              key={s}
              onClick={() => setName(s)}
              className="px-3 py-1.5 rounded-lg text-xs font-body text-white/60 hover:text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.06)' }}
            >
              {s}
            </button>
          ))}
        </div>

        <button
          onClick={handleSave}
          disabled={!name || name === settings.display_name}
          className="w-full py-3 rounded-xl text-sm font-body font-semibold transition-all"
          style={{
            background: saved ? '#34C759' : (!name || name === settings.display_name) ? 'rgba(255,255,255,0.06)' : '#3b82f6',
            color: (!name || name === settings.display_name) ? 'rgba(255,255,255,0.3)' : '#ffffff',
          }}
        >
          {saved ? '✓ Saved!' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
