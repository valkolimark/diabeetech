"""
Diabeetech Web — FastAPI Server
Serves Next.js static export + WebSocket + REST API + Voice Pipeline + CGM Sync
"""
import asyncio
import json
import os
import platform
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router as api_router
from api.websocket import ws_manager
from services.auth import AuthManager
from services.glucose import GlucoseService
from services.alerts import AlertService
from services.timers import TimerService
from services.treatments import TreatmentsService
from services.auto_announce import AutoAnnounceService

# Load environment
load_dotenv()

# Platform detection
IS_PI = platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or not IS_PI

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("diabeetech")

# App
app = FastAPI(title="Diabeetech", version="1.0.0")

# Include REST API routes
app.include_router(api_router)

# --- Current application state (shared by all components) ---
app_state = {
    "glucose_update": None,
    "alert_state": {
        "level": "normal",
        "pulsing": False,
        "addressed": False,
        "muted": False,
        "countdown_remaining": None
    },
    "voice_state": {
        "state": "idle",
        "amplitude": None,
        "wake_word": None
    },
    "timer_update": {"timers": []},
    "settings": None,
    "server_status": {
        "connected_to_backend": False,
        "voice_engine_ready": False,
        "cgm_provider": None,
        "last_sync": None
    }
}


def load_settings():
    """Load settings from data/settings.json."""
    settings_path = Path(__file__).parent / "data" / "settings.json"
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text())
            app_state["settings"] = {
                "display_name": data.get("display_name", ""),
                "display_mode": data.get("display_mode", "big"),
                "threshold_low": data.get("threshold_low", 100),
                "threshold_trending_low": data.get("threshold_trending_low", 120),
                "threshold_trending_high": data.get("threshold_trending_high", 263),
                "threshold_high": data.get("threshold_high", 300),
                "low_color": data.get("low_color", "#FF0000"),
                "trending_low_color": data.get("trending_low_color", "#FFD700"),
                "normal_color": data.get("normal_color", "#00FF00"),
                "trending_high_color": data.get("trending_high_color", "#FF8C00"),
                "high_color": data.get("high_color", "#e100ff"),
                "wake_word": data.get("wake_word", ""),
                "tts_voice": data.get("tts_voice", "en-US-JennyNeural"),
                "timezone": data.get("timezone", "America/Chicago"),
                "auto_announce_enabled": data.get("auto_announce_enabled", False),
                "auto_announce_interval": data.get("auto_announce_interval", 15),
                "theme": data.get("theme", ""),
            }
        except Exception as e:
            logger.error(f"Error loading settings: {e}")


# --- WebSocket endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Wait for ui_ready message, then send full state
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type")

            if msg_type == "ui_ready":
                logger.info("Browser sent ui_ready — sending full state")
                await ws_manager.send_full_state(websocket, app_state)

            elif msg_type == "touch_command":
                action = message.get("action")
                payload = message.get("payload", {})
                await handle_touch_command(action, payload)

            elif msg_type == "request":
                action = message.get("action")
                payload = message.get("payload", {})
                await handle_request(websocket, action, payload)

            elif msg_type == "system":
                action = message.get("action")
                if action == "shutdown":
                    logger.info("Shutdown requested from browser")
                    if IS_PI:
                        import subprocess
                        subprocess.Popen(["sudo", "shutdown", "-h", "now"])
                    else:
                        logger.info("DEV_MODE: shutdown command ignored (not on Pi)")

            elif msg_type == "settings_update":
                key = message.get("key")
                value = message.get("value")
                if key and app_state["settings"]:
                    app_state["settings"][key] = value
                    # Save to disk
                    settings_path = Path(__file__).parent / "data" / "settings.json"
                    try:
                        all_settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
                        all_settings[key] = value
                        settings_path.write_text(json.dumps(all_settings, indent=2))
                    except Exception as e:
                        logger.error(f"Error saving setting {key}: {e}")
                    await ws_manager.broadcast("settings", app_state["settings"])

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


