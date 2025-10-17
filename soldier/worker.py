import threading
import time
import os
from soldier.mq_consumer import MissionConsumer
from soldier.mq_publisher import StatusPublisher
from soldier.executer import MissionExecutor
from soldier.auth_client import AuthClient

SOLDIER_ID = os.getenv("SOLDIER_ID", "01")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

class SoldierWorker:
    def __init__(self):
        print(f" Soldier started with ID={SOLDIER_ID}")

        self.auth = AuthClient(SOLDIER_ID)
        self.auth.start_auto_refresh()

        # Keep trying to connect to RabbitMQ until it works
        self.publisher = None
        while self.publisher is None:
            try:
                self.publisher = StatusPublisher()
                print(" StatusPublisher connected.")
            except Exception as e:
                print(f"Failed to connect to RabbitMQ (publisher): {e}")
                time.sleep(5)

        self.executor = MissionExecutor(status_callback=self.publish_status)

        # Keep trying to connect the consumer too
        self.consumer = None
        while self.consumer is None:
            try:
                self.consumer = MissionConsumer(self.handle_mission)
                print(" MissionConsumer connected.")
            except Exception as e:
                print(f" Failed to connect to RabbitMQ (consumer): {e}")
                time.sleep(5)

    def publish_status(self, mission_id: str, status: str):
        token = self.auth.token
        if not self.publisher:
            print(" No publisher connection yet.")
            return
        self.publisher.publish_status(mission_id, status, token=token)

    def handle_mission(self, mission_data: dict):
        thread = threading.Thread(target=self.executor.execute, args=(mission_data,))
        thread.start()

    def start(self):
        """Start consuming missions indefinitely."""
        print(" Waiting for missions...")
        while True:
            try:
                self.consumer.start_consuming()
            except Exception as e:
                print(f" Consumer error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    worker = SoldierWorker()
    worker.start()
