import threading
import time
import requests
import os

COMMANDER_URL = os.getenv("COMMANDER_URL", "http://commander:8000")

class AuthClient:
    """Handles short-lived JWT token rotation for soldiers."""

    def __init__(self, soldier_id: str):
        self.soldier_id = soldier_id
        self.token = None
        self.lock = threading.Lock()
        self.refresh_interval = 25  # refresh every 25s
        self.refresh_thread = threading.Thread(target=self._auto_refresh, daemon=True)
        self.refresh_thread.start()

    def _fetch_token(self):
        try:
            res = requests.get(f"{COMMANDER_URL}/auth/token", params={"soldier_id": self.soldier_id}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                with self.lock:
                    self.token = data.get("token")
                print(f"🔑 Soldier {self.soldier_id}: Token refreshed")
            else:
                print(f"⚠️ Soldier {self.soldier_id}: Failed to fetch token ({res.status_code})")
        except Exception as e:
            print(f"❌ Soldier {self.soldier_id}: Error fetching token: {e}")

    def _auto_refresh(self):
        while True:
            self._fetch_token()
            time.sleep(self.refresh_interval)

    def get_token(self):
        """Safely get current token."""
        with self.lock:
            return self.token