async def handle_touch_command(action: str, payload: dict):
    """Handle touch commands from the browser."""
    if action == "address_situation":
        if alert_service:
            await alert_service.address_situation()
        app_state["alert_state"]["addressed"] = True
        await ws_manager.broadcast("alert_state", app_state.get("alert_state", {}))
    elif action == "problem_averted":
        if alert_service:
            await alert_service.problem_averted()
        app_state["alert_state"]["muted"] = True
        await ws_manager.broadcast("alert_state", app_state.get("alert_state", {}))
    elif action == "delete_timer":
        timer_id = payload.get("timer_id")
        if timer_id and timer_service:
            timer_service.remove_timer(timer_id)
            app_state["timer_update"] = timer_service.get_timer_data()
            await ws_manager.broadcast("timer_update", app_state["timer_update"])
    elif action == "delete_all_timers":
        if timer_service:
            timer_service.remove_all_timers()
        app_state["timer_update"] = {"timers": []}
        await ws_manager.broadcast("timer_update", app_state["timer_update"])


async def handle_request(websocket: WebSocket, action: str, payload: dict):
    """Handle data requests from the browser."""
    if action == "settings":
        if app_state["settings"]:
            await ws_manager.send_event(websocket, "settings", app_state["settings"])
    elif action == "timers":
        await ws_manager.send_event(websocket, "timer_update", app_state["timer_update"])
    elif action == "status":
        await ws_manager.send_event(websocket, "server_status", app_state["server_status"])
    elif action == "glucose_history":
        range_hours = payload.get("range_hours", 2)
        if glucose_service:
            readings = glucose_service.get_history_for_range(range_hours)
        else:
            readings = []
        await ws_manager.send_event(websocket, "glucose_history", {
            "readings": readings,
            "range_hours": range_hours
        })


# --- DEV_MODE simulation endpoints ---

