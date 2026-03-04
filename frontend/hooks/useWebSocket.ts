'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { WSMessage } from '@/lib/types'

type MessageHandler = (message: WSMessage) => void

interface UseWebSocketReturn {
  send: (data: object) => void
  connected: boolean
  reconnecting: boolean
}

const WS_URL = 'ws://localhost:8080/ws'
const MAX_RECONNECT_DELAY = 10000 // 10 seconds
const INITIAL_RECONNECT_DELAY = 1000 // 1 second

export function useWebSocket(onMessage: MessageHandler): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)
  const onMessageRef = useRef(onMessage)

  // Keep the callback ref updated
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        setConnected(true)
        setReconnecting(false)
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY

        // Send ui_ready to get full state sync
        ws.send(JSON.stringify({ type: 'ui_ready' }))
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return
        try {
          const message: WSMessage = JSON.parse(event.data)
          onMessageRef.current(message)
        } catch {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        setConnected(false)
        scheduleReconnect()
      }

      ws.onerror = () => {
        // onclose will fire after onerror
      }
    } catch {
      scheduleReconnect()
    }
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return
    setReconnecting(true)

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
    }

    reconnectTimerRef.current = setTimeout(() => {
      // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
      reconnectDelayRef.current = Math.min(
        reconnectDelayRef.current * 2,
        MAX_RECONNECT_DELAY
      )
      connect()
    }, reconnectDelayRef.current)
  }, [connect])

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { send, connected, reconnecting }
}
