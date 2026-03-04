# Diabeetech

Real-time continuous glucose monitoring system built for Raspberry Pi touchscreen devices. Connects to Nightscout backends to display glucose data, trigger audible alerts, and provide analytics — all through a sleek, touch-friendly interface.

## Features

- **Real-time glucose display** with color-coded states, trend arrows, and delta values
- **Interactive graph** with mousewheel/pinch zoom, pan, and 2h/6h/12h/24h time ranges
- **Audible alert system** with escalating notifications (trending high/low, high/low, urgent low) and countdown-based "Address the Situation" flow
- **Hive Insights analytics** — average glucose, GMI, time in range, coefficient of variation using standard clinical thresholds
- **Insulin timer tracking** with concentric ring visualization
- **WiFi Connect** — auto-detects no internet, scans networks, connects via touchscreen
- **Virtual keyboard** for touchscreen password and text input
- **12 built-in themes** with glucose-state color tinting
- **Multi-user authentication** via Nightscout subdomain login
- **Voice control** (Picovoice wake word + STT, Edge TTS)
- **Dev mode** with simulation endpoints for glucose, alerts, and WiFi

## Architecture

```
diabeetech-web/
├── frontend/          # Next.js 14 (static export)
│   ├── app/           # App router, providers, layout
│   ├── components/    # UI components (layouts, settings, overlays)
│   ├── hooks/         # Custom hooks (useWiFiStatus)
│   └── lib/           # Themes, utilities
├── server/            # FastAPI backend
│   ├── api/           # REST endpoints
│   ├── services/      # Business logic (alerts, WiFi, auth, glucose, clarity)
│   ├── data/          # JSON config files
│   └── static/        # Built frontend (generated)
```

**Frontend**: Next.js 14 with React, Tailwind CSS, Framer Motion, Recharts. Exported as static files served by the backend.

**Backend**: Python FastAPI with WebSocket for real-time updates. Connects to Nightscout for glucose data. Uses `nmcli` for WiFi management on Raspberry Pi.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### Setup

```bash
# Clone the repository
git clone https://github.com/valkolimark/diabeetech.git
cd diabeetech

# Install frontend dependencies
cd frontend
npm install

# Build frontend
npm run build

# Deploy to server static directory
cp -r out ../server/static

# Install backend dependencies
cd ../server
pip install -r requirements.txt

# Start the server
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open `http://localhost:8080` in your browser.

### Dev Mode Simulation

The app runs in dev mode on non-Pi platforms with simulated data.

```bash
# Simulate glucose level
curl -X POST localhost:8080/dev/glucose/simulate \
  -H 'Content-Type: application/json' \
  -d '{"sgv": 55, "trend": "Flat"}'

# Simulate no internet (triggers WiFi screen)
curl -X POST localhost:8080/dev/wifi/simulate \
  -H 'Content-Type: application/json' \
  -d '{"has_internet": false}'

# Restore internet
curl -X POST localhost:8080/dev/wifi/simulate \
  -H 'Content-Type: application/json' \
  -d '{"has_internet": true}'
```

## Raspberry Pi Deployment

Designed for Raspberry Pi 4/5 with official 7" touchscreen. On Pi, the app uses:

- `nmcli` for WiFi network scanning and connection
- Hardware-accelerated rendering for smooth animations
- Full-screen kiosk mode via Chromium

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript |
| Styling | Tailwind CSS, Framer Motion |
| Charts | Recharts |
| Backend | Python, FastAPI, WebSocket |
| CGM Data | Nightscout API |
| WiFi | nmcli (Linux/Pi) |
| Voice | Picovoice, Edge TTS |

## License

Proprietary. All rights reserved.
