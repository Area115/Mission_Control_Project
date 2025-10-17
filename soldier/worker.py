# soldier/worker.py
import os
import json
import time
import threading
import redis

from soldier.mq_consumer import MissionConsumer
from soldier.mq_publisher import StatusPublisher
from soldier.executer import MissionExecutor
from soldier.auth_client import AuthClient

SOLDIER_ID   = os.getenv("SOLDIER_ID", "01")
REDIS_HOST   = os.getenv("REDIS_HOST", "redis")
REDIS_PORT   = int(os.getenv("REDIS_PORT", 6379))
QUEUE_KEY    = f"soldier_queue:{SOLDIER_ID}"

class SoldierWorker:
    def __init__(self):
        print(f"🪖 Soldier started with ID={SOLDIER_ID}")

        # Auth (auto-refresh JWT every ~25s)
        self.auth = AuthClient(SOLDIER_ID)
        self.auth.start_auto_refresh()

        # MQ: publish statuses + consume orders
        self.publisher = StatusPublisher()
        self.consumer  = MissionConsumer(self._on_order)

        # Redis (for per-soldier queue)
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

        # Execution controller
        self.executor = MissionExecutor(status_callback=self._publish_status)
        self._busy_lock = threading.Lock()
        self._busy = False

        # Start a background thread that blocks on the Redis queue whenever idle
        self._queue_thread = threading.Thread(target=self._queue_watcher, daemon=True)
        self._queue_thread.start()

    # ------------- Busy flag helpers -------------
    def _set_busy(self, value: bool):
        with self._busy_lock:
            self._busy = value

    def _is_busy(self) -> bool:
        with self._busy_lock:
            return self._busy

    # ------------- Public status publisher -------------
    def _publish_status(self, mission_id: str, status: str):
        token = self.auth.token
        self.publisher.publish_status(mission_id, status, token=token)

        # When a mission ends, just mark not busy.
        # The queue watcher (BRPOP) will instantly grab the next queued mission if any.
        if status in ("COMPLETED", "FAILED"):
            self._set_busy(False)

    # ------------- RabbitMQ order handler -------------
    def _on_order(self, mission_data: dict):
        if not mission_data:
            return

        target = str(mission_data.get("soldier_id", "")).strip()
        if target != SOLDIER_ID:
            # ✅ Forward to the *intended* soldier’s queue so that soldier’s watcher can pick it up
            self.redis.rpush(f"soldier_queue:{target}", json.dumps(mission_data))
            print(f"⏭️ Not for me (me={SOLDIER_ID}, target={target}) → queued for soldier {target}")
            return

        if self._is_busy():
            # Soldier busy → enqueue *my* queue for later
            self.redis.rpush(QUEUE_KEY, json.dumps(mission_data))
            print(f"📦 Enqueued mission {mission_data.get('mission_id')} (busy).")
            return

        # Soldier idle → start now
        self._start_mission_now(mission_data)


    # ------------- Start mission immediately -------------
    def _start_mission_now(self, mission: dict):
        mission_id = mission.get("mission_id")
        # Notify Commander right away that we’re starting
        self.publisher.publish_status(mission_id, "IN_PROGRESS", token=mission.get("token", self.auth.token))
        # Run mission
        self._set_busy(True)
        threading.Thread(target=self.executor.execute, args=(mission,), daemon=True).start()

    # ------------- Queue watcher using BRPOP -------------
    def _queue_watcher(self):
        """
        When idle, block on BRPOP to fetch the next queued mission.
        This removes all timing races between Commander enqueue and Soldier pickup.
        """
        print(f"👂 Queue watcher started for {QUEUE_KEY}")
        # Ensure the queue exists (optional)
        while True:
            # If currently busy, just sleep briefly and re-check
            if self._is_busy():
                time.sleep(0.3)
                continue

            try:
                # BRPOP blocks until an item is available or timeout occurs.
                # We use a short timeout to allow checking _is_busy again.
                popped = self.redis.brpop(QUEUE_KEY, timeout=2)
                if not popped:
                    # timeout: nothing in queue right now
                    continue

                # popped is a tuple: (key, value)
                _, payload = popped
                mission = json.loads(payload)

                # Double-check busy (another mission might have started in the meantime)
                if self._is_busy():
                    # Put it back at the head to preserve order
                    self.redis.lpush(QUEUE_KEY, json.dumps(mission))
                    continue

                print(f"🚀 Starting queued mission {mission.get('mission_id')}")
                self._start_mission_now(mission)

            except Exception as e:
                print(f"❌ Queue watcher error: {e}")
                time.sleep(1)

    # ------------- Main loop -------------
    def start(self):
        print("🪖 Soldier worker is ready and awaiting missions...")
        # Consume RabbitMQ orders (this blocks forever)
        self.consumer.start_consuming()


if __name__ == "__main__":
    SoldierWorker().start()
