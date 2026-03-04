# Diabeetech Web — Session Continuation Prompt

Copy and paste everything below the line into a new Claude Code session to continue work.

---

## Project Context

I'm building **Diabeetech**, a real-time continuous glucose monitoring (CGM) display system. It has a **FastAPI Python backend** (`server/`) and a **Next.js React frontend** (`frontend/`). The frontend is built as a static export and served from `server/static/`.

**Read the full app overview first:** `DIABEETECH_APP_OVERVIEW.md` in the project root.

### Key Paths

- **Backend entry point:** `server/main.py`
- **API routes:** `server/api/routes.py`
- **Services:** `server/services/` (glucose.py, alerts.py, auth.py, clarity.py, device_sync.py, profiles.py, treatments.py, timer.py, auto_announce.py, voice.py)
- **WebSocket manager:** `server/ws.py`
- **Frontend components:** `frontend/components/`
- **Frontend providers/hooks:** `frontend/providers.tsx`, `frontend/hooks/`
- **Settings file:** `server/data/settings.json`
- **Saved login:** `~/.diabeetech/saved_login.json`
- **Sound files:** `server/sounds/` (EL.wav, LN.wav, ULN.wav, HN.wav, ND.wav)
- **Static frontend build:** `server/static/` (generated from `frontend/out/`)

### Building & Running

```bash
# Start the backend (from server/ directory)
cd server && python3 main.py
# Server runs on port 8080

# Build frontend (from frontend/ directory)
cd frontend && npx next build
# Then copy to server
cp -r out/* ../server/static/

# Dev simulation endpoints (dev mode auto-enabled on non-Pi)
curl -X POST http://localhost:8080/dev/glucose/simulate -H "Content-Type: application/json" -d '{"sgv": 150}'
curl -X POST http://localhost:8080/dev/timer/simulate -H "Content-Type: application/json" -d '{"type":"novolog","units":5}'
curl -X POST http://localhost:8080/dev/alert/simulate -H "Content-Type: application/json" -d '{"level":"normal"}'
```

### Test Credentials

- **jordan.diabeetech.net** / jordan@p5400.com / Camzack23
- **arimarco.diabeetech.net** / ari@p5400.com / CamZack23!
- **API_SECRET** (in .env): GodIsSoGood2Me23!

### Current Settings

- Thresholds: low=63, trending_low=100, trending_high=263, high=300
- Display mode: "big" (50/50 horizontal split)
- Theme: "Theme 11" (Forest Echo)

### Architecture Notes

- Frontend connects to backend via WebSocket for real-time updates
- Backend polls Nightscout every 30 seconds for new CGM readings
- Background sync every 5 minutes for historical data
- `reinit_services()` in main.py handles full service restart on user switch (stops polling, clears cache, reinits auth, restarts all services, broadcasts cleared state)
- Sound playback uses `afplay` on macOS, `aplay` on Linux/Pi
- Alert states: normal, trending_low, low, urgent_low, high, trending_high, no_data
- `trending_high` is silent (no sound, no action buttons)

### Recently Completed Work

1. Fixed trending_high alert bug (was incorrectly playing EL.wav sound)
2. Added logout button to Settings sidebar
3. Created branded Diabeetech landing screen with animated logo and Sign In flow
4. Overhauled virtual keyboard (numbers, symbols, domain shortcuts, Hide button)
5. Fixed login auth to use JWT via AuthManager (not raw password as API secret)
6. Implemented multi-user switching with full service reinitialization
7. Fixed display name and graph data updating on user switch

### Pending/Planned Work

- **Concentric ring insulin timers** — Plan exists at `.claude/plans/stateless-tinkering-gem.md`. Redesign insulin timer widget to show multiple timers as concentric rings in a single SVG instead of separate stacked widgets.
- Voice system integration (Picovoice wake word + STT, Edge TTS)
- Emergency contact SMS alerts
- WiFi management (Raspberry Pi only)
- Speaker enrollment (Picovoice Eagle)

### Known Issues

- onepanman.diabeetech.net has MongoDB TypeMismatch errors on the Nightscout backend (not our code issue)
- macOS requires `python3` (not `python`)
