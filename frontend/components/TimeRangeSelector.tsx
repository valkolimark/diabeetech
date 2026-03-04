'use client'

import { motion } from 'framer-motion'

interface TimeRangeSelectorProps {
  selected: number
  onChange: (hours: number) => void
}

const RANGES = [2, 6, 12, 24]

export default function TimeRangeSelector({ selected, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center gap-0.5 rounded-full p-1" style={{ background: 'rgba(255,255,255,0.06)' }}>
      {RANGES.map((hours) => (
        <button
          key={hours}
          onClick={() => onChange(hours)}
          className="relative px-3 py-1.5 text-xs font-body rounded-full transition-colors"
          style={{
            color: selected === hours ? '#ffffff' : 'rgba(255,255,255,0.4)',
            minWidth: 44,
            minHeight: 32,
          }}
        >
          {selected === hours && (
            <motion.div
              layoutId="range-pill"
              className="absolute inset-0 rounded-full"
              style={{
                background: 'rgba(59, 130, 246, 0.3)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                boxShadow: '0 0 12px rgba(59, 130, 246, 0.2)',
              }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
          <span className="relative z-10">{hours}h</span>
        </button>
      ))}
    </div>
  )
}
