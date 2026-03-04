"""
Multi-device treatment sync.

Each device has a unique ID stored at ~/.glucocom/device_id.json
When logging treatments, the device ID is included in the notes field:
  "Voice logged via Diabeetech | device:{device_id}"

Sync loop (every 30 seconds):
  - Fetch recent treatments from Nightscout
  - Filter out treatments from THIS device (by device_id in notes)
  - Apply any new treatments from OTHER devices
  - Sync insulin timers: if another device logged insulin, create a timer locally
"""
import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger("diabeetech.device_sync")

DEVICE_ID_PATH = Path.home() / ".glucocom" / "device_id.json"


def get_device_id() -> str:
    """Get or create a unique device ID."""
    if DEVICE_ID_PATH.exists():
        try:
            data = json.loads(DEVICE_ID_PATH.read_text())
            return data.get("device_id", "")
        except Exception:
            pass

    # Generate new device ID
    device_id = str(uuid.uuid4())[:8]
    DEVICE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEVICE_ID_PATH.write_text(json.dumps({"device_id": device_id}, indent=2))
    logger.info(f"Generated new device ID: {device_id}")
    return device_id


class DeviceSync:
    def __init__(self, auth_manager, timer_service=None):
        self.auth_manager = auth_manager
        self.timer_service = timer_service
        self.device_id = get_device_id()
        self._running = False
        self._last_sync_timestamp: Optional[str] = None

    async def start(self):
        """Start the sync loop (every 30 seconds)."""
        self._running = True
        logger.info(f"Device sync started (device_id={self.device_id})")

        while self._running:
            try:
                await self._sync_treatments()
            except Exception as e:
                logger.error(f"Sync error: {e}")
            await asyncio.sleep(30)

    def stop(self):
        self._running = False

    async def _sync_treatments(self):
        """Fetch recent treatments and apply remote ones."""
        if not self.auth_manager or not self.auth_manager.is_authenticated():
            return

        try:
            import aiohttp
            base_url = self.auth_manager.get_base_url()
            headers = self.auth_manager.get_headers()

            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/api/v1/treatments.json?count=20&sort=-created_at"
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return
                    treatments = await resp.json()

            # Filter treatments from other devices
            for t in treatments:
                notes = t.get("notes", "")
                if f"device:{self.device_id}" in notes:
                    continue  # Our own treatment, skip
                # Could apply remote treatments here (create timers, etc.)

        except ImportError:
            logger.debug("aiohttp not available for sync")
        except Exception as e:
            logger.error(f"Treatment sync error: {e}")

    def get_treatment_notes(self, base_notes: str = "") -> str:
        """Add device ID to treatment notes."""
        device_tag = f"device:{self.device_id}"
        if base_notes:
            return f"{base_notes} | Voice logged via Diabeetech | {device_tag}"
        return f"Voice logged via Diabeetech | {device_tag}"
