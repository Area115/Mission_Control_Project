import pika
import json
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

class StatusPublisher:
    def __init__(self):
        for attempt in range(1, 11):
            try:
                print(f"🕓 Soldier connecting to RabbitMQ ({RABBITMQ_HOST}) attempt {attempt}/10...")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RABBITMQ_HOST,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue="status_queue", durable=True)
                print(f"✅ Soldier connected to RabbitMQ at {RABBITMQ_HOST}: publishing to status_queue")
                break
            except Exception as e:
                print(f"⚠️ Soldier failed to connect to RabbitMQ ({attempt}/10): {e}")
                time.sleep(5)
        else:
            raise Exception("❌ Soldier could not connect to RabbitMQ")

    def publish_status(self, mission_update: dict):
        try:
            # ✅ Ensure it's serialized only once
            message = json.dumps(mission_update)
            self.channel.basic_publish(
                exchange='',
                routing_key='status_queue',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2  # make message persistent
                )
            )
            print(f"📤 Soldier sent update to status_queue: {message}")
        except Exception as e:
            print(f"❌ Error publishing status: {e}")

    def close(self):
        try:
            self.connection.close()
        except:
            pass
