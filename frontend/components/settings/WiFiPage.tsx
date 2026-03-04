'use client'

export default function WiFiPage() {
  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">WiFi</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Manage wireless network connections
      </p>

      <div
        className="flex flex-col items-center justify-center py-12 rounded-xl"
        style={{ background: 'rgba(255,255,255,0.03)' }}
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0" />
          <path d="M1.42 9a16 16 0 0 1 21.16 0" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <line x1="12" y1="20" x2="12.01" y2="20" />
        </svg>
        <p className="text-sm font-body text-white/30 mt-4">
          WiFi management available on device only
        </p>
        <p className="text-xs font-body text-white/20 mt-1">
          Connect to your Raspberry Pi to manage WiFi networks
        </p>
      </div>
    </div>
  )
}
