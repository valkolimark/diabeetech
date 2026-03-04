'use client'

import { getTrendChar, useTrendFont } from '@/lib/trends'
import type { TrendDirection } from '@/lib/types'

interface TrendArrowProps {
  direction: TrendDirection | string
  color: string
  size?: number
}

export default function TrendArrow({ direction, color, size = 50 }: TrendArrowProps) {
  const char = getTrendChar(direction as TrendDirection)
  const usePointerFont = useTrendFont(direction)

  return (
    <span
      className={usePointerFont ? 'font-arrows' : 'font-body'}
      style={{
        color,
        fontSize: `${size}px`,
        lineHeight: 1,
        display: 'inline-block',
      }}
    >
      {char}
    </span>
  )
}
