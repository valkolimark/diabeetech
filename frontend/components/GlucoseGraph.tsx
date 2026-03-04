'use client'

import { useEffect, useMemo, useState, useRef, useCallback } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { useApp } from '@/app/providers'
import TimeRangeSelector from './TimeRangeSelector'

function getColorForSgv(
  sgv: number,
  thresholds: { threshold_high: number; threshold_trending_high: number; threshold_trending_low: number; threshold_low: number }
): string {
  if (sgv >= thresholds.threshold_high) return '#e100ff'
  if (sgv >= thresholds.threshold_trending_high) return '#FF8C00'
  if (sgv < thresholds.threshold_low) return '#FF0000'
  if (sgv < thresholds.threshold_trending_low) return '#FFD700'
  return '#00cc44'
}

interface ZoomDomain {
  start: number
  end: number
}

const MIN_ZOOM_MS = 30 * 60 * 1000 // 30 minutes

export default function GlucoseGraph() {
  const { history, rangeHours, requestHistory, settings, connected } = useApp()

  const [zoomDomain, setZoomDomain] = useState<ZoomDomain | null>(null)
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const touchRef = useRef<{
    startDistance: number
    startDomain: ZoomDomain | null
    lastX: number | null
  }>({ startDistance: 0, startDomain: null, lastX: null })

  useEffect(() => {
    if (connected) {
      requestHistory(rangeHours)
    }
  }, [rangeHours, requestHistory, connected])

  // Reset zoom when time range changes
  useEffect(() => {
    setZoomDomain(null)
  }, [rangeHours])

  const chartData = useMemo(() => {
    return history.map((r) => ({
      time: new Date(r.timestamp).getTime(),
      sgv: r.sgv,
      color: getColorForSgv(r.sgv, settings),
    }))
  }, [history, settings])

  // Full data range boundaries
  const fullDomain = useMemo((): ZoomDomain | null => {
    if (chartData.length === 0) return null
    const times = chartData.map((d) => d.time)
    return { start: Math.min(...times), end: Math.max(...times) }
  }, [chartData])

  // X-axis domain: zoomed or full
  const xDomain = useMemo((): [number, number] | ['dataMin', 'dataMax'] => {
    if (zoomDomain) return [zoomDomain.start, zoomDomain.end]
    return ['dataMin', 'dataMax']
  }, [zoomDomain])

  // Filter data to visible range when zoomed (prevents dots rendering outside chart area)
  const visibleData = useMemo(() => {
    if (!zoomDomain) return chartData
    return chartData.filter((d) => d.time >= zoomDomain.start && d.time <= zoomDomain.end)
  }, [chartData, zoomDomain])

  const isZoomed = zoomDomain !== null

  // Generate tick positions at hour boundaries (adaptive intervals when zoomed in)
  const hourTicks = useMemo(() => {
    if (chartData.length === 0) return []

    const times = chartData.map((d) => d.time)
    const start = zoomDomain?.start ?? Math.min(...times)
    const end = zoomDomain?.end ?? Math.max(...times)
    const range = end - start

    let intervalMs: number
    if (range > 2 * 60 * 60 * 1000) {
      intervalMs = 60 * 60 * 1000 // 1 hour
    } else if (range > 60 * 60 * 1000) {
      intervalMs = 30 * 60 * 1000 // 30 minutes
    } else {
      intervalMs = 15 * 60 * 1000 // 15 minutes
    }

    const firstTick = Math.ceil(start / intervalMs) * intervalMs
    const ticks: number[] = []
    let t = firstTick
    while (t <= end) {
      ticks.push(t)
      t += intervalMs
    }

    return ticks
  }, [chartData, zoomDomain])

  const formatTime = (time: number) => {
    const d = new Date(time)
    const h = d.getHours()
    const m = d.getMinutes()
    const ampm = h >= 12 ? 'pm' : 'am'
    const h12 = h % 12 || 12
    return m === 0 ? `${h12}${ampm}` : `${h12}:${m.toString().padStart(2, '0')}${ampm}`
  }

  // --- Zoom: mousewheel ---
  const handleWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault()
      if (!fullDomain || !chartContainerRef.current) return

      const current = zoomDomain ?? fullDomain
      const range = current.end - current.start

      const zoomFactor = e.deltaY > 0 ? 1.15 : 0.85
      const newRange = Math.max(MIN_ZOOM_MS, range * zoomFactor)

      const fullRange = fullDomain.end - fullDomain.start
      if (newRange >= fullRange) {
        setZoomDomain(null)
        return
      }

      // Zoom toward cursor position
      const rect = chartContainerRef.current.getBoundingClientRect()
      const chartLeftPadding = 48 // margin.left(8) + yAxis width(40)
      const chartRightPadding = 20
      const chartWidth = rect.width - chartLeftPadding - chartRightPadding
      const cursorX = e.clientX - rect.left - chartLeftPadding
      const fraction = Math.max(0, Math.min(1, cursorX / chartWidth))

      const cursorTime = current.start + fraction * range
      let newStart = cursorTime - fraction * newRange
      let newEnd = cursorTime + (1 - fraction) * newRange

      // Clamp to full domain
      if (newStart < fullDomain.start) {
        newStart = fullDomain.start
        newEnd = fullDomain.start + newRange
      }
      if (newEnd > fullDomain.end) {
        newEnd = fullDomain.end
        newStart = fullDomain.end - newRange
      }

      setZoomDomain({ start: newStart, end: newEnd })
    },
    [zoomDomain, fullDomain]
  )

  // --- Zoom: pinch + pan (touch) ---
  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        touchRef.current.startDistance = Math.hypot(dx, dy)
        touchRef.current.startDomain = zoomDomain ?? fullDomain
        touchRef.current.lastX = null
      } else if (e.touches.length === 1 && zoomDomain) {
        touchRef.current.lastX = e.touches[0].clientX
      }
    },
    [zoomDomain, fullDomain]
  )

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!fullDomain || !chartContainerRef.current) return

      if (e.touches.length === 2 && touchRef.current.startDomain) {
        e.preventDefault()
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        const currentDistance = Math.hypot(dx, dy)
        const scale = touchRef.current.startDistance / currentDistance

        const domain = touchRef.current.startDomain
        const range = domain.end - domain.start
        const center = (domain.start + domain.end) / 2
        const fullRange = fullDomain.end - fullDomain.start
        const newRange = Math.max(MIN_ZOOM_MS, Math.min(fullRange, range * scale))

        if (newRange >= fullRange) {
          setZoomDomain(null)
          return
        }

        let newStart = center - newRange / 2
        let newEnd = center + newRange / 2
        if (newStart < fullDomain.start) {
          newStart = fullDomain.start
          newEnd = fullDomain.start + newRange
        }
        if (newEnd > fullDomain.end) {
          newEnd = fullDomain.end
          newStart = fullDomain.end - newRange
        }

        setZoomDomain({ start: newStart, end: newEnd })
      } else if (e.touches.length === 1 && zoomDomain && touchRef.current.lastX !== null) {
        e.preventDefault()
        const rect = chartContainerRef.current.getBoundingClientRect()
        const chartLeftPadding = 48
        const chartRightPadding = 20
        const chartWidth = rect.width - chartLeftPadding - chartRightPadding
        const range = zoomDomain.end - zoomDomain.start

        const deltaX = touchRef.current.lastX - e.touches[0].clientX
        const deltaTime = (deltaX / chartWidth) * range

        let newStart = zoomDomain.start + deltaTime
        let newEnd = zoomDomain.end + deltaTime

        if (newStart < fullDomain.start) {
          newStart = fullDomain.start
          newEnd = fullDomain.start + range
        }
        if (newEnd > fullDomain.end) {
          newEnd = fullDomain.end
          newStart = fullDomain.end - range
        }

        setZoomDomain({ start: newStart, end: newEnd })
        touchRef.current.lastX = e.touches[0].clientX
      }
    },
    [zoomDomain, fullDomain]
  )

  const handleTouchEnd = useCallback(() => {
    touchRef.current.startDistance = 0
    touchRef.current.startDomain = null
    touchRef.current.lastX = null
  }, [])

  // Attach native event listeners (need passive: false for preventDefault)
  useEffect(() => {
    const el = chartContainerRef.current
    if (!el) return

    el.addEventListener('wheel', handleWheel, { passive: false })
    el.addEventListener('touchstart', handleTouchStart, { passive: true })
    el.addEventListener('touchmove', handleTouchMove, { passive: false })
    el.addEventListener('touchend', handleTouchEnd, { passive: true })

    return () => {
      el.removeEventListener('wheel', handleWheel)
      el.removeEventListener('touchstart', handleTouchStart)
      el.removeEventListener('touchmove', handleTouchMove)
      el.removeEventListener('touchend', handleTouchEnd)
    }
  }, [handleWheel, handleTouchStart, handleTouchMove, handleTouchEnd])

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null
    const data = payload[0].payload
    const time = new Date(data.time)
    return (
      <div className="glass-panel px-3 py-2 text-xs">
        <div className="font-glucose text-lg" style={{ color: data.color }}>
          {data.sgv}
        </div>
        <div className="text-db-text-muted">
          {time.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
        </div>
      </div>
    )
  }

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (cx == null || cy == null) return null
    return (
      <circle
        cx={cx}
        cy={cy}
        r={3}
        fill={payload.color}
        style={{ filter: `drop-shadow(0 0 3px ${payload.color})` }}
      />
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-end mb-2">
        <TimeRangeSelector
          selected={rangeHours}
          onChange={requestHistory}
        />
      </div>

      <div
        ref={chartContainerRef}
        className="flex-1 min-h-0 relative"
        style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 12, touchAction: 'pan-y' }}
      >
        {isZoomed && (
          <button
            onClick={() => setZoomDomain(null)}
            className="absolute top-2 right-2 z-10 px-2 py-1 rounded-md text-xs font-body transition-colors"
            style={{
              background: 'rgba(255,255,255,0.1)',
              color: 'rgba(255,255,255,0.7)',
              border: '1px solid rgba(255,255,255,0.15)',
            }}
          >
            Reset Zoom
          </button>
        )}

        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-db-text-muted text-sm">
            No glucose data for this range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 16, right: 20, bottom: 12, left: 8 }}>
              <XAxis
                dataKey="time"
                type="number"
                domain={xDomain}
                allowDataOverflow={true}
                ticks={hourTicks}
                tickFormatter={formatTime}
                stroke="transparent"
                tick={{ fill: '#ffffff', fontSize: 13, fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
              />

              <YAxis
                dataKey="sgv"
                type="number"
                domain={[40, 400]}
                stroke="transparent"
                tick={{ fill: '#ffffff', fontSize: 13, fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
                width={40}
              />

              {/* Threshold lines */}
              <ReferenceLine
                y={settings.threshold_low}
                stroke="#FF0000"
                strokeDasharray="4 4"
                strokeOpacity={0.5}
              />
              <ReferenceLine
                y={settings.threshold_high}
                stroke="#FF0000"
                strokeDasharray="4 4"
                strokeOpacity={0.5}
              />

              <Tooltip content={<CustomTooltip />} cursor={false} />

              <Scatter
                data={visibleData}
                shape={<CustomDot />}
                isAnimationActive={false}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
