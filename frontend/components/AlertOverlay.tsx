'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '@/app/providers'

/**
 * Inline alert panel — shows below glucose reading for low/trending_low states only.
 * Not an overlay. Renders "Address the Situation" and "Problem Resolved" buttons
 * with a 5-minute countdown timer.
 */
export default function AlertPanel() {
  const { alert, addressSituation, problemAverted } = useApp()

  const isLowAlert =
    (alert.level === 'low' || alert.level === 'urgent_low' || alert.level === 'trending_low') &&
    !alert.muted

  const formatCountdown = (seconds: number | null): string => {
    if (seconds == null) return ''
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <AnimatePresence>
      {isLowAlert && (
        <motion.div
          className="flex flex-col items-center gap-3 mt-4"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          {/* Label */}
          <div className="text-sm font-body text-white/60 uppercase tracking-wider">
            {alert.level === 'urgent_low' && 'CRITICAL LOW'}
            {alert.level === 'low' && 'LOW GLUCOSE'}
            {alert.level === 'trending_low' && 'TRENDING LOW'}
          </div>

          {/* Address the Situation button */}
          {!alert.addressed && (
            <motion.button
              className="px-6 py-3 rounded-xl text-base font-body font-semibold
                bg-white text-black min-w-[220px]
                active:scale-95 transition-transform"
              whileTap={{ scale: 0.95 }}
              onClick={addressSituation}
            >
              Address the Situation
            </motion.button>
          )}

          {/* Countdown + Problem Resolved */}
          {alert.addressed && (
            <div className="flex flex-col items-center gap-3">
              {alert.countdown_remaining != null && (
                <div className="text-3xl font-glucose text-white/70 tabular-nums">
                  {formatCountdown(alert.countdown_remaining)}
                </div>
              )}
              <motion.button
                className="px-6 py-3 rounded-xl text-base font-body font-semibold
                  bg-green-600 text-white min-w-[220px]
                  active:scale-95 transition-transform"
                whileTap={{ scale: 0.95 }}
                onClick={problemAverted}
              >
                Problem Resolved
              </motion.button>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