if DEV_MODE:
    from fastapi import APIRouter
    dev_router = APIRouter(prefix="/dev", tags=["dev"])

    @dev_router.post("/voice/wake")
    async def dev_voice_wake():
        app_state["voice_state"] = {"state": "listening", "amplitude": None, "wake_word": "Hey Buzz"}
        await ws_manager.broadcast("voice_state", app_state["voice_state"])
        return {"ok": True}

    @dev_router.post("/voice/transcript")
    async def dev_voice_transcript(body: dict):
        await ws_manager.broadcast("voice_transcript", {
            "text": body.get("text", ""),
            "is_final": body.get("is_final", True),
            "intent": body.get("intent"),
            "confidence": body.get("confidence")
        })
        return {"ok": True}

    @dev_router.post("/voice/intent")
    async def dev_voice_intent(body: dict):
        await ws_manager.broadcast("voice_transcript", {
            "text": "",
            "is_final": True,
            "intent": body.get("intent", "glucose_query"),
            "confidence": body.get("confidence", 0.95)
        })
        return {"ok": True}

    @dev_router.post("/voice/response")
    async def dev_voice_response(body: dict):
        await ws_manager.broadcast("voice_response", {
            "text": body.get("text", ""),
            "category": body.get("category", "general")
        })
        return {"ok": True}

    @dev_router.post("/voice/state")
    async def dev_voice_state(body: dict):
        state = body.get("state", "idle")
        app_state["voice_state"]["state"] = state
        await ws_manager.broadcast("voice_state", app_state["voice_state"])
        return {"ok": True}

    @dev_router.post("/glucose/simulate")
    async def dev_glucose_simulate(body: dict):
        import time as _time
        global _sim_active_until
        # Hold simulation for 60s — prevents real polling from overriding alerts
        _sim_active_until = _time.time() + 60
        sgv = body.get("sgv", 150)
        trend = body.get("trend", "Flat")
        state = "normal"
        settings = app_state.get("settings") or {}
        th_low = settings.get("threshold_low", 100)
        th_tl = settings.get("threshold_trending_low", 120)
        th_th = settings.get("threshold_trending_high", 263)
        th_high = settings.get("threshold_high", 300)
        if sgv < th_low:
            state = "low"
        elif sgv < th_tl:
            state = "trending_low"
        elif sgv > th_high:
            state = "high"
        elif sgv > th_th:
            state = "trending_high"
        # Color from settings
        color_map = {
            "low": settings.get("low_color", "#FF0000"),
            "trending_low": settings.get("trending_low_color", "#FFD700"),
            "normal": settings.get("normal_color", "#00FF00"),
            "trending_high": settings.get("trending_high_color", "#FF8C00"),
            "high": settings.get("high_color", "#e100ff"),
        }
        color = color_map.get(state, "#404040")
        delta = body.get("delta", 0)
        from datetime import datetime
        glucose_data = {
            "sgv": sgv,
            "trend": trend,
            "direction": trend,
            "delta": delta,
            "state": state,
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "stale": False,
            "stale_minutes": 0,
            "message": f"{sgv} mg/dL",
        }
        app_state["glucose_update"] = glucose_data
        await ws_manager.broadcast("glucose_update", glucose_data)
        # Trigger alert sounds
        if alert_service:
            await alert_service.check_alert(state, sgv)
            app_state["alert_state"] = alert_service.get_state()
        return {"ok": True, "state": state}

    @dev_router.post("/alert/simulate")
    async def dev_alert_simulate(body: dict):
        import time as _time
        global _sim_active_until
        _sim_active_until = _time.time() + 60
        level = body.get("level", "low")
        # Map level to glucose state and sgv for the alert service
        level_to_state = {
            "low": ("low", 80),
            "urgent_low": ("low", 55),
            "trending_low": ("trending_low", 115),
            "high": ("high", 320),
            "trending_high": ("trending_high", 270),
            "no_data": ("no_data", None),
            "normal": ("normal", 150),
        }
        glucose_state, sgv = level_to_state.get(level, ("normal", 150))
        if alert_service:
            # Reset alert state so the level change is detected
            alert_service._current_level = "___reset___"
            alert_service._addressed = False
            alert_service._muted = False
            await alert_service.check_alert(glucose_state, sgv)
            app_state["alert_state"] = alert_service.get_state()
        else:
            app_state["alert_state"] = {
                "level": level,
                "pulsing": level in ("low", "urgent_low"),
                "addressed": False,
                "muted": False,
                "countdown_remaining": None,
            }
            await ws_manager.broadcast("alert_state", app_state["alert_state"])
        return {"ok": True}

    @dev_router.post("/timer/clear")
    async def dev_timer_clear():
        app_state["timer_update"]["timers"] = []
        await ws_manager.broadcast("timer_update", app_state["timer_update"])
        return {"ok": True}

    @dev_router.post("/timer/simulate")
    async def dev_timer_simulate(body: dict):
        import uuid
        timer = {
            "id": str(uuid.uuid4())[:8],
            "insulin_type": body.get("type", "novolog"),
            "units": body.get("units", 5),
            "start_time": "2026-02-28T12:00:00Z",
            "elapsed_seconds": 0,
            "total_seconds": 14400,
            "phase": "active",
            "phase_color": "#3b82f6",
            "progress": 0.0
        }
        app_state["timer_update"]["timers"].append(timer)
        await ws_manager.broadcast("timer_update", app_state["timer_update"])
        return {"ok": True, "timer_id": timer["id"]}

    @dev_router.post("/wifi/simulate")
    async def dev_wifi_simulate(body: dict):
        """Toggle simulated WiFi/internet state for development."""
        from services.wifi import WiFiService
        svc = WiFiService()
        has_internet = body.get("has_internet", True)
        svc.set_dev_state(has_internet)
        return {"ok": True, "has_internet": has_internet}

    app.include_router(dev_router)
    logger.info("DEV_MODE: Simulation endpoints enabled at /dev/*")


