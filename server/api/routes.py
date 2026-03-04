"""
REST API endpoints for Diabeetech.
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("diabeetech.api")

router = APIRouter(prefix="/api")

DATA_DIR = Path(__file__).parent.parent / "data"


def _read_json(filename: str, default=None):
    """Read a JSON file from the data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return default if default is not None else {}


def _write_json(filename: str, data):
    """Write data to a JSON file in the data directory."""
    path = DATA_DIR / filename
    path.write_text(json.dumps(data, indent=2))


@router.get("/status")
async def get_status():
    """Current glucose, alert state, voice state, server health."""
    # Will be populated by glucose service later
    return {
        "status": "ok",
        "glucose": None,
        "alert": {"level": "normal", "pulsing": False, "addressed": False, "muted": False},
        "voice": {"state": "idle"},
        "connected_to_backend": False,
        "voice_engine_ready": False,
        "cgm_provider": None,
        "last_sync": None
    }


@router.get("/glucose/current")
async def get_current_glucose():
    """Latest glucose reading."""
    return {"sgv": None, "trend": None, "state": "no_data", "stale": True, "message": "Not connected"}


@router.get("/glucose/history")
async def get_glucose_history(hours: int = 2):
    """Historical glucose data."""
    if hours not in (2, 6, 12, 24):
        hours = 2
    return {"readings": [], "range_hours": hours}


@router.get("/timers")
async def get_timers():
    """Active insulin timers."""
    return {"timers": []}


@router.delete("/timers/{timer_id}")
async def delete_timer(timer_id: str):
    """Delete specific timer."""
    return {"deleted": timer_id}


@router.delete("/timers")
async def delete_all_timers():
    """Delete all timers."""
    return {"deleted": "all"}


@router.get("/settings")
async def get_settings():
    """Current settings."""
    return _read_json("settings.json")


@router.put("/settings")
async def update_settings(update: dict):
    """Update a setting."""
    settings = _read_json("settings.json")
    settings.update(update)
    _write_json("settings.json", settings)
    return settings


@router.get("/contacts")
async def get_contacts():
    """Emergency contacts list."""
    return _read_json("contacts.json", default=[])


@router.put("/contacts")
async def update_contacts(contacts: list):
    """Update emergency contacts."""
    _write_json("contacts.json", contacts)
    return contacts


@router.get("/auth/status")
async def auth_status():
    """Check authentication status."""
    from pathlib import Path
    import json
    login_path = Path.home() / ".diabeetech" / "saved_login.json"
    if login_path.exists():
        try:
            data = json.loads(login_path.read_text())
            return {
                "authenticated": bool(data.get("subdomain")),
                "subdomain": data.get("subdomain", ""),
                "email": data.get("email", ""),
            }
        except Exception:
            pass
    return {"authenticated": False, "subdomain": "", "email": ""}


@router.post("/auth/login")
async def auth_login(body: dict):
    """Login to Nightscout using AuthManager."""
    import hashlib
    import os
    from pathlib import Path
    from services.auth import AuthManager

    subdomain = body.get("subdomain", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "").strip()

    if not subdomain or not email:
        return {"success": False, "error": "Subdomain and email are required"}

    # Use AuthManager for proper JWT login
    auth = AuthManager()
    result = await auth.login(subdomain, email, password)

    if not result.get("success"):
        # Fallback: try with the API_SECRET from .env for api-secret header auth
        api_secret = os.getenv("API_SECRET", "")
        if api_secret:
            try:
                import aiohttp
                api_secret_hash = hashlib.sha1(api_secret.encode()).hexdigest()
                url = f"https://{subdomain}.diabeetech.net/api/v1/entries.json?count=1"
                headers = {"api-secret": api_secret_hash}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            login_path = Path.home() / ".diabeetech" / "saved_login.json"
                            login_path.parent.mkdir(parents=True, exist_ok=True)
                            login_path.write_text(json.dumps({
                                "subdomain": subdomain,
                                "email": email,
                                "token": None,
                                "tenant_id": None,
                                "user_id": None,
                            }, indent=2))
                            result = {"success": True, "subdomain": subdomain}
            except Exception as e:
                logger.error(f"API secret fallback failed: {e}")

    # Reinitialize all services with new credentials
    if result.get("success"):
        from main import reinit_services
        await reinit_services()

    return result


@router.post("/auth/logout")
async def auth_logout():
    """Clear saved login and reinitialize services."""
    from pathlib import Path
    login_path = Path.home() / ".diabeetech" / "saved_login.json"
    if login_path.exists():
        login_path.unlink()

    # Reinitialize services (will start without auth)
    from main import reinit_services
    await reinit_services()

    return {"success": True}


@router.get("/clarity/{period}")
async def get_clarity(period: int):
    """Clarity analytics for a given period (days)."""
    from services.clarity import get_clarity_stats
    if period not in (3, 7, 14, 30):
        period = 7
    settings = _read_json("settings.json")
    thresholds = {
        "threshold_high": settings.get("threshold_high", 300),
        "threshold_trending_high": settings.get("threshold_trending_high", 263),
        "threshold_trending_low": settings.get("threshold_trending_low", 120),
        "threshold_low": settings.get("threshold_low", 100),
    }
    return get_clarity_stats(period, thresholds)


@router.get("/profiles")
async def get_profiles():
    """List all user profiles."""
    from services.profiles import ProfileManager
    pm = ProfileManager()
    return {"profiles": pm.list_profiles(), "current": pm.get_current_profile()}


@router.get("/device/id")
async def get_device_id():
    """Get current device ID."""
    from services.device_sync import get_device_id
    return {"device_id": get_device_id()}


@router.get("/system/info")
async def get_system_info():
    """System information."""
    import platform
    import os
    from pathlib import Path

    IS_PI = platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
    DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or not IS_PI

    # Read subdomain from saved login
    subdomain = ""
    login_path = Path.home() / ".diabeetech" / "saved_login.json"
    if login_path.exists():
        try:
            import json
            data = json.loads(login_path.read_text())
            subdomain = data.get("subdomain", "")
        except Exception:
            pass

    return {
        "platform": f"{'Raspberry Pi' if IS_PI else platform.system()} ({platform.machine()})",
        "dev_mode": DEV_MODE,
        "subdomain": subdomain,
        "python_version": platform.python_version(),
    }
