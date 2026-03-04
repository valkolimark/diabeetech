"""
Alert orchestrator: sounds (aplay/afplay).

Sound Mapping:
  Normal / Recovery    → EL.wav   (plays once)
  Trending Low         → LN.wav   (every 8 seconds) + Address/Problem Resolved buttons
  Low                  → LN.wav   (every 5 seconds)  + Address/Problem Resolved buttons
  Urgent/Critical Low  → ULN.wav  (every 3 seconds)  + Address/Problem Resolved buttons
  High                 → HN.wav   (plays once)
  No Data              → ND.wav   (every 30 seconds)
"""
import asyncio
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, Callable, Awaitable

logger = logging.getLogger("diabeetech.alerts")

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

SOUNDS_DIR = Path(__file__).parent.parent / "sounds"


def play_sound(filepath: str):
    """Play a WAV file using the platform-appropriate command."""
    if DEV_MODE and os.getenv("DEV_SKIP_AUDIO", "false").lower() == "true":
        logger.info(f"[DEV] Would play sound: {filepath}")
        return

    system = platform.system()
    if system == "Linux":
        subprocess.Popen(["aplay", "-q", filepath])
    elif system == "Darwin":
        subprocess.Popen(["afplay", filepath])
    else:
        logger.warning(f"No audio player for platform: {system}")


class AlertService:
    def __init__(self, broadcast_callback: Callable[[str, dict], Awaitable[None]]):
        self.broadcast = broadcast_callback
        self._current_level = "normal"
        self._addressed = False
        self._muted = False
        self._countdown_remaining: Optional[int] = None
        self._sound_task: Optional[asyncio.Task] = None
        self._countdown_task: Optional[asyncio.Task] = None
        self._running = True

    def get_state(self) -> dict:
        return {
            "level": self._current_level,
            "pulsing": self._current_level in ("low", "urgent_low", "trending_low"),
            "addressed": self._addressed,
            "muted": self._muted,
            "countdown_remaining": self._countdown_remaining,
        }

    async def check_alert(self, glucose_state: str, sgv: Optional[int] = None):
        """Check alert conditions and trigger appropriate responses."""
        prev_level = self._current_level

        # Determine alert level
        if glucose_state == "low":
            if sgv is not None and sgv < 70:
                new_level = "urgent_low"
            else:
                new_level = "low"
        elif glucose_state == "trending_low":
            new_level = "trending_low"
        elif glucose_state == "trending_high":
            new_level = "trending_high"
        elif glucose_state == "high":
            new_level = "high"
        elif glucose_state == "no_data":
            new_level = "no_data"
        else:
            new_level = "normal"

        # --- Transitioning OUT of a low alert ---
        if new_level not in ("low", "urgent_low", "trending_low") and prev_level in ("low", "urgent_low", "trending_low"):
            self._stop_repeating_sounds()
            self._addressed = False
            self._muted = False
            self._countdown_remaining = None
            if self._countdown_task:
                self._countdown_task.cancel()
                self._countdown_task = None

        # --- Handle non-low states ---
        if new_level == "trending_high":
            if new_level != prev_level:
                self._current_level = "trending_high"
                self._stop_repeating_sounds()
                await self._broadcast_state()
            return

        if new_level == "normal":
            if new_level != prev_level:
                self._current_level = "normal"
                self._stop_repeating_sounds()
                # Play EL.wav once
                sound = SOUNDS_DIR / "EL.wav"
                if sound.exists():
                    play_sound(str(sound))
                await self._broadcast_state()
            return

        if new_level == "high":
            if new_level != prev_level:
                self._current_level = "high"
                self._stop_repeating_sounds()
                # Play HN.wav once
                sound = SOUNDS_DIR / "HN.wav"
                if sound.exists():
                    play_sound(str(sound))
                await self._broadcast_state()
            return

        if new_level == "no_data":
            if new_level != prev_level:
                self._current_level = "no_data"
                self._stop_repeating_sounds()
                # Play ND.wav every 30 seconds
                self._start_repeating_sound("ND.wav", interval=30)
                await self._broadcast_state()
            return

        # --- Low states: sounds + Address/Problem Resolved flow ---

        # If muted (Problem Resolved was pressed), don't re-trigger
        if self._muted:
            return

        # If addressed and countdown is running, don't re-trigger
        if self._addressed and self._countdown_remaining is not None and self._countdown_remaining > 0:
            if new_level != self._current_level:
                self._current_level = new_level
                await self._broadcast_state()
            return

        # Level changed or countdown expired → restart
        if new_level != prev_level or (self._addressed and self._countdown_remaining is not None and self._countdown_remaining <= 0):
            self._current_level = new_level
            self._addressed = False
            self._muted = False
            self._countdown_remaining = None
            self._stop_repeating_sounds()

            if new_level == "low":
                self._start_repeating_sound("LN.wav", interval=5)
            elif new_level == "urgent_low":
                self._start_repeating_sound("ULN.wav", interval=3)
            elif new_level == "trending_low":
                self._start_repeating_sound("LN.wav", interval=8)

            await self._broadcast_state()

    async def address_situation(self):
        """User pressed 'Address the Situation' — stop sound, start 5 min countdown."""
        self._addressed = True
        self._stop_repeating_sounds()
        self._countdown_remaining = 300  # 5 minutes

        if self._countdown_task:
            self._countdown_task.cancel()
        self._countdown_task = asyncio.create_task(self._run_countdown())

        await self._broadcast_state()

    async def problem_averted(self):
        """User pressed 'Problem Resolved' — stop everything."""
        self._muted = True
        self._stop_repeating_sounds()
        if self._countdown_task:
            self._countdown_task.cancel()
            self._countdown_task = None
        self._countdown_remaining = None
        await self._broadcast_state()

    async def _run_countdown(self):
        """5-minute countdown after 'Address the Situation'."""
        while self._countdown_remaining is not None and self._countdown_remaining > 0:
            await asyncio.sleep(1)
            self._countdown_remaining -= 1
            await self._broadcast_state()

        # Countdown expired — resume alerts if still in a low state
        if not self._muted and self._current_level in ("low", "urgent_low", "trending_low"):
            self._addressed = False
            self._countdown_remaining = None
            if self._current_level == "low":
                self._start_repeating_sound("LN.wav", interval=5)
            elif self._current_level == "urgent_low":
                self._start_repeating_sound("ULN.wav", interval=3)
            elif self._current_level == "trending_low":
                self._start_repeating_sound("LN.wav", interval=8)
            await self._broadcast_state()

    def _start_repeating_sound(self, filename: str, interval: int):
        """Start repeating a sound at the given interval."""
        self._stop_repeating_sounds()
        self._sound_task = asyncio.create_task(self._repeat_sound(filename, interval))

    def _stop_repeating_sounds(self):
        """Stop any repeating sound."""
        if self._sound_task:
            self._sound_task.cancel()
            self._sound_task = None

    async def _repeat_sound(self, filename: str, interval: int):
        """Play a sound on repeat at the given interval."""
        sound = SOUNDS_DIR / filename
        if not sound.exists():
            logger.warning(f"Sound file not found: {sound}")
            return
        while self._running:
            play_sound(str(sound))
            await asyncio.sleep(interval)

    async def _broadcast_state(self):
        """Broadcast current alert state to all WebSocket clients."""
        await self.broadcast("alert_state", self.get_state())

    def stop(self):
        self._running = False
        self._stop_repeating_sounds()
        if self._countdown_task:
            self._countdown_task.cancel()
