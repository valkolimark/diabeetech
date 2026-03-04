'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '@/app/providers'

export default function VoiceIndicator() {
  const { voiceState } = useApp()
  const state = voiceState.state

  return (
    <div className="flex items-center justify-center" style={{ height: 48, width: 48 }}>
      <AnimatePresence mode="wait">
        {/* Idle: pulsing ring */}
        {state === 'idle' && (
          <motion.div
            key="idle"
            className="relative flex items-center justify-center"
            style={{ width: 24, height: 24 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              className="absolute rounded-full"
              style={{
                width: 24,
                height: 24,
                border: '2px solid rgba(255,255,255,0.15)',
              }}
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            />
          </motion.div>
        )}

        {/* Listening: expanding concentric rings */}
        {state === 'listening' && (
          <motion.div
            key="listening"
            className="relative flex items-center justify-center"
            style={{ width: 48, height: 48 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="absolute rounded-full"
                style={{
                  border: '2px solid #3b82f6',
                }}
                initial={{ width: 8, height: 8, opacity: 1 }}
                animate={{
                  width: [8, 44],
                  height: [8, 44],
                  opacity: [0.8, 0],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeOut',
                  delay: i * 0.5,
                }}
              />
            ))}
            <div
              className="rounded-full"
              style={{ width: 8, height: 8, background: '#3b82f6' }}
            />
          </motion.div>
        )}

        {/* Processing: bouncing dots */}
        {state === 'processing' && (
          <motion.div
            key="processing"
            className="flex items-center gap-1.5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="rounded-full"
                style={{ width: 8, height: 8, background: '#3b82f6' }}
                animate={{ y: [0, -8, 0] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.15,
                }}
              />
            ))}
          </motion.div>
        )}

        {/* Speaking: waveform bars */}
        {state === 'speaking' && (
          <motion.div
            key="speaking"
            className="flex items-center gap-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                className="rounded-full"
                style={{ width: 3, background: '#10b981' }}
                animate={{
                  height: [6, 12 + (i % 3) * 6, 6],
                }}
                transition={{
                  duration: 0.5 + (i % 2) * 0.2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.1,
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
