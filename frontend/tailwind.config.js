/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'db-bg': '#0a0a0f',
        'db-surface': 'rgba(255, 255, 255, 0.03)',
        'db-border': 'rgba(255, 255, 255, 0.06)',
        'db-normal': '#00FF00',
        'db-trending-high': '#FF8C00',
        'db-high': '#e100ff',
        'db-trending-low': '#FFD700',
        'db-low': '#FF0000',
        'db-no-data': '#404040',
        'db-text': '#ffffff',
        'db-text-muted': '#6b7280',
        'db-accent': '#3b82f6',
      },
      fontFamily: {
        'glucose': ['ProximaNovaBlack', 'Arial Black', 'Impact', 'Helvetica Neue', 'sans-serif'],
        'arrows': ['PizzaDudePointers'],
        'body': ['Poppins', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2s ease-in-out infinite',
        'pulse-alert': 'pulse-alert 0.5s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'pulse-alert': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'glow': {
          '0%': { filter: 'brightness(1)' },
          '100%': { filter: 'brightness(1.3)' },
        },
      },
    }
  },
  plugins: [],
}
