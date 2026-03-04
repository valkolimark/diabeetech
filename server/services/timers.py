"""
Insulin timer management + persistence.

Timer phases:
  ACTIVE (0-30 min):   Blue (#007AFF)
  PEAK   (30-150 min): Green (#34C759)
  WANING (150+ min):   Orange→Red gradient
  EXPIRED:             Timer removed

Default duration: 240 minutes (4 hours)
Peak time: 120 minutes
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Callable, Awaitable

logger = logging.getLogger("diabeetech.timers")

STATE_DIR = Path.home() / ".glucocom"
STATE_FILE = STATE_DIR / "insulin_timer_state_multi.json"

DEFAULT_DURATION_MINUTES = 240
DEFAULT_PEAK_MINUTES = 120


class InsulinTimer:
    def __init__(self, insulin_type: str, units: float,
                 duration_minutes: int = DEFAULT_DURATION_MINUTES,
                 peak_minutes: int = DEFAULT_PEAK_MINUTES,
                 is_correction: bool = False,
                 administered_at: Optional[datetime] = None,
                 timer_id: Optional[str] = None):
        self.id = timer_id or f"timer_{int(datetime.now().timestamp())}"
        self.insulin_type = insulin_type
        self.units = units
        self.duration_minutes = duration_minutes
        self.peak_minutes = peak_minutes
        self.is_correction = is_correction
        self.administered_at = administered_at or datetime.now()

    @property
    def total_seconds(self) -> int:
        return self.duration_minutes * 60

    @property
    def elapsed_seconds(self) -> float:
        return (datetime.now() - self.administered_at).total_seconds()

    @property
    def remaining_seconds(self) -> float:
        return max(0, self.total_seconds - self.elapsed_seconds)

    @property
    def progress(self) -> float:
        """0.0 = just started, 1.0 = expired."""
        return min(1.0, self.elapsed_seconds / self.total_seconds)

    @property
    def expired(self) -> bool:
        return self.elapsed_seconds >= self.total_seconds

    @property
    def phase(self) -> str:
        elapsed_min = self.elapsed_seconds / 60
        if self.expired:
            return "expired"
        if elapsed_min < 30:
            return "active"
        if elapsed_min < 150:
            return "peak"
        return "waning"

    @property
    def phase_color(self) -> str:
        phase = self.phase
        if phase == "active":
            return "#007AFF" if not self.is_correction else "#9333EA"
        elif phase == "peak":
            return "#34C759" if not self.is_correction else "#A855F7"
        elif phase == "waning":
            # Gradient from orange to red
            remaining_ratio = self.remaining_seconds / (self.total_seconds * 0.3)
            remaining_ratio = max(0, min(1, remaining_ratio))
            g = int(149 * remaining_ratio)
            return f"#FF{g:02X}00" if not self.is_correction else f"#DB{int(39+112*remaining_ratio):02X}{int(116+131*remaining_ratio):02X}"
        return "#404040"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "insulin_type": self.insulin_type,
            "units": self.units,
            "start_time": self.administered_at.isoformat(),
            "elapsed_seconds": int(self.elapsed_seconds),
            "total_seconds": self.total_seconds,
            "phase": self.phase,
            "phase_color": self.phase_color,
            "progress": round(self.progress, 4),
            "is_correction": self.is_correction,
        }

    def to_save_dict(self) -> dict:
        return {
            "id": self.id,
            "insulin_type": self.insulin_type,
            "units": self.units,
            "duration_minutes": self.duration_minutes,
            "peak_minutes": self.peak_minutes,
            "administered_at": self.administered_at.isoformat(),
            "is_correction": self.is_correction,
        }

    @classmethod
    def from_save_dict(cls, data: dict) -> 'InsulinTimer':
        return cls(
            insulin_type=data.get("insulin_type", "Unknown"),
            units=data.get("units", 0),
            duration_minutes=data.get("duration_minutes", DEFAULT_DURATION_MINUTES),
            peak_minutes=data.get("peak_minutes", DEFAULT_PEAK_MINUTES),
            is_correction=data.get("is_correction", False),
            administered_at=datetime.fromisoformat(data["administered_at"]),
            timer_id=data.get("id"),
        )


class TimerService:
    def __init__(self, broadcast_callback: Callable[[str, dict], Awaitable[None]]):
        self.broadcast = broadcast_callback
        self.timers: List[InsulinTimer] = []
        self._running = False
        self._update_task: Optional[asyncio.Task] = None

        # Load persisted timers
        self._load_state()

    def _load_state(self):
        """Load persisted timer state."""
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text())
            timers_data = data.get("timers", {})
            for timer_data in timers_data.values():
                timer = InsulinTimer.from_save_dict(timer_data)
                if not timer.expired:
                    self.timers.append(timer)

            if self.timers:
                logger.info(f"Recovered {len(self.timers)} active insulin timers")
            else:
                # Clean up state file if no active timers
                STATE_FILE.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error loading timer state: {e}")

    def _save_state(self):
        """Persist timer state."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        timers_dict = {}
        primary_id = None
        for timer in self.timers:
            timers_dict[timer.id] = timer.to_save_dict()
            if not timer.is_correction and primary_id is None:
                primary_id = timer.id

        data = {
            "timers": timers_dict,
            "primary_timer_id": primary_id,
        }
        STATE_FILE.write_text(json.dumps(data, indent=2))

    def add_timer(self, insulin_type: str, units: float,
                  is_correction: bool = False) -> InsulinTimer:
        """Create and add a new insulin timer."""
        # Auto-detect correction: if there's already a primary timer, new one is correction
        if self.timers and not is_correction:
            has_primary = any(not t.is_correction for t in self.timers)
            if has_primary:
                is_correction = True

        timer = InsulinTimer(
            insulin_type=insulin_type,
            units=units,
            is_correction=is_correction,
        )
        self.timers.append(timer)
        self._save_state()
        logger.info(f"Timer added: {units} units of {insulin_type} ({'correction' if is_correction else 'primary'})")
        return timer

    def remove_timer(self, timer_id: str) -> bool:
        """Remove a specific timer."""
        before = len(self.timers)
        self.timers = [t for t in self.timers if t.id != timer_id]
        if len(self.timers) < before:
            self._save_state()
            return True
        return False

    def remove_all_timers(self):
        """Remove all timers."""
        self.timers.clear()
        STATE_FILE.unlink(missing_ok=True)
        logger.info("All timers removed")

    def get_timer_data(self) -> dict:
        """Get current timer state for WebSocket broadcast."""
        # Remove expired timers
        self.timers = [t for t in self.timers if not t.expired]
        return {"timers": [t.to_dict() for t in self.timers]}

    def calculate_iob(self) -> float:
        """Calculate total Insulin On Board (linear decay over duration)."""
        total_iob = 0.0
        for timer in self.timers:
            if not timer.expired:
                elapsed_hours = timer.elapsed_seconds / 3600
                duration_hours = timer.duration_minutes / 60
                remaining = timer.units * (1 - elapsed_hours / duration_hours)
                total_iob += max(0, remaining)
        return round(total_iob, 1)

    async def start_updates(self):
        """Start periodic timer updates (every 10 seconds)."""
        self._running = True
        while self._running:
            if self.timers:
                # Remove expired
                before = len(self.timers)
                self.timers = [t for t in self.timers if not t.expired]
                if len(self.timers) < before:
                    self._save_state()

                await self.broadcast("timer_update", self.get_timer_data())
            await asyncio.sleep(10)

    def stop(self):
        self._running = False
        if self._update_task:
            self._update_task.cancel()
