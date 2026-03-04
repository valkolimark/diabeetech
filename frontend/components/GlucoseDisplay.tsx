'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useSpring } from 'framer-motion'
import { useApp } from '@/app/providers'
import TrendArrow from './TrendArrow'
import AlertPanel from './AlertOverlay'
import { getGlowColor } from '@/lib/colors'
import type { GlucoseState } from '@/lib/types'

interface GlucoseDisplayProps {
  numberSize?: number
  arrowSize?: number
  showDetails?: boolean
}

export default function GlucoseDisplay({
  numberSize = 200,
  arrowSize = 50,
  showDetails = true,
}: GlucoseDisplayProps) {
  const { glucose, settings } = useApp()

  const springValue = useSpring(0, { stiffness: 80, damping: 20 })
  const [displayValue, setDisplayValue] = useState<string>('---')
  const prevSgvRef = useRef<number | null>(null)

  useEffect(() => {
    if (glucose?.sgv != null && !glucose.stale) {
      const sgv = glucose.sgv
      if (prevSgvRef.current !== null && prevSgvRef.current !== sgv) {
        springValue.set(sgv)
      } else {
        springValue.jump(sgv)
        // Directly set display value — jump() may not trigger the onChange listener
        setDisplayValue(Math.round(sgv).toString())
      }
      prevSgvRef.current = sgv
    }
  }, [glucose?.sgv, glucose?.stale, springValue])

  useEffect(() => {
    const unsubscribe = springValue.on('change', (v) => {
      setDisplayValue(Math.round(v).toString())
    })
    return unsubscribe
  }, [springValue])

  const isNoData = !glucose || glucose.stale || glucose.sgv == null
  const state: GlucoseState = glucose?.state as GlucoseState || 'no_data'
  const color = glucose?.color || '#404040'
  const glowColor = getGlowColor(state)

  const deltaText = glucose?.delta != null
    ? `${glucose.delta > 0 ? '+' : ''}${glucose.delta}`
    : '---'

  const minutesText = glucose?.stale_minutes
    ? `${glucose.stale_minutes}m ago`
    : glucose?.timestamp
    ? formatMinutesAgo(glucose.timestamp)
    : '---'

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Display Name */}
      {settings.display_name && (
        <div className="text-3xl font-bold font-body mb-2" style={{ color: 'rgba(255,255,255,0.85)', letterSpacing: 2 }}>
          {settings.display_name}
        </div>
      )}

      {/* Glucose Number + Trend Arrow */}
      <div className="flex items-center gap-2">
        <motion.div
          className="font-glucose leading-none"
          style={{
            fontSize: isNoData ? `${numberSize * 0.35}px` : `${numberSize}px`,
            color,
            textShadow: `0 0 40px ${glowColor}, 0 0 80px ${glowColor.replace('0.4', '0.2').replace('0.5', '0.25')}`,
          }}
          animate={{ color }}
          transition={{ duration: 0.5 }}
        >
          {isNoData ? 'NO DATA' : displayValue}
        </motion.div>

        {!isNoData && glucose && (
          <TrendArrow
            direction={glucose.trend}
            color={color}
            size={arrowSize}
          />
        )}
      </div>

      {isNoData && (
        <div
          className="font-glucose mt-1"
          style={{ fontSize: `${numberSize * 0.15}px`, color }}
        >
          Available
        </div>
      )}

      {/* Info Pills */}
      {showDetails && (
        <div className="flex items-center gap-2 mt-3">
          <span className="info-pill">
            <span className="value" style={{ color: isNoData ? '#404040' : color }}>{deltaText}</span>
            &nbsp;mg/dL
          </span>
          <span className="info-pill">
            {minutesText}
          </span>
        </div>
      )}

      {/* Alert buttons — inline below reading for low states */}
      <AlertPanel />
    </div>
  )
}

function formatMinutesAgo(timestamp: string): string {
  try {
    const dt = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - dt.getTime()
    const minutes = Math.floor(diffMs / 60000)
    if (minutes < 1) return 'just now'
    if (minutes === 1) return '1m ago'
    return `${minutes}m ago`
  } catch {
    return '---'
  }
}
