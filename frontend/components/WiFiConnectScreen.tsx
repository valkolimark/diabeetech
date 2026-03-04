'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useKeyboard } from '@/components/VirtualKeyboard'

interface WiFiNetwork {
  ssid: string
  signal: number
  secured: boolean
}

type ViewState = 'scanning' | 'networks' | 'password' | 'connecting' | 'success' | 'failure'

interface WiFiConnectScreenProps {
  onConnected: () => void
}

export default function WiFiConnectScreen({ onConnected }: WiFiConnectScreenProps) {
  const [view, setView] = useState<ViewState>('scanning')
  const [networks, setNetworks] = useState<WiFiNetwork[]>([])
  const [selectedNetwork, setSelectedNetwork] = useState<WiFiNetwork | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    scanNetworks()
  }, [])

  const scanNetworks = useCallback(async () => {
    setView('scanning')
    try {
      const res = await fetch('/api/wifi/scan')
      const data = await res.json()
      setNetworks(data.networks || [])
      setView('networks')
    } catch {
      setNetworks([])
      setView('networks')
    }
  }, [])

  const handleSelectNetwork = (network: WiFiNetwork) => {
    setSelectedNetwork(network)
    setPassword('')
    setError('')
    if (network.secured) {
      setView('password')
    } else {
      handleConnect(network.ssid, '')
    }
  }

  const handleConnect = async (ssid: string, pwd: string) => {
    setView('connecting')
    try {
      const res = await fetch('/api/wifi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ssid, password: pwd }),
      })
      const data = await res.json()
      if (data.success) {
        setView('success')
        setTimeout(() => onConnected(), 2000)
      } else {
        setError(data.error || 'Connection failed')
        setView('failure')
      }
    } catch {
      setError('Unable to reach device. Please try again.')
      setView('failure')
    }
  }

  return (
    <motion.div
      className="fixed inset-0 z-[70] flex items-center justify-center"
      style={{ background: 'rgba(10, 10, 15, 0.98)' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <AnimatePresence mode="wait">
        {view === 'scanning' && <ScanningView key="scanning" />}
        {view === 'networks' && (
          <NetworkListView
            key="networks"
            networks={networks}
            onSelect={handleSelectNetwork}
            onRefresh={scanNetworks}
          />
        )}
        {view === 'password' && selectedNetwork && (
          <PasswordView
            key="password"
            network={selectedNetwork}
            password={password}
            onPasswordChange={setPassword}
            onConnect={() => handleConnect(selectedNetwork.ssid, password)}
            onBack={() => setView('networks')}
          />
        )}
        {view === 'connecting' && (
          <ConnectingView key="connecting" ssid={selectedNetwork?.ssid || ''} />
        )}
        {view === 'success' && (
          <SuccessView key="success" ssid={selectedNetwork?.ssid || ''} />
        )}
        {view === 'failure' && (
          <FailureView
            key="failure"
            error={error}
            onRetry={() => {
              if (selectedNetwork?.secured) {
                setPassword('')
                setView('password')
              } else {
                scanNetworks()
              }
            }}
            onScanAgain={scanNetworks}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}


// --- Sub-views ---

function ScanningView() {
  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <img src="/images/loading.gif" alt="Scanning" style={{ width: 200, height: 112 }} className="mb-6" />
      <div className="text-lg font-body text-white/80">Searching for networks...</div>
      <div className="text-sm font-body text-white/30 mt-2">This may take a few seconds</div>
    </motion.div>
  )
}

function NetworkListView({
  networks,
  onSelect,
  onRefresh,
}: {
  networks: WiFiNetwork[]
  onSelect: (n: WiFiNetwork) => void
  onRefresh: () => void
}) {
  return (
    <motion.div
      className="w-full max-w-md px-6"
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-body font-semibold text-white">WiFi Networks</h2>
          <p className="text-sm font-body text-white/30 mt-1">Select a network to connect</p>
        </div>
        <button
          onClick={onRefresh}
          className="w-10 h-10 flex items-center justify-center rounded-xl transition-colors"
          style={{ background: 'rgba(255,255,255,0.08)' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>

      {/* WiFi icon */}
      <div className="flex justify-center mb-4">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(59,130,246,0.6)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0" />
          <path d="M1.42 9a16 16 0 0 1 21.16 0" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <line x1="12" y1="20" x2="12.01" y2="20" />
        </svg>
      </div>

      {/* Network list */}
      <div className="space-y-2 max-h-[320px] overflow-y-auto">
        {networks.length === 0 ? (
          <div className="text-center py-8 text-sm font-body text-white/30">
            No networks found. Tap refresh to scan again.
          </div>
        ) : (
          networks.map((network) => (
            <motion.button
              key={network.ssid}
              onClick={() => onSelect(network)}
              className="w-full flex items-center gap-3 px-4 rounded-xl transition-colors"
              style={{
                height: 56,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
              }}
              whileTap={{ scale: 0.98 }}
            >
              <SignalBars signal={network.signal} />
              <span className="flex-1 text-left text-sm font-body text-white/90 truncate">
                {network.ssid}
              </span>
              {network.secured && (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              )}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </motion.button>
          ))
        )}
      </div>
    </motion.div>
  )
}

function PasswordView({
  network,
  password,
  onPasswordChange,
  onConnect,
  onBack,
}: {
  network: WiFiNetwork
  password: string
  onPasswordChange: (v: string) => void
  onConnect: () => void
  onBack: () => void
}) {
  const { openKeyboard, isOpen: keyboardOpen } = useKeyboard()
  const passwordRef = useRef<HTMLInputElement>(null)

  return (
    <motion.div
      className="w-full max-w-sm px-6"
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.3 }}
      style={{ paddingBottom: keyboardOpen ? 320 : 0, transition: 'padding-bottom 0.3s' }}
    >
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-sm font-body text-blue-400 hover:text-blue-300 transition-colors mb-6"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Back
      </button>

      <div className="flex items-center gap-3 mb-6">
        <SignalBars signal={network.signal} />
        <div>
          <div className="text-lg font-body font-semibold text-white">{network.ssid}</div>
          <div className="text-xs font-body text-white/30">Enter password to connect</div>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs font-body text-white/40 mb-1 block">Password</label>
        <input
          ref={passwordRef}
          type="password"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          onFocus={() => openKeyboard(passwordRef as React.RefObject<HTMLInputElement>)}
          placeholder="Enter WiFi password"
          className="w-full px-4 py-3 rounded-xl text-white font-body text-sm outline-none"
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        />
      </div>

      <button
        onClick={onConnect}
        disabled={!password}
        className="w-full py-3 rounded-xl text-sm font-body font-semibold transition-all"
        style={{
          background: password ? '#3b82f6' : 'rgba(59,130,246,0.3)',
          color: '#ffffff',
          opacity: password ? 1 : 0.5,
        }}
      >
        Connect
      </button>
    </motion.div>
  )
}

function ConnectingView({ ssid }: { ssid: string }) {
  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <img src="/images/loading.gif" alt="Connecting" style={{ width: 200, height: 112 }} className="mb-6" />
      <div className="text-lg font-body text-white/80">Connecting to {ssid}...</div>
      <div className="text-sm font-body text-white/30 mt-2">Please wait</div>
    </motion.div>
  )
}

function SuccessView({ ssid }: { ssid: string }) {
  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div
        className="w-20 h-20 rounded-full flex items-center justify-center mb-6"
        style={{ background: 'rgba(52,199,89,0.15)' }}
      >
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#34C759" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <div className="text-xl font-body font-semibold text-white">Connected!</div>
      <div className="text-sm font-body text-white/40 mt-2">Successfully connected to {ssid}</div>
    </motion.div>
  )
}

function FailureView({
  error,
  onRetry,
  onScanAgain,
}: {
  error: string
  onRetry: () => void
  onScanAgain: () => void
}) {
  return (
    <motion.div
      className="flex flex-col items-center px-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div
        className="w-20 h-20 rounded-full flex items-center justify-center mb-6"
        style={{ background: 'rgba(255,59,48,0.15)' }}
      >
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </div>
      <div className="text-xl font-body font-semibold text-white mb-2">Connection Failed</div>
      <div className="text-sm font-body text-white/40 text-center mb-8 max-w-xs">{error}</div>
      <div className="flex gap-3">
        <button
          onClick={onScanAgain}
          className="px-6 py-3 rounded-xl text-sm font-body font-medium transition-colors"
          style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.7)' }}
        >
          Scan Again
        </button>
        <button
          onClick={onRetry}
          className="px-6 py-3 rounded-xl text-sm font-body font-semibold transition-colors"
          style={{ background: '#3b82f6', color: '#ffffff' }}
        >
          Try Again
        </button>
      </div>
    </motion.div>
  )
}


// --- Signal Strength Bars ---

function SignalBars({ signal }: { signal: number }) {
  const bars = signal >= 66 ? 3 : signal >= 33 ? 2 : 1
  const active = 'rgba(59,130,246,0.8)'
  const dim = 'rgba(255,255,255,0.15)'

  return (
    <svg width="20" height="18" viewBox="0 0 20 18">
      <rect x="1" y="12" width="4" height="6" rx="1" fill={bars >= 1 ? active : dim} />
      <rect x="8" y="7" width="4" height="11" rx="1" fill={bars >= 2 ? active : dim} />
      <rect x="15" y="1" width="4" height="17" rx="1" fill={bars >= 3 ? active : dim} />
    </svg>
  )
}
