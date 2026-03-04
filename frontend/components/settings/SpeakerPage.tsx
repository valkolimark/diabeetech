'use client'

export default function SpeakerPage() {
  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Speaker Enrollment</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Enroll your voice for speaker verification
      </p>

      <div
        className="flex flex-col items-center justify-center py-12 rounded-xl"
        style={{ background: 'rgba(255,255,255,0.03)' }}
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
        <p className="text-sm font-body text-white/30 mt-4">
          Speaker enrollment available on device only
        </p>
        <p className="text-xs font-body text-white/20 mt-1">
          Uses Picovoice Eagle for voice verification
        </p>
      </div>
    </div>
  )
}
