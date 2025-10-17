import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))
ORDERS_QUEUE = "orders_queue"


class MissionConsumer:

    def __init__(self, on_message_callback):
        self.on_message_callback = on_message_callback
        try:
            connection_params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
            # self.connection = pika.BlockingConnection(connection_params)
            self.connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq", heartbeat=600, blocked_connection_timeout=300)
)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=ORDERS_QUEUE, durable=True)
            print(f" Soldier connected to RabbitMQ — listening on {ORDERS_QUEUE}")
        except Exception as e:
            print(f" Soldier failed to connect to RabbitMQ: {e}")
            raise

    def start_consuming(self):
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body.decode())
                print(f" Received mission: {message}")
                self.on_message_callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f" Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue=ORDERS_QUEUE, on_message_callback=callback)
        print(" Waiting for missions... Press CTRL+C to stop.")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(" Soldier stopped listening.")
            self.connection.close()

if __name__ == "__main__":
    def handle_mission(msg):
        print("➡️ Handling mission:", msg)

    consumer = MissionConsumer(handle_mission)
    consumer.start_consuming()
