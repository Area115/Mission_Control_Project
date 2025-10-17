import json
import redis
import os

class MissionStore:
    def __init__(self):
        # Connect to Redis (make sure Redis is running on localhost:6379)
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )

    # ------------------ Mission Management ------------------

    def add_mission(self, mission_id: str, mission_data: dict):
        self.redis.set(mission_id, json.dumps(mission_data))

    def get_mission(self, mission_id: str) -> dict | None:
        data = self.redis.get(mission_id)
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set_status(self, mission_id: str, status: str):
        mission = self.get_mission(mission_id)
        if not mission:
            print(f" No mission found for ID: {mission_id}")
            return
        mission["status"] = status
        self.add_mission(mission_id, mission)
        print(f" Updated mission {mission_id} → {status}")

    def get_all_missions_for_soldier(self, soldier_id: str) -> list[dict]:
        all_keys = self.redis.keys("*")
        result = []
        for key in all_keys:
            data = self.redis.get(key)
            if not data:
                continue
            try:
                mission = json.loads(data)
                if mission.get("soldier_id") == soldier_id:
                    result.append(mission)
            except Exception:
                continue
        return result

    def get_all_missions(self) -> list[dict]:
        all_keys = self.redis.keys("*")
        missions = []
        for key in all_keys:
            data = self.redis.get(key)
            if not data:
                continue
            try:
                missions.append(json.loads(data))
            except Exception:
                continue
        return missions
