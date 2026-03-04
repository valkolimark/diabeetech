export interface ThemeDef {
  name: string
  label: string
  accent: string
  bg: string
}

export const THEMES: ThemeDef[] = [
  { name: 'Theme 1', label: 'Cerulean Calm', accent: '#3b82f6', bg: '#17345f' },
  { name: 'Theme 2', label: 'Facebook Blue', accent: '#1877F2', bg: '#0a3068' },
  { name: 'Theme 3', label: 'Quantum Blue', accent: '#06b6d4', bg: '#034955' },
  { name: 'Theme 4', label: 'Lunar Tides', accent: '#8b5cf6', bg: '#382562' },
  { name: 'Theme 5', label: 'Mocha Sand', accent: '#d97706', bg: '#573003' },
  { name: 'Theme 6', label: 'Melon Mist', accent: '#f97316', bg: '#632e06' },
  { name: 'Theme 7', label: 'Twilight Violet', accent: '#a855f7', bg: '#432262' },
  { name: 'Theme 8', label: 'Sage Mist', accent: '#22c55e', bg: '#0e4f26' },
  { name: 'Theme 9', label: 'Amber Dusk', accent: '#eab308', bg: '#5e4803' },
  { name: 'Theme 10', label: 'Indigo Dream', accent: '#6366f1', bg: '#282860' },
  { name: 'Theme 11', label: 'Forest Echo', accent: '#10b981', bg: '#074a34' },
  { name: 'Theme 12', label: 'Burgundy Blush', accent: '#ef4444', bg: '#601b1b' },
]

export function getTheme(name: string): ThemeDef | undefined {
  return THEMES.find(t => t.name === name)
}

/** Lighten a hex color slightly for gradient secondary */
export function lightenHex(hex: string, amount: number = 0.15): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const lr = Math.min(255, Math.round(r + (255 - r) * amount))
  const lg = Math.min(255, Math.round(g + (255 - g) * amount))
  const lb = Math.min(255, Math.round(b + (255 - b) * amount))
  return `#${lr.toString(16).padStart(2, '0')}${lg.toString(16).padStart(2, '0')}${lb.toString(16).padStart(2, '0')}`
}
