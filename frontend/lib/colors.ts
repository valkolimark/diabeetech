import { GlucoseState } from './types'

// Default glucose state colors (match settings.json)
export const GLUCOSE_COLORS: Record<GlucoseState, string> = {
  normal: '#00FF00',
  trending_high: '#FF8C00',
  high: '#e100ff',
  trending_low: '#FFD700',
  low: '#FF0000',
  no_data: '#404040',
}

// CSS variable glow colors (with alpha for shadow effects)
export function getGlowColor(state: GlucoseState): string {
  const glows: Record<GlucoseState, string> = {
    normal: 'rgba(0, 255, 0, 0.4)',
    trending_high: 'rgba(255, 140, 0, 0.4)',
    high: 'rgba(225, 0, 255, 0.4)',
    trending_low: 'rgba(255, 215, 0, 0.4)',
    low: 'rgba(255, 0, 0, 0.5)',
    no_data: 'rgba(64, 64, 64, 0.2)',
  }
  return glows[state] || glows.no_data
}

export function getStateColor(state: GlucoseState, customColors?: Record<string, string>): string {
  if (customColors) {
    const mapping: Record<GlucoseState, string> = {
      normal: customColors.normal_color || GLUCOSE_COLORS.normal,
      trending_high: customColors.trending_high_color || GLUCOSE_COLORS.trending_high,
      high: customColors.high_color || GLUCOSE_COLORS.high,
      trending_low: customColors.trending_low_color || GLUCOSE_COLORS.trending_low,
      low: customColors.low_color || GLUCOSE_COLORS.low,
      no_data: GLUCOSE_COLORS.no_data,
    }
    return mapping[state]
  }
  return GLUCOSE_COLORS[state]
}
