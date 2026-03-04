'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SettingsNav from './SettingsNav'
import DisplayNamePage from './DisplayNamePage'
import ThresholdsPage from './ThresholdsPage'
import ColorsPage from './ColorsPage'
import ContactsPage from './ContactsPage'
import WiFiPage from './WiFiPage'
import VoicePage from './VoicePage'
import ThemePage from './ThemePage'
import TimezonePage from './TimezonePage'
import SpeakerPage from './SpeakerPage'
import AboutPage from './AboutPage'

export type SettingsCategory =
  | 'display_name'
  | 'thresholds'
  | 'colors'
  | 'contacts'
  | 'wifi'
  | 'voice'
  | 'theme'
  | 'timezone'
  | 'speaker'
  | 'about'

interface SettingsOverlayProps {
  onClose: () => void
}

const PAGE_MAP: Record<SettingsCategory, React.FC> = {
  display_name: DisplayNamePage,
  thresholds: ThresholdsPage,
  colors: ColorsPage,
  contacts: ContactsPage,
  wifi: WiFiPage,
  voice: VoicePage,
  theme: ThemePage,
  timezone: TimezonePage,
  speaker: SpeakerPage,
  about: AboutPage,
}

export default function SettingsOverlay({ onClose }: SettingsOverlayProps) {
  const [activeCategory, setActiveCategory] = useState<SettingsCategory>('display_name')

  const ActivePage = PAGE_MAP[activeCategory]

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col"
      style={{
        background: 'rgba(10, 10, 15, 0.97)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      {/* Header */}
      <div
        className="flex items-center px-4"
        style={{
          height: 48,
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <button
          onClick={onClose}
          className="flex items-center gap-2 text-sm font-body text-blue-400 hover:text-blue-300 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </button>
        <span className="flex-1 text-center text-sm font-body uppercase text-white/50" style={{ letterSpacing: 3 }}>
          Settings
        </span>
        <div style={{ width: 60 }} />
      </div>

      {/* Body: Nav + Content */}
      <div className="flex flex-1 min-h-0">
        {/* Left sidebar nav */}
        <SettingsNav
          active={activeCategory}
          onChange={setActiveCategory}
        />

        {/* Right content area */}
        <div className="flex-1 min-h-0 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeCategory}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <ActivePage />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  )
}
