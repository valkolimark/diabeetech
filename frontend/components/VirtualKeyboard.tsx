'use client'

import React, { createContext, useContext, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// --- Keyboard Context ---

interface KeyboardContextType {
  isOpen: boolean
  openKeyboard: (ref: React.RefObject<HTMLInputElement>, isNumeric?: boolean) => void
  closeKeyboard: () => void
}

const KeyboardContext = createContext<KeyboardContextType>({
  isOpen: false,
  openKeyboard: () => {},
  closeKeyboard: () => {},
})

export function useKeyboard() {
  return useContext(KeyboardContext)
}

export function VirtualKeyboardProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [numeric, setNumeric] = useState(false)
  const inputRef = useRef<React.RefObject<HTMLInputElement> | null>(null)

  const openKeyboard = useCallback((ref: React.RefObject<HTMLInputElement>, isNumeric = false) => {
    inputRef.current = ref
    setNumeric(isNumeric)
    setIsOpen(true)
  }, [])

  const closeKeyboard = useCallback(() => {
    setIsOpen(false)
    if (inputRef.current?.current) {
      inputRef.current.current.blur()
    }
    inputRef.current = null
  }, [])

  const handleKeyPress = useCallback((key: string) => {
    const el = inputRef.current?.current
    if (!el) return

    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    )?.set

    if (key === 'Backspace') {
      const newVal = el.value.slice(0, -1)
      nativeInputValueSetter?.call(el, newVal)
      el.dispatchEvent(new Event('input', { bubbles: true }))
    } else if (key === 'Enter') {
      closeKeyboard()
    } else {
      const newVal = el.value + key
      nativeInputValueSetter?.call(el, newVal)
      el.dispatchEvent(new Event('input', { bubbles: true }))
    }
  }, [closeKeyboard])

  return (
    <KeyboardContext.Provider value={{ isOpen, openKeyboard, closeKeyboard }}>
      {children}
      <AnimatePresence>
        {isOpen && (
          <KeyboardPanel
            numeric={numeric}
            onKeyPress={handleKeyPress}
            onClose={closeKeyboard}
          />
        )}
      </AnimatePresence>
    </KeyboardContext.Provider>
  )
}

// --- Layouts ---

type KeyboardMode = 'lower' | 'upper' | 'symbols1' | 'symbols2'

const ROWS_LOWER = [
  ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '⌫'],
  ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
  ['⇧', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '↵'],
  ['#+=', '.com', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '.net', '.org'],
  ['Hide', '@', ' ', '.', ','],
]

const ROWS_UPPER = [
  ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '⌫'],
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
  ['⇧', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '↵'],
  ['#+=', '.com', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '.net', '.org'],
  ['Hide', '@', ' ', '.', ','],
]

const ROWS_SYMBOLS1 = [
  ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '⌫'],
  ['-', '/', ':', ';', "'", '"', '{', '}', '[', ']'],
  ['#+=', '_', '\\', '|', '~', '<', '>', '?', '!', '+', '↵'],
  ['ABC', '.com', ' ', '.net', '.org'],
]

const ROWS_SYMBOLS2 = [
  ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '⌫'],
  ['€', '£', '¥', '•', '=', '+', '~', '`', '|', '\\'],
  ['ABC', '[', ']', '{', '}', '<', '>', '/', '?', '#', '↵'],
  ['ABC', '.com', ' ', '.net', '.org'],
]

const NUM_ROWS = [
  ['1', '2', '3'],
  ['4', '5', '6'],
  ['7', '8', '9'],
  ['+', '0', '⌫'],
]

// --- Keyboard Panel ---

interface KeyboardPanelProps {
  numeric: boolean
  onKeyPress: (key: string) => void
  onClose: () => void
}

