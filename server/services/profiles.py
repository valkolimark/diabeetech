"""
Multi-user profile manager.

Each user gets an isolated data directory:
  server/data/profiles/{profile_id}/
    ├── settings.json
    ├── contacts.json
    └── cache/
        ├── historical_data.json
        └── insulin_timers.json

Profile ID = MD5(subdomain + ":" + email)
"""
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("diabeetech.profiles")

DATA_DIR = Path(__file__).parent.parent / "data"
PROFILES_DIR = DATA_DIR / "profiles"
REGISTRY_FILE = DATA_DIR / "profiles.json"


def compute_profile_id(subdomain: str, email: str) -> str:
    """Compute a profile ID from subdomain and email."""
    raw = f"{subdomain}:{email}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


class ProfileManager:
    def __init__(self):
        self._current_profile_id: Optional[str] = None
        self._registry: list = []
        self._load_registry()

    def _load_registry(self):
        """Load the profiles registry."""
        if REGISTRY_FILE.exists():
            try:
                self._registry = json.loads(REGISTRY_FILE.read_text())
            except Exception:
                self._registry = []
        else:
            self._registry = []

    def _save_registry(self):
        """Save the profiles registry."""
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_FILE.write_text(json.dumps(self._registry, indent=2))

    def get_profile_dir(self, profile_id: str) -> Path:
        """Get the data directory for a profile."""
        return PROFILES_DIR / profile_id

    def ensure_profile(self, subdomain: str, email: str, display_name: str = "") -> str:
        """Create profile directory if needed, return profile_id."""
        profile_id = compute_profile_id(subdomain, email)
        profile_dir = self.get_profile_dir(profile_id)

        if not profile_dir.exists():
            logger.info(f"Creating profile: {profile_id} ({subdomain}/{email})")
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "cache").mkdir(exist_ok=True)

            # Copy default settings if main settings exist
            default_settings = DATA_DIR / "settings.json"
            if default_settings.exists():
                shutil.copy2(default_settings, profile_dir / "settings.json")
            else:
                (profile_dir / "settings.json").write_text("{}")

            (profile_dir / "contacts.json").write_text("[]")

        # Update registry
        existing = next((p for p in self._registry if p["id"] == profile_id), None)
        if existing:
            existing["display_name"] = display_name or existing.get("display_name", "")
        else:
            self._registry.append({
                "id": profile_id,
                "subdomain": subdomain,
                "email": email,
                "display_name": display_name or subdomain,
            })
        self._save_registry()

        self._current_profile_id = profile_id
        return profile_id

    def get_current_profile(self) -> Optional[dict]:
        """Get the current active profile info."""
        if not self._current_profile_id:
            return None
        return next((p for p in self._registry if p["id"] == self._current_profile_id), None)

    def list_profiles(self) -> list:
        """List all known profiles."""
        return self._registry

    def switch_profile(self, profile_id: str) -> bool:
        """Switch to a different profile."""
        profile = next((p for p in self._registry if p["id"] == profile_id), None)
        if not profile:
            return False

        profile_dir = self.get_profile_dir(profile_id)
        if not profile_dir.exists():
            return False

        self._current_profile_id = profile_id
        logger.info(f"Switched to profile: {profile_id} ({profile.get('display_name', '')})")
        return True

    def get_profile_settings(self, profile_id: Optional[str] = None) -> dict:
        """Load settings for a profile."""
        pid = profile_id or self._current_profile_id
        if not pid:
            return {}
        settings_file = self.get_profile_dir(pid) / "settings.json"
        if settings_file.exists():
            try:
                return json.loads(settings_file.read_text())
            except Exception:
                return {}
        return {}

    def save_profile_settings(self, settings: dict, profile_id: Optional[str] = None):
        """Save settings for a profile."""
        pid = profile_id or self._current_profile_id
        if not pid:
            return
        settings_file = self.get_profile_dir(pid) / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(settings, indent=2))