# --- Services (initialized at startup) ---
auth_manager: AuthManager = None
glucose_service: GlucoseService = None
alert_service: AlertService = None
timer_service: TimerService = None
treatments_service: TreatmentsService = None
auto_announce_service: AutoAnnounceService = None
_glucose_poll_task: asyncio.Task = None
_sim_active_until: float = 0  # timestamp when simulation mode expires


# --- Startup/Shutdown ---

@app.on_event("startup")
async def startup():
    global auth_manager, glucose_service, alert_service, timer_service, treatments_service, auto_announce_service

    logger.info(f"Diabeetech Server starting (DEV_MODE={DEV_MODE}, Platform={platform.system()})")
    load_settings()
    logger.info("Settings loaded")

    # Initialize auth manager
    auth_manager = AuthManager()
    # Try JWT login if we have credentials but no token
    if auth_manager.subdomain and not auth_manager.token:
        auth_manager.ensure_jwt_login()
    if auth_manager.is_authenticated():
        logger.info(f"Authenticated as {auth_manager.get_subdomain()} (token={'yes' if auth_manager.token else 'no'})")
        app_state["server_status"]["connected_to_backend"] = True
    else:
        logger.warning("Not authenticated — CGM sync will not start")

    # Initialize alert service
    alert_service = AlertService(ws_manager.broadcast)
    app_state["alert_state"] = alert_service.get_state()

    # Initialize glucose service and start polling
    if app_state["settings"] and auth_manager.is_authenticated():
        glucose_service = GlucoseService(auth_manager, app_state["settings"])

        async def glucose_broadcast(event_type: str, data: dict):
            import time as _time
            app_state["glucose_update"] = data
            await ws_manager.broadcast(event_type, data)
            # Skip alert check while simulation is active
            if _sim_active_until > _time.time():
                return
            if alert_service and data.get("state"):
                await alert_service.check_alert(data["state"], data.get("sgv"))

        global _glucose_poll_task
        _glucose_poll_task = asyncio.create_task(glucose_service.start_polling(glucose_broadcast))
        app_state["server_status"]["last_sync"] = datetime.now().isoformat()
        logger.info("CGM polling started")

    # Initialize timer service
    timer_service = TimerService(ws_manager.broadcast)
    app_state["timer_update"] = timer_service.get_timer_data()
    asyncio.create_task(timer_service.start_updates())
    logger.info("Timer service started")

    # Initialize treatments service
    if auth_manager.is_authenticated():
        treatments_service = TreatmentsService(auth_manager)
        logger.info("Treatments service initialized")

    # Initialize auto-announce service
    from voice.tts import speak
    auto_announce_service = AutoAnnounceService(
        get_state=lambda: app_state,
        speak_fn=speak,
    )
    auto_announce_service.start()
    logger.info("Auto-announce service started")


