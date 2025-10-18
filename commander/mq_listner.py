import os
import pika
import json
import redis
import threading
import time
from commander.auth import verify_token  # 🟢 NEW — import token verifier

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

class StatusListener:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

        # Retry connection to RabbitMQ until it’s ready
        for attempt in range(1, 11):
            try:
                print(f"🐇 Connecting to RabbitMQ ({RABBIT_HOST}) attempt {attempt}/10...")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RABBIT_HOST,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue="status_queue", durable=True)
                print("📡 Commander listening to status_queue for mission updates")
                break
            except Exception as e:
                print(f"⚠️ RabbitMQ not ready yet: {e}")
                time.sleep(5)
        else:
            raise Exception("❌ Could not connect to RabbitMQ after retries")

    def start(self):
        """Continuously consume mission updates from status_queue."""
        def callback(ch, method, properties, body):
            try:
                raw_message = body.decode().strip()
                print(f"📨 Raw message from status_queue: '{raw_message}'")

                # Parse JSON
                update = json.loads(raw_message)

                # 🟢 Step 1: Extract and verify token
                token = update.get("token")
                if not token:
                    print("⚠️ Missing token in update — ignoring message.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                decoded = verify_token(token)
                if not decoded:
                    print("🚫 Invalid or expired token — ignoring message.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # 🟢 Step 2: Verify mission data
                mission_id = update.get("mission_id")
                new_status = update.get("status")

                if not mission_id:
                    print("⚠️ Missing mission_id in update")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                key = f"mission:{mission_id}"
                mission_json = self.redis.get(key)
                if mission_json:
                    mission_data = json.loads(mission_json)
                    mission_data["status"] = new_status
                    self.redis.set(key, json.dumps(mission_data))
                    print(f"✅ Updated Redis for {mission_id} → {new_status}")
                else:
                    print(f"⚠️ Mission {mission_id} not found in Redis")

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except json.JSONDecodeError:
                print("❌ Received non-JSON message in status_queue.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"❌ Error handling message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue="status_queue", on_message_callback=callback)

        print("🛰️ Commander actively consuming from status_queue...")
        self.channel.start_consuming()


def start_status_listener():
    """Run the listener in a background thread."""
    def run():
        listener = StatusListener()
        listener.start()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🛰️ Commander background listener started ✅")
