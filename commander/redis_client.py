import json
import redis
import os


class MissionStore:
    def __init__(self):
        # Connect to Redis
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )

    # -------------------------------------------------------
    # 🧩 Core Mission CRUD
    # -------------------------------------------------------

    def add_mission(self, mission_id: str, mission_data: dict):
        key = f"mission:{mission_id}" 
        self.redis.set(key, json.dumps(mission_data))

    def get_mission(self, mission_id: str) -> dict | None:
        key = f"mission:{mission_id}" 
        data = self.redis.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set_status(self, mission_id: str, status: str):
        key = f"mission:{mission_id}"
        mission = self.get_mission(mission_id)
        if not mission:
            print(f" No mission found with ID {mission_id}")
            return
        mission["status"] = status
        self.redis.set(key, json.dumps(mission))
        print(f"Updated mission {mission_id} → {status}")

    def get_all_missions_for_soldier(self, soldier_id: str):
        result = []
        for key in self.redis.keys("mission:*"): 
            try:
                data = self.redis.get(key)
                if not data:
                    continue
                mission = json.loads(data)
                if mission.get("soldier_id") == soldier_id:
                    result.append(mission)
            except Exception:
                continue
        return result

    # -------------------------------------------------------
    # 🧩 Fetch all missions — debugging/admin
    # -------------------------------------------------------

    def get_all_missions(self) -> list[dict]:
        missions = []
        for key in self.redis.keys("mission:*"):
            data = self.redis.get(key)
            if data:
                try:
                    missions.append(json.loads(data))
                except Exception:
                    pass
        return missions

    def update_status(self, mission_id, new_status):
        key = f"mission:{mission_id}"
        data = self.redis.get(key)
        if not data:
            print(f" Mission {mission_id} not found in Redis.")
            return
        mission = json.loads(data)
        mission["status"] = new_status
        self.redis.set(key, json.dumps(mission))
        print(f" Mission {mission_id} status updated to {new_status}")
    # -------------------------------------------------------
# 🧩 Soldier Mission Queue Management
# -------------------------------------------------------
    def enqueue_mission_for_soldier(self, soldier_id: str, mission_data: dict):
        """Add a mission to the soldier's Redis queue."""
        queue_key = f"soldier_queue:{soldier_id}"
        self.redis.rpush(queue_key, json.dumps(mission_data))
        print(f"📦 Queued mission {mission_data['mission_id']} for soldier {soldier_id}")

    def dequeue_mission_for_soldier(self, soldier_id: str) -> dict | None:
        """Pop the next mission from the soldier's Redis queue."""
        queue_key = f"soldier_queue:{soldier_id}"
        data = self.redis.lpop(queue_key)
        if not data:
            return None
        try:
            mission = json.loads(data)
            print(f"📤 Dequeued mission {mission['mission_id']} for soldier {soldier_id}")
            return mission
        except Exception:
            return None