function KeyboardPanel({ numeric, onKeyPress, onClose }: KeyboardPanelProps) {
  const [mode, setMode] = useState<KeyboardMode>('lower')

  const handleKey = (key: string) => {
    if (key === 'Hide') {
      onClose()
      return
    }
    if (key === '⇧') {
      setMode((m) => (m === 'upper' ? 'lower' : 'upper'))
      return
    }
    if (key === '#+=') {
      setMode((m) => (m === 'symbols1' ? 'symbols2' : 'symbols1'))
      return
    }
    if (key === 'ABC') {
      setMode('lower')
      return
    }
    if (key === '⌫') {
      onKeyPress('Backspace')
      return
    }
    if (key === '↵') {
      onKeyPress('Enter')
      return
    }
    onKeyPress(key)
    if (mode === 'upper') setMode('lower')
  }

  const getRows = () => {
    if (numeric) return NUM_ROWS
    switch (mode) {
      case 'upper': return ROWS_UPPER
      case 'symbols1': return ROWS_SYMBOLS1
      case 'symbols2': return ROWS_SYMBOLS2
      default: return ROWS_LOWER
    }
  }

  const rows = getRows()

  const getKeyWidth = (key: string): number => {
    if (key === ' ') return 200
    if (numeric) return 80
    if (['.com', '.net', '.org'].includes(key)) return 64
    if (['⇧', '⌫', '↵'].includes(key)) return 64
    if (['#+=', 'ABC', 'Hide'].includes(key)) return 64
    return 52
  }

  const isSpecial = (key: string) =>
    ['⇧', '⌫', '↵', '#+=', 'ABC', 'Hide', '.com', '.net', '.org'].includes(key)

  return (
    <motion.div
      className="fixed bottom-0 left-0 right-0 z-[80] flex flex-col"
      style={{
        background: 'rgba(20, 20, 25, 0.98)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255,255,255,0.08)',
      }}
      initial={{ y: '100%' }}
      animate={{ y: 0 }}
      exit={{ y: '100%' }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {/* Rows */}
      <div className={`flex flex-col gap-1.5 p-2 ${numeric ? 'items-center' : ''}`}>
        {rows.map((row, ri) => (
          <div key={ri} className="flex justify-center gap-1">
            {row.map((key) => {
              const isSpace = key === ' '
              const special = isSpecial(key)
              const isShiftActive = key === '⇧' && mode === 'upper'
              const isSymbolActive = key === '#+=' && (mode === 'symbols1' || mode === 'symbols2')
              const isHide = key === 'Hide'

              return (
                <motion.button
                  key={`${ri}-${key}`}
                  onClick={() => handleKey(key)}
                  className="flex items-center justify-center rounded-lg text-white font-body select-none"
                  style={{
                    width: getKeyWidth(key),
                    height: 48,
                    fontSize: special ? 14 : 18,
                    background: isShiftActive || isSymbolActive
                      ? 'rgba(59,130,246,0.3)'
                      : isHide
                      ? 'rgba(239,68,68,0.15)'
                      : special
                      ? 'rgba(255,255,255,0.12)'
                      : 'rgba(255,255,255,0.08)',
                    border: isHide
                      ? '1px solid rgba(239,68,68,0.2)'
                      : '1px solid rgba(255,255,255,0.1)',
                    color: isHide ? '#ef4444' : '#ffffff',
                  }}
                  whileTap={{ scale: 0.93, background: 'rgba(255,255,255,0.15)' }}
                >
                  {isSpace ? 'space' : key}
                </motion.button>
              )
            })}
          </div>
        ))}

        {/* Done row for numeric */}
        {numeric && (
          <div className="flex justify-center gap-2 mt-1">
            <motion.button
              onClick={onClose}
              className="flex items-center justify-center rounded-lg text-white/60 font-body"
              style={{ width: 120, height: 48, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
              whileTap={{ scale: 0.95 }}
            >
              Cancel
            </motion.button>
            <motion.button
              onClick={() => onKeyPress('Enter')}
              className="flex items-center justify-center rounded-lg text-white font-body font-semibold"
              style={{ width: 120, height: 48, background: '#3b82f6' }}
              whileTap={{ scale: 0.95 }}
            >
              Done
            </motion.button>
          </div>
        )}
      </div>
    </motion.div>
  )
}
