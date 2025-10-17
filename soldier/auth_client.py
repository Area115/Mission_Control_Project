import os
import time
import threading
import requests

COMMANDER_BASE = os.getenv("COMMANDER_BASE", "http://commander:8000")
SOLDIER_ID = os.getenv("SOLDIER_ID", "01")
REFRESH_SECONDS = int(os.getenv("JWT_REFRESH_SECONDS", 25))

class AuthClient:
    def __init__(self, soldier_id: str):
        self.soldier_id = soldier_id
        self.token = None
        self._stop = False
        self._thread = None

    def fetch_token_once(self):
        url = f"{COMMANDER_BASE}/auth/token"
        params = {"soldier_id": self.soldier_id}

        for attempt in range(10):
            try:
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                self.token = data["token"]
                print(f"Received JWT for soldier {self.soldier_id}")
                return
            except Exception as e:
                print(f"Token fetch error (attempt {attempt+1}/10): {e}")
                time.sleep(5)
        print(f" Soldier {self.soldier_id} could not fetch token after multiple attempts.")

    def start_auto_refresh(self):
        def loop():
            while not self._stop:
                try:
                    print(f"♻️ Refreshing token for soldier {self.soldier_id}...")
                    self.fetch_token_once()
                except Exception as e:
                    print(f"❌ Token fetch error: {e}")
                for _ in range(REFRESH_SECONDS):
                    if self._stop:
                        break
                    time.sleep(1)

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1)
