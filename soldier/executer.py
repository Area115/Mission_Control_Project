import time
import json
from soldier.mq_publisher import StatusPublisher


class MissionExecutor:
    """
    Simulates mission execution for a soldier.
    Sends periodic status updates to RabbitMQ via StatusPublisher.
    """

    def __init__(self, soldier_id: str):
        self.soldier_id = soldier_id
        self.status_publisher = StatusPublisher()

    def execute_mission(self, mission: dict):
        mission_id = mission.get("mission_id")
        objective = mission.get("objective")
        priority = mission.get("priority", "MEDIUM")

        print(f"🎯 Soldier {self.soldier_id} executing mission {mission_id} → {objective} (Priority: {priority})")

        try:
            # ------------------------------
            # 1️⃣ Send IN_PROGRESS update
            # ------------------------------
            self._send_status_update(mission_id, "IN_PROGRESS")

            # ------------------------------
            # 2️⃣ Simulate mission execution time
            # ------------------------------
            total_steps = 5
            for step in range(1, total_steps + 1):
                time.sleep(2)  # simulate doing part of the task
                progress = int((step / total_steps) * 100)
                print(f"🪖 Soldier {self.soldier_id} progress: {progress}% ({step}/{total_steps})")

            # ------------------------------
            # 3️⃣ Send COMPLETED update
            # ------------------------------
            self._send_status_update(mission_id, "COMPLETED")

            print(f"✅ Soldier {self.soldier_id} completed mission {mission_id} → {objective}")

        except Exception as e:
            print(f"❌ Error executing mission {mission_id}: {e}")
            # If something fails, mark as FAILED
            self._send_status_update(mission_id, "FAILED")

    def _send_status_update(self, mission_id: str, status: str):
        """Helper to send status updates."""
        try:
            message = {
                "mission_id": mission_id,
                "status": status
            }
            self.status_publisher.publish_status(message)
        except Exception as e:
            print(f"⚠️ Failed to publish status update for {mission_id}: {e}")

    def close(self):
        """Cleanly close RabbitMQ connection."""
        try:
            self.status_publisher.close()
        except:
            pass
