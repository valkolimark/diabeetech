"""
Auto-Announce Service — periodically speaks glucose reading aloud.
Reads settings for enabled state and interval.
"""
import asyncio
import logging
from typing import Optional, Callable

logger = logging.getLogger("diabeetech.auto_announce")

TREND_WORDS = {
    "DoubleUp": "rising fast",
    "SingleUp": "rising",
    "FortyFiveUp": "trending up",
    "Flat": "steady",
    "FortyFiveDown": "trending down",
    "SingleDown": "falling",
    "DoubleDown": "falling fast",
    "NOT COMPUTABLE": "",
    "RATE OUT OF RANGE": "",
    None: "",
}


class AutoAnnounceService:
    """Periodically announces glucose via TTS."""

    def __init__(self, get_state: Callable, speak_fn: Callable):
        self._get_state = get_state
        self._speak = speak_fn
        self._task: Optional[asyncio.Task] = None

    def start(self):
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())
        logger.info("Auto-announce service started")

    def stop(self):
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("Auto-announce service stopped")

    async def _loop(self):
        while True:
            try:
                state = self._get_state()
                settings = state.get("settings", {})
                enabled = settings.get("auto_announce_enabled", False)
                interval = settings.get("auto_announce_interval", 15)

                if enabled:
                    glucose = state.get("glucose_update")
                    if glucose and glucose.get("sgv"):
                        sgv = glucose["sgv"]
                        trend = glucose.get("trend", "")
                        trend_word = TREND_WORDS.get(trend, "")
                        msg = f"Your glucose is {sgv}"
                        if trend_word:
                            msg += f", {trend_word}"
                        msg += "."
                        logger.info(f"Auto-announce: {msg}")
                        self._speak(msg)

                    await asyncio.sleep(interval * 60)
                else:
                    # Check every 30s if it got enabled
                    await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-announce error: {e}")
                await asyncio.sleep(60)
