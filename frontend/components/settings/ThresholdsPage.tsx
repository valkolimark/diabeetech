'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useApp } from '@/app/providers'

interface ThresholdSliderProps {
  label: string
  value: number
  min: number
  max: number
  color: string
  onChange: (v: number) => void
}

function ThresholdSlider({ label, value, min, max, color, onChange }: ThresholdSliderProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-body text-white/70">{label}</span>
        <span className="text-sm font-body font-semibold" style={{ color }}>
          {value} mg/dL
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, ${color} 0%, ${color} ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) 100%)`,
        }}
      />
    </div>
  )
}

export default function ThresholdsPage() {
  const { settings, send } = useApp()

  const [low, setLow] = useState(settings.threshold_low)
  const [trendingLow, setTrendingLow] = useState(settings.threshold_trending_low)
  const [trendingHigh, setTrendingHigh] = useState(settings.threshold_trending_high)
  const [high, setHigh] = useState(settings.threshold_high)

  const saveTimer = useRef<ReturnType<typeof setTimeout>>()

  const debouncedSave = useCallback((key: string, value: number) => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      send({ type: 'settings_update', key, value })
    }, 500)
  }, [send])

  const handleLow = (v: number) => { setLow(v); debouncedSave('threshold_low', v) }
  const handleTrendingLow = (v: number) => { setTrendingLow(v); debouncedSave('threshold_trending_low', v) }
  const handleTrendingHigh = (v: number) => { setTrendingHigh(v); debouncedSave('threshold_trending_high', v) }
  const handleHigh = (v: number) => { setHigh(v); debouncedSave('threshold_high', v) }

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Glucose Thresholds</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Set the glucose ranges for alerts and color coding
      </p>

      <div className="space-y-6">
        <ThresholdSlider label="Low Glucose" value={low} min={50} max={120} color="#FF0000" onChange={handleLow} />
        <ThresholdSlider label="Trending Low" value={trendingLow} min={80} max={150} color="#FFD700" onChange={handleTrendingLow} />
        <ThresholdSlider label="Trending High" value={trendingHigh} min={180} max={300} color="#FF8C00" onChange={handleTrendingHigh} />
        <ThresholdSlider label="High Glucose" value={high} min={200} max={400} color="#e100ff" onChange={handleHigh} />
      </div>

      {/* Validation warning */}
      {(low >= trendingLow || trendingLow >= trendingHigh || trendingHigh >= high) && (
        <div className="mt-4 px-4 py-2 rounded-xl text-xs font-body text-yellow-400" style={{ background: 'rgba(255,200,0,0.1)' }}>
          Thresholds must be in ascending order: Low &lt; Trending Low &lt; Trending High &lt; High
        </div>
      )}
    </div>
  )
}
