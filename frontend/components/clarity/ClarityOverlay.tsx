'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ClarityData {
  period_days: number
  total_readings: number
  average_glucose: number
  std_deviation: number
  gmi: number
  time_in_range: { very_high: number; high: number; in_range: number; low: number; very_low: number }
  coefficient_of_variation: number
  data_sufficiency: number
  vs_prior_period: { average_change: number; average_change_pct: number }
}

interface ClarityOverlayProps {
  onClose: () => void
}

const PERIODS = [3, 7]

function gmiColor(gmi: number): string {
  if (gmi < 7) return '#34C759'
  if (gmi < 8) return '#FFD700'
  return '#FF3B30'
}

export default function ClarityOverlay({ onClose }: ClarityOverlayProps) {
  const [period, setPeriod] = useState(7)
  const [data, setData] = useState<ClarityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showNotice, setShowNotice] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/clarity/${period}`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [period])

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col"
      style={{
        background: 'rgba(10, 10, 15, 0.97)',
        backdropFilter: 'blur(20px)',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.25 }}
    >
      {/* Header */}
      <div className="flex items-center px-4" style={{ height: 48, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <button onClick={onClose} className="flex items-center gap-2 text-sm font-body text-blue-400 hover:text-blue-300">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Back
        </button>
        <span className="flex-1 text-center text-sm font-body uppercase text-white/50" style={{ letterSpacing: 3 }}>
          Hive Insights
        </span>
        <div style={{ width: 60 }} />
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Standard thresholds notice — collapsed by default */}
        <div className="flex justify-center mb-4">
          <button
            onClick={() => setShowNotice((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-colors"
            style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="rgba(59,130,246,0.7)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span className="text-[11px] font-body text-blue-400/70">Standard thresholds</span>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="rgba(59,130,246,0.5)" strokeWidth="2"
              style={{ transform: showNotice ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
        <AnimatePresence>
          {showNotice && (
            <motion.div
              className="flex justify-center mb-4"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="px-4 py-2 rounded-lg mx-auto max-w-md text-[11px] font-body text-blue-400/70 text-center"
                style={{ background: 'rgba(59,130,246,0.08)' }}>
                Calculated using standard clinical thresholds (In Range: 70–180 mg/dL, Low: &lt;70, Very Low: &lt;54, High: &gt;180, Very High: &gt;250), not your custom settings.
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Period selector */}
        <div className="flex justify-center gap-2 mb-6">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className="px-4 py-2 rounded-full text-sm font-body transition-all"
              style={{
                background: period === p ? 'rgba(59,130,246,0.3)' : 'rgba(255,255,255,0.06)',
                border: period === p ? '1px solid rgba(59,130,246,0.4)' : '1px solid transparent',
                color: period === p ? '#fff' : 'rgba(255,255,255,0.4)',
              }}
            >
              {p} days
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center text-white/30 font-body py-12">Loading...</div>
        ) : !data || data.total_readings === 0 ? (
          <div className="text-center text-white/30 font-body py-12">No data for this period</div>
        ) : (
          <div className="max-w-2xl mx-auto space-y-4">
            {/* Top stat cards */}
            <div className="grid grid-cols-3 gap-3">
              {/* Average */}
              <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <div className="text-xs font-body text-white/40 mb-1">Average</div>
                <div className="text-2xl font-glucose text-white">{Math.round(data.average_glucose)}</div>
                <div className="text-xs font-body text-white/30">mg/dL</div>
                {data.vs_prior_period.average_change !== 0 && (
                  <div className="text-xs font-body mt-1" style={{ color: data.vs_prior_period.average_change < 0 ? '#34C759' : '#FF9500' }}>
                    {data.vs_prior_period.average_change > 0 ? '▲' : '▼'} {Math.abs(data.vs_prior_period.average_change_pct)}%
                  </div>
                )}
              </div>

              {/* Std Dev */}
              <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <div className="text-xs font-body text-white/40 mb-1">Std Dev</div>
                <div className="text-2xl font-glucose text-white">±{Math.round(data.std_deviation)}</div>
                <div className="text-xs font-body text-white/30">mg/dL</div>
                <div className="text-xs font-body text-white/20 mt-1">CV: {data.coefficient_of_variation}%</div>
              </div>

              {/* GMI */}
              <div className="rounded-xl p-4 flex flex-col items-center" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <div className="text-xs font-body text-white/40 mb-2">Est. A1C (GMI)</div>
                <div className="relative" style={{ width: 64, height: 64 }}>
                  <svg width="64" height="64" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="28" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
                    <circle
                      cx="32" cy="32" r="28"
                      fill="none"
                      stroke={gmiColor(data.gmi)}
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray={`${(data.gmi / 14) * 176} 176`}
                      transform="rotate(-90 32 32)"
                      style={{ filter: `drop-shadow(0 0 4px ${gmiColor(data.gmi)}80)` }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-glucose" style={{ color: gmiColor(data.gmi) }}>{data.gmi}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Time in Range bar */}
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <div className="text-xs font-body text-white/40 mb-3">Time in Range</div>
              <div className="flex w-full h-8 rounded-lg overflow-hidden">
                {data.time_in_range.very_low > 0 && (
                  <div style={{ width: `${data.time_in_range.very_low}%`, background: '#8B0000' }} title={`Very Low: ${data.time_in_range.very_low}%`} />
                )}
                {data.time_in_range.low > 0 && (
                  <div style={{ width: `${data.time_in_range.low}%`, background: '#FF3B30' }} title={`Low: ${data.time_in_range.low}%`} />
                )}
                <div style={{ width: `${data.time_in_range.in_range}%`, background: '#34C759' }} title={`In Range: ${data.time_in_range.in_range}%`} />
                {data.time_in_range.high > 0 && (
                  <div style={{ width: `${data.time_in_range.high}%`, background: '#FF9500' }} title={`High: ${data.time_in_range.high}%`} />
                )}
                {data.time_in_range.very_high > 0 && (
                  <div style={{ width: `${data.time_in_range.very_high}%`, background: '#e100ff' }} title={`Very High: ${data.time_in_range.very_high}%`} />
                )}
              </div>
              <div className="flex justify-between mt-2 text-[10px] font-body text-white/40">
                <span>Very Low {data.time_in_range.very_low}%</span>
                <span>Low {data.time_in_range.low}%</span>
                <span style={{ color: '#34C759' }}>In Range {data.time_in_range.in_range}%</span>
                <span>High {data.time_in_range.high}%</span>
                <span>Very High {data.time_in_range.very_high}%</span>
              </div>
            </div>

            {/* Data sufficiency */}
            <div className="text-xs font-body text-white/30 text-center">
              {data.total_readings.toLocaleString()} readings ({data.data_sufficiency}% data sufficiency)
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
