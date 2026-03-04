'use client'

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useKeyboard } from '@/components/VirtualKeyboard'

interface LoginScreenProps {
  onLogin: () => void
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [showForm, setShowForm] = useState(false)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: '#000000' }}
    >
      <AnimatePresence mode="wait">
        {!showForm ? (
          <LandingView key="landing" onSignIn={() => setShowForm(true)} />
        ) : (
          <LoginForm key="form" onLogin={onLogin} onBack={() => setShowForm(false)} />
        )}
      </AnimatePresence>
    </div>
  )
}

function LandingView({ onSignIn }: { onSignIn: () => void }) {
  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4 }}
    >
      {/* Animated Logo */}
      <img
        src="/images/loading.gif"
        alt="Diabeetech"
        className="mb-6"
        style={{ width: 320, height: 180 }}
      />

      {/* Logo Text */}
      <div
        className="text-5xl font-body font-bold text-white uppercase"
        style={{ letterSpacing: 8 }}
      >
        Diabeetech
      </div>

      {/* Tagline */}
      <div className="text-sm font-body text-white/30 mt-3" style={{ letterSpacing: 2 }}>
        Glucose Monitoring System
      </div>

      {/* Divider */}
      <div
        className="mt-10 mb-8"
        style={{
          width: 60,
          height: 1,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
        }}
      />

      {/* Sign In Button */}
      <motion.button
        onClick={onSignIn}
        className="px-10 py-3 rounded-xl text-sm font-body font-semibold transition-all"
        style={{
          background: '#3b82f6',
          color: '#ffffff',
          minWidth: 200,
        }}
        whileTap={{ scale: 0.97 }}
      >
        Sign In
      </motion.button>
    </motion.div>
  )
}

function LoginForm({ onLogin, onBack }: { onLogin: () => void; onBack: () => void }) {
  const { openKeyboard, isOpen: keyboardOpen } = useKeyboard()
  const [subdomain, setSubdomain] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const subdomainRef = useRef<HTMLInputElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  const scrollFieldIntoView = (ref: React.RefObject<HTMLInputElement>) => {
    setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 250)
  }

  const handleFocus = (ref: React.RefObject<HTMLInputElement>, isNumeric = false) => {
    openKeyboard(ref as React.RefObject<HTMLInputElement>, isNumeric)
    scrollFieldIntoView(ref)
  }

  const handleLogin = useCallback(async () => {
    if (!subdomain || !email || !password) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subdomain, email, password }),
      })
      const data = await res.json()

      if (data.success) {
        onLogin()
      } else {
        setError(data.error || 'Login failed')
      }
    } catch {
      setError('Connection error. Check your network.')
    } finally {
      setLoading(false)
    }
  }, [subdomain, email, password, onLogin])

  return (
    <motion.div
      className="fixed inset-0 overflow-y-auto"
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 30 }}
      transition={{ duration: 0.3 }}
    >
      <div
        className="min-h-full flex flex-col items-center px-6 pt-4"
        style={{ paddingBottom: keyboardOpen ? 320 : 40 }}
      >
        {/* Header with back button */}
        <div className="w-full max-w-sm flex items-center mb-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm font-body text-blue-400 hover:text-blue-300 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back
          </button>
        </div>

        {/* Logo */}
        <div className="flex flex-col items-center mb-6">
          <div className="text-2xl font-body font-bold text-white uppercase" style={{ letterSpacing: 4 }}>
            Diabeetech
          </div>
          <div className="text-xs font-body text-white/30 mt-1">
            Glucose Monitoring System
          </div>
        </div>

        {/* Sign In heading */}
        <h2 className="text-lg font-body font-semibold text-white mb-4 text-center">
          Sign In
        </h2>

        {/* Form */}
        <div className="w-full max-w-sm space-y-4">
          {/* Subdomain */}
          <div>
            <label className="text-xs font-body text-white/40 mb-1 block">Subdomain</label>
            <div
              className="flex items-center rounded-xl"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <input
                ref={subdomainRef}
                type="text"
                value={subdomain}
                onChange={(e) => setSubdomain(e.target.value)}
                onFocus={() => handleFocus(subdomainRef)}
                placeholder="yourname"
                className="flex-1 min-w-0 px-4 py-3 bg-transparent text-white font-body text-sm outline-none"
              />
              <span className="text-xs font-body text-white/30 pr-3 flex-shrink-0 whitespace-nowrap">
                .diabeetech.net
              </span>
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="text-xs font-body text-white/40 mb-1 block">Email</label>
            <input
              ref={emailRef}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={() => handleFocus(emailRef)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 rounded-xl text-white font-body text-sm outline-none"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
            />
          </div>

          {/* Password */}
          <div>
            <label className="text-xs font-body text-white/40 mb-1 block">Password</label>
            <input
              ref={passwordRef}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => handleFocus(passwordRef)}
              placeholder="••••••••"
              className="w-full px-4 py-3 rounded-xl text-white font-body text-sm outline-none"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
            />
          </div>

          {/* Error */}
          {error && (
            <div className="text-xs font-body text-red-400 text-center py-2">
              {error}
            </div>
          )}

          {/* Sign In button */}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full py-3 rounded-xl text-sm font-body font-semibold transition-all"
            style={{
              background: loading ? 'rgba(59,130,246,0.5)' : '#3b82f6',
              color: '#ffffff',
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>
      </div>
    </motion.div>
  )
}
