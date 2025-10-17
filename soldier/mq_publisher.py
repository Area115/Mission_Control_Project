import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))
STATUS_QUEUE = "status_queue"

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

class StatusPublisher:
    def __init__(self):
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        self.connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
)
        self.channel = self.connection.channel()
        # self.channel.queue_declare(queue="status_queue")
        self.channel.queue_declare(queue="status_queue", durable=True)


    def publish_status(self, mission_id: str, status: str, token: str | None = None):
        message = {"mission_id": mission_id, "status": status}
        if token:
            message["token"] = token
        body = json.dumps(message)
        self.channel.basic_publish(exchange="", routing_key="status_queue", body=body)
        print(f"📡 Sent status update → {message}")

    def close(self):
        """Cleanly close connection."""
        self.connection.close()
        print("🔌 Closed connection to RabbitMQ")


if __name__ == "__main__":
    publisher = StatusPublisher()
    publisher.publish_status("mission-alpha", "IN_PROGRESS")
    publisher.publish_status("mission-alpha", "COMPLETED")
    publisher.close()

