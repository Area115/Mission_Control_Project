import pika
import json
import time
import os

class StatusListener:
    def __init__(self, mission_store):
        self.mission_store = mission_store
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        for attempt in range(10):
            try:
                print(f" [Commander] Connecting to RabbitMQ at {host} (attempt {attempt+1}/10)...")
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue="status_queue", durable=True)
                print(f"✅ [Commander] Connected to RabbitMQ ({host}) — listening on 'status_queue'")
                return
            except Exception as e:
                print(f"Failed to connect to RabbitMQ: {e}")
                time.sleep(5)
        print(" Could not connect to RabbitMQ after multiple attempts.")
        self.connection = None
        self.channel = None

    # 👇 THIS is the missing callback function
    def _callback(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            mission_id = data.get("mission_id")
            status = data.get("status")
            print(f" Received status update → {data}")

            if mission_id and status:
                self.mission_store.update_status(mission_id, status)
                print(f"Mission {mission_id} updated to {status}")
            else:
                print(f" Invalid message payload: {data}")

        except Exception as e:
            print(f" Error processing message: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_listening(self):
        if not self.channel:
            print(" No RabbitMQ channel available for listening.")
            return

        print(" [Commander] Listening for soldier status updates...")
        self.channel.basic_consume(
            queue="status_queue",
            on_message_callback=self._callback,
            auto_ack=False
        )
        self.channel.start_consuming()
