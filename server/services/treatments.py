"""
Nightscout-compatible treatments API client.

Posts insulin and food treatments to the user's Nightscout instance.
"""
import json
import logging
from datetime import datetime
from typing import Optional

import requests

from services.auth import AuthManager

logger = logging.getLogger("diabeetech.treatments")


class TreatmentsService:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager

    def log_insulin(self, units: float, insulin_type: str,
                    is_correction: bool = False,
                    carbs: Optional[float] = None,
                    glucose: Optional[int] = None,
                    notes: Optional[str] = None) -> bool:
        """
        Post an insulin treatment to Nightscout.

        Args:
            units: Insulin units administered
            insulin_type: e.g. "Humalog", "Novolog", "Lantus"
            is_correction: True if this is a correction dose
            carbs: Carbs eaten (for meal bolus)
            glucose: Current glucose value (for corrections)
            notes: Additional notes

        Returns:
            True on success, False on failure
        """
        base_url = self.auth.get_base_url()
        if not base_url:
            logger.error("No base URL configured — cannot log treatment")
            return False

        # Determine event type
        if carbs and carbs > 0:
            event_type = "Meal Bolus"
        elif is_correction:
            event_type = "Correction Bolus"
        else:
            event_type = "Bolus"

        now = datetime.now()
        treatment = {
            "eventType": event_type,
            "created_at": now.isoformat(),
            "mills": int(now.timestamp() * 1000),
            "insulin": units,
            "insulinType": insulin_type,
            "units": "mg/dl",
            "enteredBy": "Diabeetech",
            "notes": notes or f"{units} units of {insulin_type}",
        }

        if carbs:
            treatment["carbs"] = carbs
        if glucose:
            treatment["glucose"] = glucose
            treatment["glucoseType"] = "Sensor"

        url = f"{base_url}/api/v1/treatments"
        headers = self.auth.get_headers()

        try:
            response = requests.post(url, json=treatment, headers=headers, timeout=15)
            if response.status_code in (200, 201):
                logger.info(f"Treatment logged: {units} units {insulin_type} ({event_type})")
                return True
            else:
                logger.error(f"Treatment log failed: {response.status_code} {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Treatment log error: {e}")
            return False

    def get_treatments(self, hours: int = 168, count: int = 100) -> list:
        """Fetch recent treatments from Nightscout."""
        base_url = self.auth.get_base_url()
        if not base_url:
            return []

        url = f"{base_url}/api/v1/treatments.json"
        headers = self.auth.get_headers()
        params = {"count": count}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching treatments: {e}")
            return []
