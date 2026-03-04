'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import GlucoseDisplay from '@/components/GlucoseDisplay'
import GlucoseGraph from '@/components/GlucoseGraph'
import InsulinTimers from '@/components/InsulinTimer'
import VoiceIndicator from '@/components/VoiceIndicator'

export default function CompactLayout() {
  const [showGraph, setShowGraph] = useState(false)

  return (
    <div className="relative w-full h-full">
      {/* Main content — full width, centered */}
      <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-4">
        <GlucoseDisplay
          numberSize={140}
          arrowSize={48}
          showDetails={true}
        />
        <VoiceIndicator />
        <InsulinTimers />

        {/* Graph toggle button */}
        <button
          onClick={() => setShowGraph(true)}
          className="absolute right-0 top-1/2 -translate-y-1/2 flex items-center justify-center rounded-l-lg transition-colors"
          style={{
            width: 28,
            height: 64,
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRight: 'none',
          }}
          title="Show graph"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      {/* Graph drawer — slides in from right */}
      <AnimatePresence>
        {showGraph && (
          <>
            {/* Backdrop */}
            <motion.div
              className="absolute inset-0 z-10"
              style={{ background: 'rgba(0,0,0,0.4)' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowGraph(false)}
            />
            {/* Drawer */}
            <motion.div
              className="absolute right-0 top-0 h-full z-20 flex flex-col p-3"
              style={{
                width: '55%',
                background: 'rgba(10,10,15,0.95)',
                borderLeft: '1px solid rgba(255,255,255,0.08)',
                backdropFilter: 'blur(16px)',
              }}
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            >
              {/* Close button */}
              <button
                onClick={() => setShowGraph(false)}
                className="self-start mb-2 flex items-center gap-1 text-xs font-body text-white/40 hover:text-white/70 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
                Close
              </button>
              <div className="flex-1 min-h-0">
                <GlucoseGraph />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
