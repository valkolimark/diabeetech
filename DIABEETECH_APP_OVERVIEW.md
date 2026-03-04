# Diabeetech Web Application

## What Is Diabeetech?

Diabeetech is a real-time continuous glucose monitoring (CGM) display system designed to run on a Raspberry Pi as a dedicated bedside/desk device. It connects to a user's Nightscout multi-tenant backend to pull live CGM data and presents it on a touchscreen display with audible alerts, voice interaction, insulin tracking, and analytics.

The application consists of a **FastAPI Python backend** and a **Next.js (React) static frontend**, communicating via WebSocket for real-time updates.

---

## Architecture

- **Backend**: Python FastAPI server (`server/main.py`) serving REST API, WebSocket, and static frontend
- **Frontend**: Next.js static export served from `server/static/`
- **Data Source**: Nightscout multi-tenant API (`https://{subdomain}.diabeetech.net`)
- **Audio**: Platform-native sound playback (`afplay` on macOS, `aplay` on Linux)
- **Voice**: Picovoice (wake word + STT) + Microsoft Edge TTS
- **Target Platform**: Raspberry Pi with touchscreen (also runs on macOS for development)

---

## Features

### 1. Real-Time Glucose Monitoring
- 30-second polling loop for latest CGM readings from Nightscout
- 5-minute background sync for historical data
- Glucose state classification based on configurable thresholds:
  - **Low** (below low threshold)
  - **Trending Low** (between low and trending low thresholds)
  - **Normal** (between trending low and trending high thresholds)
  - **Trending High** (between trending high and high thresholds)
  - **High** (above high threshold)
  - **Urgent Low** (below 70 mg/dL within low state)
  - **No Data** (stale or missing readings)
- Color-coded display for each state (customizable colors)
- Delta (change) calculation between readings
- Trend direction arrows (DoubleUp, SingleUp, FortyFiveUp, Flat, FortyFiveDown, SingleDown, DoubleDown)
- Spring-animated number transitions
- "Minutes ago" timestamp display

### 2. Glucose Graph
- Recharts scatter plot of historical readings
- Color-coded dots matching glucose state
- Time range selector: 2h, 6h, 12h, 24h
- Threshold reference lines
- Custom tooltip with SGV value and timestamp

### 3. Audible Alert System
- Sound alerts triggered by glucose thresholds:
  - **Normal / Recovery**: EL.wav (plays once)
  - **Trending Low**: LN.wav (every 8 seconds) + action buttons
  - **Low**: LN.wav (every 5 seconds) + action buttons
  - **Urgent/Critical Low** (<70): ULN.wav (every 3 seconds) + action buttons
  - **High**: HN.wav (plays once)
  - **Trending High**: No sound (silent)
  - **No Data**: ND.wav (every 30 seconds)
- **Address the Situation** button (low states only):
  - Stops repeating sound
  - Starts 5-minute countdown timer
  - Shows "Problem Resolved" button
- **Problem Resolved** button: stops all sounds and countdown
- Countdown expiry restarts the alert cycle
- Visual pulsing background animation for low states

### 4. Multi-User Authentication
- Login flow with Nightscout multi-tenant backend
  - Subdomain + email + password
  - JWT token authentication with API secret fallback
- Branded landing screen with animated logo and "Sign In" button
- Logout button in Settings sidebar
- User switching: fully reinitializes all services
  - Clears glucose history cache
  - Updates display name to match logged-in user
  - Fetches fresh data from new user's Nightscout instance
  - Broadcasts updated settings and cleared history to frontend
- Persistent login via `~/.diabeetech/saved_login.json`

### 5. Insulin Timer Tracking
- Multiple concurrent insulin timers
- Timer lifecycle phases with color coding:
  - **Active** (0-30 min): Blue
  - **Peak** (30-150 min): Green
  - **Waning** (150+ min): Orange to Red gradient
  - **Expired**: Auto-removed
- SVG concentric ring visualization
- Progress tracking and remaining time display
- Delete individual or all timers
- Persistent state storage

### 6. Display Layouts
- **Big Layout**: 50/50 horizontal split
  - Left: Glucose display, voice indicator, insulin timers
  - Right: Glucose graph with time range selector
- **Compact Layout**: Vertical stack for smaller displays
- Switchable via Theme settings page

