"""
CGM data sync service.

Handles:
- 30-second polling loop for latest glucose data
- 5-minute background sync for historical data
- Glucose state detection with configurable thresholds
- Color assignment based on state
- Local JSON cache for offline fallback
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

import requests

from services.auth import AuthManager

logger = logging.getLogger("diabeetech.glucose")

DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
HISTORY_CACHE = CACHE_DIR / "historical_data.json"


class GlucoseService:
    def __init__(self, auth_manager: AuthManager, settings: dict):
        self.auth = auth_manager
        self.settings = settings

        # Thresholds from settings
        self.threshold_high = int(settings.get("threshold_high", 300))
        self.threshold_trending_high = int(settings.get("threshold_trending_high", 263))
        self.threshold_trending_low = int(settings.get("threshold_trending_low", 120))
        self.threshold_low = int(settings.get("threshold_low", 100))

        # Colors from settings
        self.colors = {
            "high": settings.get("high_color", "#e100ff"),
            "trending_high": settings.get("trending_high_color", "#FF8C00"),
            "normal": settings.get("normal_color", "#00FF00"),
            "trending_low": settings.get("trending_low_color", "#FFD700"),
            "low": settings.get("low_color", "#FF0000"),
            "no_data": "#404040",
        }

        # State
        self.latest_reading: Optional[dict] = None
        self.historical_data: List[dict] = []
        self.last_sync: Optional[datetime] = None
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None

        # Load cached history
        self._load_cache()

    def _load_cache(self):
        """Load historical data from local cache."""
        if HISTORY_CACHE.exists():
            try:
                self.historical_data = json.loads(HISTORY_CACHE.read_text())
                logger.info(f"Loaded {len(self.historical_data)} cached readings")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.historical_data = []

    def _save_cache(self):
        """Save historical data to local cache."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            # Keep last 90 days max
            cutoff = datetime.now() - timedelta(days=90)
            cutoff_ms = int(cutoff.timestamp() * 1000)
            self.historical_data = [
                r for r in self.historical_data if r.get("date", 0) > cutoff_ms
            ]
            HISTORY_CACHE.write_text(json.dumps(self.historical_data))
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get_glucose_state(self, glucose: float) -> str:
        """Determine glucose state based on thresholds."""
        if glucose >= self.threshold_high:
            return "high"
        if glucose < self.threshold_low:
            return "low"
        if glucose < self.threshold_trending_low:
            return "trending_low"
        if glucose >= self.threshold_trending_high:
            return "trending_high"
        return "normal"

    def get_state_color(self, state: str) -> str:
        """Get the color for a glucose state."""
        return self.colors.get(state, self.colors["no_data"])

    def _calculate_diff(self, current_glucose: float, entries: list) -> Optional[int]:
        """
        Calculate the glucose difference from the previous reading.
        Validates that readings are 3-10 minutes apart.
        """
        now = datetime.now()

        # Priority 1: Use API response entries (index 1 = previous reading)
        if len(entries) >= 2:
            prev = entries[1]
            prev_date_ms = prev.get("date", 0)
            if prev_date_ms:
                prev_dt = datetime.fromtimestamp(prev_date_ms / 1000)
                gap_minutes = (now - prev_dt).total_seconds() / 60
                # Accept entries from 3-10 minutes ago
                if 3 <= gap_minutes <= 15:
                    prev_glucose = prev.get("sgv", 0)
                    if prev_glucose:
                        return int(round(current_glucose - prev_glucose))

        # Priority 2: Use historical data
        if self.historical_data:
            sorted_hist = sorted(self.historical_data, key=lambda x: x.get("date", 0), reverse=True)
            for entry in sorted_hist:
                entry_date_ms = entry.get("date", 0)
                if entry_date_ms:
                    entry_dt = datetime.fromtimestamp(entry_date_ms / 1000)
                    gap_minutes = (now - entry_dt).total_seconds() / 60
                    if 3 <= gap_minutes <= 15:
                        prev_glucose = entry.get("sgv", 0)
                        if prev_glucose:
                            return int(round(current_glucose - prev_glucose))

        # Priority 3: Use latest reading if available
        if self.latest_reading:
            prev_glucose = self.latest_reading.get("sgv", 0)
            if prev_glucose and prev_glucose != current_glucose:
                return int(round(current_glucose - prev_glucose))

        return None

    def fetch_latest(self) -> Optional[dict]:
        """
        Fetch the latest glucose reading from the Nightscout API.
        Returns a glucose_update dict or None on failure.
        """
        base_url = self.auth.get_base_url()
        if not base_url:
            logger.warning("No base URL configured — skipping fetch")
            return None

        headers = self.auth.get_headers()
        url = f"{base_url}/api/v1/entries.json"
        params = {
            "find[type]": "sgv",
            "count": 3,
            "sort": "-date"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                logger.error(f"API returned {response.status_code}: {response.text[:200]}")
                return self._get_cached_reading()

            data = response.json()

            # Handle wrapped response formats
            if isinstance(data, dict):
                data = data.get("entries") or data.get("data") or []

            if not data or not isinstance(data, list):
                logger.warning("No entries in API response")
                return self._get_cached_reading()

            # Parse latest entry
            entry = data[0]
            glucose = entry.get("sgv")
            if glucose is None:
                return self._get_cached_reading()

            glucose = float(glucose)
            trend = entry.get("direction") or entry.get("trend", "")
            if isinstance(trend, int):
                # Convert numeric trend to string
                trend_map = {
                    1: "DoubleUp", 2: "SingleUp", 3: "FortyFiveUp",
                    4: "Flat", 5: "FortyFiveDown", 6: "SingleDown",
                    7: "DoubleDown"
                }
                trend = trend_map.get(trend, "NOT COMPUTABLE")

            date_ms = entry.get("date", 0)
            if date_ms:
                dt = datetime.fromtimestamp(date_ms / 1000)
                minutes_ago = int((datetime.now() - dt).total_seconds() / 60)
                timestamp = dt.isoformat()
            else:
                minutes_ago = 0
                timestamp = datetime.now().isoformat()

            # Check staleness (> 15 minutes)
            stale = minutes_ago > 15

            if stale:
                state = "no_data"
                color = self.colors["no_data"]
            else:
                state = self.get_glucose_state(glucose)
                color = self.get_state_color(state)

            # Calculate diff
            diff = self._calculate_diff(glucose, data)

            # Build result
            result = {
                "sgv": int(round(glucose)),
                "trend": trend,
                "direction": trend,
                "timestamp": timestamp,
                "delta": diff,
                "state": state,
                "color": color,
                "stale": stale,
                "stale_minutes": minutes_ago if stale else 0,
            }

            # Update latest reading
            self.latest_reading = result

            # Add to historical data (deduplicate by timestamp)
            if date_ms and not stale:
                existing_dates = {r.get("date") for r in self.historical_data}
                if date_ms not in existing_dates:
                    self.historical_data.append({
                        "sgv": int(round(glucose)),
                        "date": date_ms,
                        "direction": trend,
                        "diff": diff,
                    })
                    # Sort by date
                    self.historical_data.sort(key=lambda x: x.get("date", 0))
                    self._save_cache()

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching glucose: {e}")
            return self._get_cached_reading()
        except Exception as e:
            logger.error(f"Error fetching glucose: {e}")
            return self._get_cached_reading()

    def _get_cached_reading(self) -> Optional[dict]:
        """Return the last known reading as a cached/stale result."""
        if self.latest_reading:
            cached = dict(self.latest_reading)
            cached["stale"] = True
            cached["state"] = "no_data"
            cached["color"] = self.colors["no_data"]
            return cached
        return None

    def fetch_history(self, count: int = 2016) -> List[dict]:
        """Fetch historical glucose data from the Nightscout API."""
        base_url = self.auth.get_base_url()
        if not base_url:
            return self.historical_data

        headers = self.auth.get_headers()
        url = f"{base_url}/api/v1/entries.json"
        params = {"count": count}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code != 200:
                logger.error(f"History fetch failed: {response.status_code}")
                return self.historical_data

            data = response.json()
            if isinstance(data, dict):
                data = data.get("entries") or data.get("data") or []

            if data:
                # Merge with existing history (deduplicate by date)
                existing_dates = {r.get("date") for r in self.historical_data}
                new_count = 0
                for entry in data:
                    date_ms = entry.get("date", 0)
                    if date_ms and date_ms not in existing_dates:
                        self.historical_data.append({
                            "sgv": entry.get("sgv"),
                            "date": date_ms,
                            "direction": entry.get("direction") or entry.get("trend", ""),
                            "diff": None,
                        })
                        existing_dates.add(date_ms)
                        new_count += 1

                self.historical_data.sort(key=lambda x: x.get("date", 0))
                self._save_cache()
                self.last_sync = datetime.now()
                logger.info(f"History sync: {new_count} new entries, {len(self.historical_data)} total")

            return self.historical_data

        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return self.historical_data

    def get_history_for_range(self, hours: int = 2) -> List[dict]:
        """Get historical data for a specific time range with state/color info."""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_ms = int(cutoff.timestamp() * 1000)

        readings = []
        for entry in self.historical_data:
            if entry.get("date", 0) >= cutoff_ms:
                sgv = entry.get("sgv")
                if sgv is not None:
                    state = self.get_glucose_state(sgv)
                    readings.append({
                        "sgv": sgv,
                        "timestamp": datetime.fromtimestamp(entry["date"] / 1000).isoformat(),
                        "trend": entry.get("direction", ""),
                        "state": state,
                        "color": self.get_state_color(state),
                    })

        return readings

    async def start_polling(self, broadcast_callback):
        """Start the 30-second glucose polling loop."""
        self._running = True
        logger.info("Starting glucose polling loop (30s interval)")

        # Initial history sync
        self._sync_task = asyncio.create_task(self._background_sync())

        while self._running:
            try:
                result = await asyncio.get_event_loop().run_in_executor(None, self.fetch_latest)
                if result:
                    await broadcast_callback("glucose_update", result)
                    logger.info(
                        f"Glucose: {result['sgv']} mg/dL | {result['trend']} | "
                        f"state={result['state']} | delta={result['delta']}"
                    )
                else:
                    # No data available
                    await broadcast_callback("glucose_update", {
                        "sgv": None,
                        "trend": "NOT COMPUTABLE",
                        "direction": "NOT COMPUTABLE",
                        "timestamp": datetime.now().isoformat(),
                        "delta": None,
                        "state": "no_data",
                        "color": self.colors["no_data"],
                        "stale": True,
                        "stale_minutes": 0,
                    })
            except Exception as e:
                logger.error(f"Polling error: {e}")

            await asyncio.sleep(30)

    async def _background_sync(self):
        """Background sync every 5 minutes for historical data."""
        while self._running:
            try:
                should_sync = (
                    self.last_sync is None or
                    (datetime.now() - self.last_sync).total_seconds() > 300
                )
                if should_sync:
                    logger.info("Starting background history sync...")
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.fetch_history, 2016
                    )
            except Exception as e:
                logger.error(f"Background sync error: {e}")
            await asyncio.sleep(300)  # Check every 5 minutes

    def stop(self):
        """Stop all polling and sync tasks."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()
        logger.info("Glucose service stopped")
