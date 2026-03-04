'use client'

import GlucoseDisplay from '@/components/GlucoseDisplay'
import GlucoseGraph from '@/components/GlucoseGraph'
import InsulinTimers from '@/components/InsulinTimer'
import VoiceIndicator from '@/components/VoiceIndicator'

export default function BigLayout() {
  return (
    <div className="flex w-full h-full">
      {/* Left Panel — 50% — Glucose, voice, timers */}
      <div
        className="h-full flex flex-col items-center justify-center p-3 gap-2"
        style={{
          width: '50%',
          background: 'rgba(0, 0, 0, 0.15)',
          borderRight: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        <GlucoseDisplay
          numberSize={110}
          arrowSize={38}
          showDetails={true}
        />
        <VoiceIndicator />
        <InsulinTimers />
      </div>

      {/* Right Panel — 50% — Graph */}
      <div className="h-full flex flex-col p-3" style={{ width: '50%' }}>
        <GlucoseGraph />
      </div>
    </div>
  )
}
