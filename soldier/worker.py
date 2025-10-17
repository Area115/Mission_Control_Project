import pika
import json
import os
import time
from soldier.executer import MissionExecutor


# ===============================
# 🔧 Environment setup
# ===============================
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
SOLDIER_ID = os.getenv("SOLDIER_ID", "1")

ORDERS_QUEUE = f"orders_queue_{SOLDIER_ID}"
STATUS_QUEUE = "status_queue"


# ===============================
# 🪖 Soldier Worker
# ===============================
class MissionConsumer:
    """Listens for missions, executes them if assigned."""

    def __init__(self):
        # Retry RabbitMQ connection until successful
        for attempt in range(1, 11):
            try:
                print(f"🕓 Soldier {SOLDIER_ID}: Connecting to RabbitMQ ({RABBITMQ_HOST}) attempt {attempt}/10...")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RABBITMQ_HOST,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                self.channel = self.connection.channel()

                # Declare queues (durable to survive restarts)
                self.channel.queue_declare(queue=ORDERS_QUEUE, durable=True)
                self.channel.queue_declare(queue=STATUS_QUEUE, durable=True)

                print(f"✅ Soldier {SOLDIER_ID} connected to RabbitMQ — consuming from {ORDERS_QUEUE}")
                break
            except Exception as e:
                print(f"⚠️ Soldier {SOLDIER_ID} failed to connect to RabbitMQ ({attempt}/10): {e}")
                time.sleep(5)
        else:
            raise Exception(f"❌ Soldier {SOLDIER_ID} could not connect to RabbitMQ")

        self.executor = MissionExecutor(SOLDIER_ID)

    # -------------------------------------------------------
    # Consume and process messages
    # -------------------------------------------------------
    def start(self):
        """Start consuming missions for this soldier."""
        print(f"🪖 Soldier {SOLDIER_ID} ready — listening on '{ORDERS_QUEUE}'")

        def callback(ch, method, properties, body):
            try:
                message = body.decode()
                mission = json.loads(message)
                assigned_id = str(mission.get("soldier_id"))

                # Only process missions for this soldier
                if assigned_id != SOLDIER_ID:
                    print(f"🪶 Soldier {SOLDIER_ID}: Mission {mission.get('mission_id')} not for me ({assigned_id}), skipping...")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                print(f"📥 Soldier {SOLDIER_ID} received mission → {mission}")
                self.executor.execute_mission(mission)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"❌ Soldier {SOLDIER_ID} failed to handle mission: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # Limit to one mission at a time
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=ORDERS_QUEUE, on_message_callback=callback)

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(f"🛑 Soldier {SOLDIER_ID} stopped consuming missions.")
            self.channel.stop_consuming()
        except Exception as e:
            print(f"⚠️ Soldier {SOLDIER_ID} consumer stopped unexpectedly: {e}")

    # -------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------
    def close(self):
        try:
            self.executor.close()
            self.connection.close()
        except:
            pass


# ===============================
# 🏁 Entry Point
# ===============================
if __name__ == "__main__":
    print(f"🚀 Starting Soldier Worker ID={SOLDIER_ID}")
    worker = MissionConsumer()
    worker.start()
