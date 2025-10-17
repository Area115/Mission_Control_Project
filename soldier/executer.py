import time
import random
import os
JOB_EXECUTION_TIME = int(os.getenv("JOB_EXECUTION_TIME", 10))
class MissionExecutor:

    def __init__(self, status_callback):
        self.status_callback = status_callback

    def execute(self, mission_data: dict):
        mission_id = mission_data.get("mission_id")
        print(f" Starting mission {mission_id} → {mission_data['objective']}")

        # Step 1: mark as IN_PROGRESS
        self.status_callback(mission_id, "IN_PROGRESS")

        # Step 2: simulate mission running (5–15 sec delay)
        pick = random.randint(1, 100)
        print(f" Mission {mission_id} in progress... will take {JOB_EXECUTION_TIME} seconds.")
        time.sleep(JOB_EXECUTION_TIME)

        # Step 3: randomly decide success or failure (90% success chance)
        result = "COMPLETED" if pick < 80 else "FAILED"

        # Step 4: publish final status
        print(f" Mission {mission_id} {result}")
        self.status_callback(mission_id, result)

if __name__ == "__main__":
    def mock_callback(mission_id, status):
        print(f" Callback → {mission_id}: {status}")

    mission = {
        "mission_id": "test123",
        "objective": "Test mission execution"
    }

    executor = MissionExecutor(mock_callback)
    executor.execute(mission)
