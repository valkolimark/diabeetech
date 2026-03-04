# Changelog

All notable changes to the Diabeetech Web Application will be documented in this file.

## [1.1.0] - 2026-03-03

### Added
- **WiFi Connect Screen**: Full-screen overlay that auto-appears when no internet is detected. Scans for available WiFi networks, allows password entry via virtual keyboard, and connects. Includes scanning, network list, password, connecting, success, and failure views with smooth transitions. Uses `nmcli` on Raspberry Pi, simulated networks in dev mode.
- **WiFi status polling**: `useWiFiStatus` hook polls `/api/wifi/status` every 10 seconds with optimistic defaults to avoid flash on startup.
- **WiFi backend service**: `WiFiService` class with `get_status()`, `scan_networks()`, and `connect()` methods. Dev mode simulation with `/dev/wifi/simulate` endpoint.
- **Hive Insights**: Renamed Clarity analytics to "Hive Insights" to avoid trademark conflicts. Uses standard Dexcom clinical thresholds (70-180 mg/dL) with a collapsible info notice explaining the threshold basis.

### Fixed
- **Alert countdown timer**: Countdown now broadcasts every 1 second instead of every 10 seconds, so the timer ticks smoothly after pressing "Address the Situation".
- **Simulation override**: Added `_sim_active_until` guard so real glucose polling doesn't override simulated alert states during testing.
- **Virtual keyboard z-index**: Keyboard now renders at z-[80] so it appears above the WiFi overlay (z-[70]).

### Changed
- **Graph zoom & pan**: Mousewheel zoom in/out on the glucose graph. Touch devices support pinch-to-zoom and single-finger pan. "Reset Zoom" button appears when zoomed. Adaptive tick intervals (hourly, 30-min, 15-min).
- **Graph styling**: X-axis shows clean hour markers ("1am", "2am"). Axis labels are white and semi-bold. Increased chart margins. Smaller dot radius (3px).
- **Compact layout**: Graph drawer opens full screen width instead of 55%.
- **Analytics periods**: Removed 14-day and 30-day periods (insufficient cached data), kept 3-day and 7-day.
- **Settings**: Removed Speaker Enrollment and About from settings navigation.

## [1.0.0] - Initial Release

### Features
- Real-time continuous glucose monitoring via Nightscout multi-tenant backend
- Color-coded glucose display with trend arrows and delta
- Recharts scatter plot with 2h/6h/12h/24h time range selector
- Audible alert system with Address the Situation / Problem Resolved flow
- Multi-user authentication (subdomain + email + password)
- Insulin timer tracking with concentric ring visualization
- 12 built-in themes with glucose state color tinting
- Clarity analytics (average glucose, GMI, time in range, CV)
- Voice system (Picovoice wake word + STT, Edge TTS)
- Virtual keyboard for touchscreen input
- Settings panel (thresholds, colors, contacts, WiFi, timezone)
- Multi-device sync for treatments
- Dev mode with simulation endpoints
