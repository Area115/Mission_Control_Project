import pika
import json
import os
from dotenv import load_dotenv
import time

load_dotenv()

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))
ORDERS_QUEUE = os.getenv("ORDERS_QUEUE", "orders_queue")

class MissionConsumer:
    def __init__(self, on_message_callback):
        self.on_message_callback = on_message_callback

        # Try connecting multiple times in case RabbitMQ isn't ready yet
        for attempt in range(10):
            try:
                connection_params = pika.ConnectionParameters(
                    host=RABBIT_HOST,
                    port=RABBIT_PORT,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=ORDERS_QUEUE, durable=True)
                self.channel.basic_consume(queue="orders_queue", on_message_callback=callback)
                print(f"✅ Soldier connected to RabbitMQ at {RABBIT_HOST}:{RABBIT_PORT} — listening on {ORDERS_QUEUE}")
                break
            except Exception as e:
                print(f"⚠️ Soldier failed to connect to RabbitMQ (attempt {attempt+1}/10): {e}")
                time.sleep(3)
        else:
            raise Exception("❌ Could not connect to RabbitMQ after 10 attempts")

    def start_consuming(self):
        self.channel.basic_consume(
            queue=ORDERS_QUEUE,
            on_message_callback=self.on_message_callback,
            auto_ack=False
        )
        print("🎯 Soldier started consuming missions...")
        self.channel.start_consuming()


if __name__ == "__main__":
    def handle_mission(msg):
        print("➡️ Handling mission:", msg)

    consumer = MissionConsumer(handle_mission)
    consumer.start_consuming()
