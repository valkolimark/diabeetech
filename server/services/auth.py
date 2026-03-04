"""
Auth manager for Diabeetech Nightscout multi-tenant backend.

Responsibilities:
1. Read saved login from ~/.diabeetech/saved_login.json
2. Construct tenant-specific base URL: https://{subdomain}.diabeetech.net
3. Provide api-secret header (SHA1 hash) for all Nightscout API calls
4. Manage JWT token for auth-protected endpoints
5. Handle login flow (subdomain + email + password → JWT)
6. Persist login state back to saved_login.json
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("diabeetech.auth")


class AuthManager:
    def __init__(self):
        self.subdomain: Optional[str] = None
        self.base_url: Optional[str] = None
        self.api_secret_hash: Optional[str] = None
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.email: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None

        self._base_domain = os.getenv("API_BASE_DOMAIN", "diabeetech.net")
        self._api_secret = os.getenv("API_SECRET", "")

        # Compute SHA1 hash of API secret at startup
        if self._api_secret:
            self.api_secret_hash = hashlib.sha1(self._api_secret.encode()).hexdigest()
            logger.info(f"API secret hash computed: {self.api_secret_hash[:12]}...")

        # Load saved login
        self._load_saved_login()

    @property
    def saved_login_path(self) -> Path:
        """Path to saved login file. Uses ~/.diabeetech/ on all platforms."""
        return Path.home() / ".diabeetech" / "saved_login.json"

    def _load_saved_login(self):
        """Load saved login from ~/.diabeetech/saved_login.json."""
        path = self.saved_login_path
        if not path.exists():
            # Also check server/data/saved_credentials.json as fallback
            fallback = Path(__file__).parent.parent / "data" / "saved_credentials.json"
            if fallback.exists():
                try:
                    data = json.loads(fallback.read_text())
                    if data and data.get("subdomain"):
                        self._apply_login_data(data)
                        return
                except Exception:
                    pass
            logger.warning("No saved login found. CGM sync will not start until login.")
            return

        try:
            data = json.loads(path.read_text())
            self._apply_login_data(data)
        except Exception as e:
            logger.error(f"Error loading saved login: {e}")

    def _apply_login_data(self, data: dict):
        """Apply login data from saved file."""
        self.subdomain = data.get("subdomain")
        self.email = data.get("email")
        self.token = data.get("token")
        self.tenant_id = data.get("tenant_id")
        self.user_id = data.get("user_id")

        if self.subdomain:
            self.base_url = f"https://{self.subdomain}.{self._base_domain}"
            logger.info(f"Loaded login: subdomain={self.subdomain}, base_url={self.base_url}")
        else:
            logger.warning("Saved login has no subdomain")

    def save_login(self):
        """Persist current login state to ~/.diabeetech/saved_login.json."""
        path = self.saved_login_path
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "subdomain": self.subdomain,
            "email": self.email,
            "token": self.token,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
        }
        path.write_text(json.dumps(data, indent=2))
        logger.info(f"Login saved to {path}")

    async def login(self, subdomain: str, email: str, password: str) -> dict:
        """
        Login to the Nightscout multi-tenant backend.
        Returns the JWT payload on success.
        """
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.{self._base_domain}"
        url = f"{self.base_url}/api/auth/login"

        try:
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "subdomain": subdomain
            }, timeout=30)

            if response.status_code == 200:
                result = response.json()
                self.token = result.get("token") or result.get("accessToken")
                self.email = email

                # Parse JWT payload (without verification - just decode the claims)
                if self.token:
                    import jwt
                    try:
                        payload = jwt.decode(self.token, options={"verify_signature": False})
                        self.tenant_id = payload.get("tenantId")
                        self.user_id = payload.get("userId")
                    except Exception:
                        pass

                self.save_login()
                logger.info(f"Login successful for {email}@{subdomain}")
                return {"success": True, "subdomain": subdomain}
            else:
                logger.error(f"Login failed: {response.status_code} {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": str(e)}

    def get_base_url(self) -> Optional[str]:
        """Get the tenant-specific base URL."""
        return self.base_url

    def get_headers(self) -> dict:
        """Get headers for Nightscout API calls (JWT token or api-secret)."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.api_secret_hash:
            headers["api-secret"] = self.api_secret_hash
        return headers

    def get_subdomain(self) -> Optional[str]:
        """Get the current subdomain."""
        return self.subdomain

    def is_authenticated(self) -> bool:
        """Check if we have a valid subdomain and either token or api-secret."""
        return bool(self.subdomain and (self.token or self.api_secret_hash))

    def ensure_jwt_login(self):
        """Auto-login with API_SECRET as password if we have subdomain + email but no token."""
        if self.token:
            return True
        if not self.subdomain or not self.email or not self._api_secret:
            return False
        try:
            url = f"{self.base_url}/api/auth/login"
            response = requests.post(url, json={
                "email": self.email,
                "password": self._api_secret,
                "subdomain": self.subdomain,
            }, timeout=15)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("accessToken") or result.get("token")
                if self.token:
                    try:
                        import jwt as pyjwt
                        payload = pyjwt.decode(self.token, options={"verify_signature": False})
                        self.tenant_id = payload.get("tenantId")
                        self.user_id = payload.get("userId")
                    except Exception:
                        pass
                    self.save_login()
                    logger.info(f"JWT login successful for {self.email}@{self.subdomain}")
                    return True
            logger.error(f"JWT login failed: {response.status_code} {response.text[:200]}")
        except Exception as e:
            logger.error(f"JWT login error: {e}")
        return False
