"""
WiFi management service.
On Pi: uses nmcli to scan, connect, check status.
On dev: returns simulated data.
"""
import asyncio
import logging
import os
import platform
import subprocess

logger = logging.getLogger("diabeetech.wifi")

IS_PI = platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or not IS_PI

# Dev-mode simulation state
_dev_wifi_state = {
    "connected": True,
    "ssid": "HomeNetwork_5G",
    "has_internet": True,
}

FAKE_NETWORKS = [
    {"ssid": "HomeNetwork_5G", "signal": 85, "secured": True},
    {"ssid": "Neighbor_WiFi", "signal": 62, "secured": True},
    {"ssid": "CoffeeShop_Free", "signal": 45, "secured": False},
    {"ssid": "IoT_Network", "signal": 30, "secured": True},
]


class WiFiService:
    """Manages WiFi operations via nmcli on Pi, simulated in dev."""

    async def get_status(self) -> dict:
        if DEV_MODE:
            return {
                "connected": _dev_wifi_state["connected"],
                "ssid": _dev_wifi_state["ssid"],
                "has_internet": _dev_wifi_state["has_internet"],
            }

        connected = False
        ssid = None
        has_internet = False

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["nmcli", "-t", "-f", "GENERAL.STATE,GENERAL.CONNECTION", "dev", "show", "wlan0"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if "GENERAL.STATE" in line and "connected" in line.lower():
                    connected = True
                if "GENERAL.CONNECTION" in line:
                    val = line.split(":", 1)[1].strip() if ":" in line else ""
                    if val and val != "--":
                        ssid = val
        except Exception as e:
            logger.error(f"Error checking WiFi status: {e}")

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
                capture_output=True, timeout=5,
            )
            has_internet = result.returncode == 0
        except Exception:
            has_internet = False

        return {"connected": connected, "ssid": ssid, "has_internet": has_internet}

    async def scan_networks(self) -> dict:
        if DEV_MODE:
            await asyncio.sleep(1.5)  # Simulate scan delay
            return {"networks": FAKE_NETWORKS}

        networks = []
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "-e", "yes",
                 "dev", "wifi", "list", "--rescan", "yes"],
                capture_output=True, text=True, timeout=15,
            )
            seen = {}
            for line in result.stdout.strip().split("\n"):
                parts = line.split(":")
                if len(parts) >= 3:
                    ssid = parts[0].strip().replace("\\:", ":")
                    if not ssid:
                        continue
                    try:
                        signal = int(parts[1].strip())
                    except ValueError:
                        signal = 0
                    security = parts[2].strip()
                    secured = security != "" and security != "--"
                    if ssid not in seen or signal > seen[ssid]["signal"]:
                        seen[ssid] = {"ssid": ssid, "signal": signal, "secured": secured}

            networks = sorted(seen.values(), key=lambda n: n["signal"], reverse=True)
        except Exception as e:
            logger.error(f"Error scanning WiFi networks: {e}")

        return {"networks": networks}

    async def connect(self, ssid: str, password: str = "") -> dict:
        if DEV_MODE:
            await asyncio.sleep(2)
            if password == "test" or not password:
                _dev_wifi_state["connected"] = True
                _dev_wifi_state["ssid"] = ssid
                _dev_wifi_state["has_internet"] = True
                return {"success": True}
            else:
                return {"success": False, "error": "Incorrect password (dev mode: use 'test')"}

        try:
            cmd = ["nmcli", "dev", "wifi", "connect", ssid]
            if password:
                cmd += ["password", password]

            result = await asyncio.to_thread(
                subprocess.run, cmd,
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode == 0:
                await asyncio.sleep(2)
                status = await self.get_status()
                if status["has_internet"]:
                    return {"success": True}
                else:
                    return {"success": True, "warning": "Connected but no internet access"}
            else:
                error_msg = result.stderr.strip() or "Connection failed"
                return {"success": False, "error": error_msg}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Connection timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_dev_state(self, has_internet: bool):
        _dev_wifi_state["has_internet"] = has_internet
        if not has_internet:
            _dev_wifi_state["connected"] = False
            _dev_wifi_state["ssid"] = None