async def reinit_services():
    """Reinitialize all services with current auth state. Called after login/logout."""
    global auth_manager, glucose_service, alert_service, timer_service, treatments_service, auto_announce_service, _glucose_poll_task

    # Stop existing services — cancel the polling task first
    if _glucose_poll_task and not _glucose_poll_task.done():
        _glucose_poll_task.cancel()
        _glucose_poll_task = None
        logger.info("Cancelled glucose polling task")
    if glucose_service:
        glucose_service.stop()
        glucose_service = None
    if alert_service:
        alert_service.stop()
    if timer_service:
        timer_service.stop()
    if auto_announce_service:
        auto_announce_service.stop()

    # Clear old user's cached data and app state
    from services.glucose import HISTORY_CACHE
    if HISTORY_CACHE.exists():
        HISTORY_CACHE.unlink()
        logger.info("Cleared glucose history cache for user switch")
    app_state["glucose_update"] = {}
    app_state["history"] = []

    # Reload settings
    load_settings()

    # Reinitialize auth manager with fresh credentials
    auth_manager = AuthManager()
    if auth_manager.subdomain and not auth_manager.token:
        auth_manager.ensure_jwt_login()

    if auth_manager.is_authenticated():
        logger.info(f"Re-authenticated as {auth_manager.get_subdomain()}")
        app_state["server_status"]["connected_to_backend"] = True
        # Update display name to match the logged-in user
        subdomain = auth_manager.get_subdomain()
        if subdomain and app_state.get("settings"):
            display_name = subdomain.capitalize()
            app_state["settings"]["display_name"] = display_name
            # Persist to settings.json
            settings_path = Path(__file__).parent / "data" / "settings.json"
            try:
                settings_data = json.loads(settings_path.read_text())
                settings_data["display_name"] = display_name
                settings_path.write_text(json.dumps(settings_data, indent=2))
            except Exception:
                pass
            logger.info(f"Display name set to: {display_name}")
            # Broadcast updated settings to frontend
            await ws_manager.broadcast("settings", app_state["settings"])
    else:
        logger.warning("Not authenticated after reinit")
        app_state["server_status"]["connected_to_backend"] = False

    # Reinitialize alert service
    alert_service = AlertService(ws_manager.broadcast)
    app_state["alert_state"] = alert_service.get_state()

    # Reinitialize glucose service
    logger.info(f"Reinit check: settings={bool(app_state.get('settings'))}, authenticated={auth_manager.is_authenticated()}, subdomain={auth_manager.get_subdomain()}, base_url={auth_manager.get_base_url()}")
    if app_state["settings"] and auth_manager.is_authenticated():
        glucose_service = GlucoseService(auth_manager, app_state["settings"])

        async def glucose_broadcast(event_type: str, data: dict):
            import time as _time
            app_state["glucose_update"] = data
            await ws_manager.broadcast(event_type, data)
            # Skip alert check while simulation is active
            if _sim_active_until > _time.time():
                return
            if alert_service and data.get("state"):
                await alert_service.check_alert(data["state"], data.get("sgv"))

        _glucose_poll_task = asyncio.create_task(glucose_service.start_polling(glucose_broadcast))
        logger.info("CGM polling restarted")
    else:
        # Clear glucose state
        app_state["glucose_update"] = {}
        await ws_manager.broadcast("glucose_update", {})

    # Broadcast cleared history to all clients
    await ws_manager.broadcast("glucose_history", {"readings": [], "range_hours": 2})

    # Reinitialize timer service
    timer_service = TimerService(ws_manager.broadcast)
    app_state["timer_update"] = timer_service.get_timer_data()
    asyncio.create_task(timer_service.start_updates())

    # Reinitialize treatments service
    if auth_manager.is_authenticated():
        treatments_service = TreatmentsService(auth_manager)
    else:
        treatments_service = None

    # Reinitialize auto-announce service
    from voice.tts import speak
    auto_announce_service = AutoAnnounceService(
        get_state=lambda: app_state,
        speak_fn=speak,
    )
    auto_announce_service.start()

    logger.info("All services reinitialized")


@app.on_event("shutdown")
async def shutdown():
    global glucose_service, alert_service, timer_service
    logger.info("Diabeetech Server shutting down")
    if glucose_service:
        glucose_service.stop()
    if alert_service:
        alert_service.stop()
    if timer_service:
        timer_service.stop()
    if auto_announce_service:
        auto_announce_service.stop()


# --- Static frontend serving (must be LAST route) ---

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve the Next.js static export. Falls back to index.html for SPA routing."""
    if not STATIC_DIR.exists():
        return {"error": "Frontend not built. Run: cd frontend && npm run build, then cp -r out ../server/static"}

    # Try exact file
    file_path = STATIC_DIR / path
    if file_path.is_file():
        return FileResponse(file_path)

    # Try with index.html (Next.js trailing slash)
    index_path = STATIC_DIR / path / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)

    # Fallback to root index.html
    root_index = STATIC_DIR / "index.html"
    if root_index.is_file():
        return FileResponse(root_index)

    return {"error": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
