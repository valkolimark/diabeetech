import { TrendDirection } from './types'

/**
 * Map Nightscout direction strings to PizzaDude Pointers font characters.
 * This is the EXACT mapping from the existing itiflux app.
 */
export const TREND_ARROW_MAP: Record<TrendDirection, string> = {
  'DoubleUp': 'CC',
  'SingleUp': 'C',
  'FortyFiveUp': 'D',
  'Flat': 'E',
  'FortyFiveDown': 'F',
  'SingleDown': 'G',
  'DoubleDown': 'GG',
  'NOT COMPUTABLE': '?',
}

/**
 * Get the PizzaDude Pointers font character(s) for a trend direction.
 */
export function getTrendChar(direction: TrendDirection | string): string {
  return TREND_ARROW_MAP[direction as TrendDirection] || '?'
}

/**
 * Whether to use the PizzaDude Pointers font for this trend.
 * Returns false for "NOT COMPUTABLE" (should use Poppins for "?")
 */
export function useTrendFont(direction: TrendDirection | string): boolean {
  return direction !== 'NOT COMPUTABLE' && direction in TREND_ARROW_MAP
}

/**
 * Human-readable trend description.
 */
export function getTrendLabel(direction: TrendDirection | string): string {
  const labels: Record<string, string> = {
    'DoubleUp': 'Rising Rapidly',
    'SingleUp': 'Rising',
    'FortyFiveUp': 'Rising Slowly',
    'Flat': 'Steady',
    'FortyFiveDown': 'Falling Slowly',
    'SingleDown': 'Falling',
    'DoubleDown': 'Falling Rapidly',
    'NOT COMPUTABLE': 'Unknown',
  }
  return labels[direction] || 'Unknown'
}
