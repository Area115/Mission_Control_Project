import pika
import json
import time
import os

class MissionPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        for attempt in range(10):
            try:
                print(f" [Commander] Connecting to RabbitMQ at {host} (attempt {attempt+1}/10)...")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host, heartbeat=600, blocked_connection_timeout=300)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue="orders_queue", durable=True)
                print(f" Commander connected to RabbitMQ ({host}) — ready to publish to orders_queue")
                return
            except Exception as e:
                print(f" Failed to connect to RabbitMQ: {e}")
                time.sleep(5)
        print(" Could not connect to RabbitMQ after multiple attempts.")
        self.connection = None
        self.channel = None

    # 👇 Add this method to actually publish messages
    def publish(self, mission_data: dict):
        if not self.channel or self.channel.is_closed:
            print(" RabbitMQ channel not available — reconnecting...")
            self.connect()
            if not self.channel:
                print(" Unable to publish mission — no active RabbitMQ channel.")
                return

        try:
            message = json.dumps(mission_data)
            self.channel.basic_publish(
                exchange="",
                routing_key="orders_queue",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2  # make message persistent
                ),
            )
            print(f" Mission published to orders_queue: {message}")
        except Exception as e:
            print(f" Failed to publish mission: {e}")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print(" Closed RabbitMQ connection.")
