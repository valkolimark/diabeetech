# Changelog

All notable changes to the Diabeetech Web Application will be documented in this file.

## [1.0.1] - 2026-03-03

### Fixed
- **Alert countdown timer**: Countdown now broadcasts every 1 second instead of every 10 seconds, so the timer ticks smoothly after pressing "Address the Situation" instead of appearing stalled.

### Added
- **Graph zoom & pan**: Users can now mousewheel to zoom in/out on the glucose graph time axis. Touch devices support pinch-to-zoom and single-finger pan when zoomed. A "Reset Zoom" button appears when zoomed in.
- **Adaptive tick intervals**: When zoomed in past 2 hours the graph shows 30-minute ticks; past 1 hour it shows 15-minute ticks.

### Changed
- **Graph X-axis labels**: Time labels now display as clean hour markers ("1am", "2am", "3am") using explicit hour-boundary tick positions instead of auto-generated ticks at arbitrary times.
- **Graph axis fonts**: X and Y axis labels are now white and semi-bold (previously faint at 40% opacity).
- **Graph padding**: Increased chart margins and Y-axis width so labels are not pressed against the edges.

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
