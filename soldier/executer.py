import time
import json
from soldier.mq_publisher import StatusPublisher


class MissionExecutor:
    """
    Simulates mission execution for a soldier.
    Sends periodic status updates to RabbitMQ via StatusPublisher.
    Includes JWT token for Commander authentication.
    """

    def __init__(self, soldier_id: str, auth_client=None):  # 🟢 added auth_client param
        self.soldier_id = soldier_id
        self.status_publisher = StatusPublisher()
        self.auth_client = auth_client  # 🟢 store AuthClient reference for rotating tokens

    def execute_mission(self, mission: dict, token: str = None):
        """
        Executes a mission and sends progress updates.
        A fresh token is attached to every update.
        """
        mission_id = mission.get("mission_id")
        objective = mission.get("objective")
        priority = mission.get("priority", "MEDIUM")

        print(f"🎯 Soldier {self.soldier_id} executing mission {mission_id} → {objective} (Priority: {priority})")

        try:
            # ------------------------------
            # 1️⃣ Send IN_PROGRESS update
            # ------------------------------
            self._send_status_update(mission_id, "IN_PROGRESS", token)

            # ------------------------------
            # 2️⃣ Simulate mission execution time
            # ------------------------------
            total_steps = 5
            for step in range(1, total_steps + 1):
                time.sleep(2)  # simulate doing part of the task
                progress = int((step / total_steps) * 100)
                print(f"🪖 Soldier {self.soldier_id} progress: {progress}% ({step}/{total_steps})")

                # 🟢 Optionally, send intermediate updates every 2 steps
                if step % 2 == 0:
                    fresh_token = self._get_current_token()
                    self._send_status_update(mission_id, f"PROGRESS_{progress}%", fresh_token)

            # ------------------------------
            # 3️⃣ Send COMPLETED update
            # ------------------------------
            final_token = self._get_current_token()
            self._send_status_update(mission_id, "COMPLETED", final_token)

            print(f"✅ Soldier {self.soldier_id} completed mission {mission_id} → {objective}")

        except Exception as e:
            print(f"❌ Error executing mission {mission_id}: {e}")
            # If something fails, mark as FAILED
            failed_token = self._get_current_token()
            self._send_status_update(mission_id, "FAILED", failed_token)

    # -------------------------------------------------------
    # 🧩 Helper: Send a status update with token
    # -------------------------------------------------------
    def _send_status_update(self, mission_id: str, status: str, token: str = None):
        """Helper to send status updates."""
        try:
            message = {
                "mission_id": mission_id,
                "status": status
            }

            # 🟢 Attach latest JWT token
            if not token:
                token = self._get_current_token()

            if token:
                message["token"] = token
                print(f"🔐 Soldier {self.soldier_id} attached token to update ({status})")
            else: 
                print(f"⚠️ Soldier {self.soldier_id} has no token available while sending {status}")

            self.status_publisher.publish_status(message)
        except Exception as e:
            print(f"⚠️ Failed to publish status update for {mission_id}: {e}")

    # -------------------------------------------------------
    # 🔄 Helper: Get latest token
    # -------------------------------------------------------
    def _get_current_token(self):
        """Fetch latest token from AuthClient if available."""
        if self.auth_client:
            return self.auth_client.get_token()
        return None

    def close(self):
        """Cleanly close RabbitMQ connection."""
        try:
            self.status_publisher.close()
        except:
            pass
