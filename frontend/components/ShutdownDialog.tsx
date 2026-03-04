'use client'

import { motion } from 'framer-motion'

interface ShutdownDialogProps {
  onConfirm: () => void
  onCancel: () => void
}

export default function ShutdownDialog({ onConfirm, onCancel }: ShutdownDialogProps) {
  return (
    <motion.div
      className="fixed inset-0 z-[60] flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      onClick={onCancel}
    >
      <motion.div
        className="rounded-2xl p-6 w-80"
        style={{ background: 'rgba(30,30,40,0.95)', border: '1px solid rgba(255,255,255,0.1)' }}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Power icon */}
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: 'rgba(255,59,48,0.15)' }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
              <line x1="12" y1="2" x2="12" y2="12" />
            </svg>
          </div>
        </div>

        <h3 className="text-white font-body font-semibold text-center text-lg mb-2">
          Shut Down Device?
        </h3>
        <p className="text-white/40 font-body text-sm text-center mb-6">
          The device will power off and stop monitoring glucose until restarted.
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-3 rounded-xl text-sm font-body font-medium transition-colors"
            style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.7)' }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-3 rounded-xl text-sm font-body font-semibold transition-colors"
            style={{ background: '#FF3B30', color: '#ffffff' }}
          >
            Shut Down
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
