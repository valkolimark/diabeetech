'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '@/app/providers'

function formatTime(totalSeconds: number): string {
  const remaining = Math.max(0, totalSeconds)
  const hours = Math.floor(remaining / 3600)
  const minutes = Math.floor((remaining % 3600) / 60)
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}`
  }
  const seconds = Math.floor(remaining % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const STROKE_WIDTH = 12
const RING_SPACING = 2      // tiny gap so rings look flush but distinct
const OUTER_RADIUS = 80

// Distinct colors per ring
const RING_COLORS = [
  '#3b82f6', // blue
  '#a855f7', // purple
  '#f97316', // orange
  '#06b6d4', // cyan
]

export default function InsulinTimers() {
  const { timers, deleteAllTimers } = useApp()

  if (timers.length === 0) return null

  const svgSize = (OUTER_RADIUS + STROKE_WIDTH / 2) * 2 + 8
  const center = svgSize / 2

  return (
    <div className="flex flex-col items-center gap-3">
      <span className="text-[10px] text-db-text-muted uppercase tracking-widest font-body">
        Insulin on Board
      </span>

      <AnimatePresence mode="wait">
        <motion.div
          key={timers.length}
          className="relative flex items-center justify-center"
          style={{ width: svgSize, height: svgSize }}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        >
          {/* SVG concentric rings */}
          <svg
            width={svgSize}
            height={svgSize}
            className="absolute transform -rotate-90"
          >
            {timers.map((timer, i) => {
              const radius = OUTER_RADIUS - i * (STROKE_WIDTH + RING_SPACING)
              if (radius < 20) return null
              const circumference = 2 * Math.PI * radius
              const color = RING_COLORS[i % RING_COLORS.length]

              return (
                <g key={timer.id}>
                  <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth={STROKE_WIDTH}
                  />
                  <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth={STROKE_WIDTH}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={circumference * timer.progress}
                    style={{
                      filter: `drop-shadow(0 0 8px ${color}90)`,
                      transition: 'stroke-dashoffset 1s linear, stroke 0.5s ease',
                    }}
                  />
                </g>
              )
            })}
          </svg>

          {/* Center text */}
          <div className="relative flex flex-col items-center justify-center z-10 gap-1">
            {timers.map((timer, i) => {
              const radius = OUTER_RADIUS - i * (STROKE_WIDTH + RING_SPACING)
              if (radius < 20) return null
              const remaining = timer.total_seconds - timer.elapsed_seconds
              const color = RING_COLORS[i % RING_COLORS.length]

              return (
                <div key={timer.id} className="flex items-center gap-2" style={{ color }}>
                  <span className="text-sm font-glucose leading-none">
                    {timer.units}u
                  </span>
                  <span className="text-[10px] font-body uppercase tracking-wide opacity-70 leading-none">
                    {timer.insulin_type}
                  </span>
                  <span className="text-xs font-body opacity-60 leading-none">
                    {formatTime(remaining)}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Delete touch target */}
          <button
            className="absolute inset-0 opacity-0 active:opacity-100 z-20"
            onDoubleClick={() => deleteAllTimers?.()}
            title="Double-tap to delete all"
          />
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
