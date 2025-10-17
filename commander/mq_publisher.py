import os
import json
import pika

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))

class MissionPublisher:
    def __init__(self):
        credentials = pika.PlainCredentials("guest", "guest")
        connection_params = pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=RABBIT_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self.connection = pika.BlockingConnection(connection_params)
        self.channel = self.connection.channel()
        print(f"✅ Commander connected to RabbitMQ ({RABBIT_HOST}) — ready to publish missions")

    def publish_mission(self, mission: dict):
        soldier_id = str(mission.get("soldier_id"))
        queue_name = f"orders_queue_{soldier_id}"
        self.channel.queue_declare(queue=queue_name, durable=True)
        mission["status"] = "QUEUED"
        message = json.dumps(mission)
        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print(f"📤 Mission published → {queue_name}: {message}")
        return {"mission": mission, "queue": queue_name}

    def close(self):
        if self.connection.is_open:
            self.connection.close()