### 7. Theme System
- 12 built-in themes:
  1. Cerulean Calm (blue)
  2. Facebook Blue
  3. Quantum Blue (cyan)
  4. Lunar Tides (purple)
  5. Mocha Sand (brown)
  6. Melon Mist (orange)
  7. Twilight Violet (purple)
  8. Sage Mist (green)
  9. Amber Dusk (yellow)
  10. Indigo Dream (indigo)
  11. Forest Echo (teal)
  12. Burgundy Blush (red)
- Theme controls background color (dominant)
- Glucose state tints blend additively with theme background
- Save & Apply with page reload

### 8. Clarity Analytics
- Period selector: 3, 7, 14, 30 days
- Metrics:
  - Average Glucose with prior period comparison
  - Glucose Management Indicator (GMI / estimated A1C)
  - Time in Range breakdown (Very High, High, In Range, Low, Very Low)
  - Standard Deviation
  - Coefficient of Variation
  - Data Sufficiency percentage
- Color-coded GMI (green < 7, yellow 7-8, red > 8)
- Trend comparison vs prior period

### 9. Voice System
- **Wake Word Detection**: Picovoice Cobra with selectable wake words (Hey Buzz, Bee-tech, GlucoCom, Gludi, Bumble Bee, Hive One, Queen Bee)
- **Speech-to-Text**: Picovoice Cheetah with automatic punctuation
- **Text-to-Speech**: Microsoft Edge TTS with 5 voice options (Jenny, Guy, Aria, Davis, Sara)
- **Auto-Announce**: Periodic glucose reading announcements (configurable interval)
- **Visual Indicator**: Animated states (idle, listening, processing, speaking)
- **Intent Classification**: Glucose queries, insulin logging, meal logging, timer commands

### 10. Virtual Keyboard
- Full QWERTY layout with uppercase/lowercase toggle
- Number row on main keyboard
- Two symbol pages (all special characters, currency symbols, brackets, etc.)
- Domain shortcuts: .com, .net, .org
- @ key on bottom row
- Hide button to dismiss keyboard
- Numeric keypad mode for number-only fields
- Active field scrolls into view above keyboard

### 11. Settings
- **Display Name**: Customizable name shown above glucose reading
- **Glucose Thresholds**: Interactive sliders for Low, Trending Low, Trending High, High
- **Status Colors**: Color picker for each glucose state
- **Emergency Contacts**: Name + phone number list for SMS alerts
- **WiFi**: Network management (Raspberry Pi only)
- **Voice**: Wake word selection, TTS voice, auto-announce toggle and interval
- **Theme**: Theme selection + display mode (Big/Compact)
- **Timezone**: 10+ timezone options including US zones and international
- **Speaker Enrollment**: Voice recognition setup (Picovoice Eagle)
- **About**: System information display

### 12. Header Bar
- Real-time clock (timezone-aware)
- WebSocket connection status indicator (green/red dot)
- Refresh button (page reload)
- Clarity analytics button
- Settings button
- Power/shutdown button with confirmation dialog

### 13. Dev Mode
- Simulation endpoints for testing without real CGM data:
  - Glucose state simulation (any SGV value)
  - Alert level simulation
  - Timer creation/clearing
  - Voice wake word, transcript, intent, response simulation
- Enabled automatically when not on Raspberry Pi

### 14. Treatments Logging
- Logs insulin treatments to Nightscout API
- Event types: Meal Bolus, Correction Bolus
- Supports carbs, glucose values, and notes
- Device-aware logging with unique device ID

### 15. Multi-Device Sync
- Unique device ID per installation
- Treatment synchronization across devices
- Auto-creates local insulin timers from remote treatments
- 30-second sync loop

---

## Data Storage

| Location | Purpose |
|----------|---------|
| `server/data/settings.json` | Global settings |
| `server/data/contacts.json` | Emergency contacts |
| `server/data/cache/historical_data.json` | 90-day glucose history cache |
| `~/.diabeetech/saved_login.json` | Auth credentials |
| `~/.glucocom/device_id.json` | Device identity |
| `~/.glucocom/insulin_timer_state_multi.json` | Insulin timer persistence |

---

## Platform Support

| Platform | Capabilities |
|----------|-------------|
| Raspberry Pi (ARM) | Full features: voice, audio alerts, touchscreen, GPIO |
| macOS | Development mode: audio via afplay, no GPIO |
| Linux (x86) | Audio via aplay, no GPIO |
| Browser | Chrome, Safari, Firefox (touchscreen optimized) |
