import pika
import json
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")


class StatusPublisher:
    """
    Handles publishing mission status updates to RabbitMQ.
    Automatically includes the Soldier's JWT token for Commander verification.
    """

    def __init__(self):
        """Initialize and connect to RabbitMQ with retry logic."""
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

    # --------------------------------------------------------
    # 🔄 Reconnect helper (in case connection drops)
    # --------------------------------------------------------
    def _reconnect(self):
        """Attempt to reconnect if connection to RabbitMQ is lost."""
        try:
            print("♻️ Reconnecting Soldier publisher to RabbitMQ...")
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue="status_queue", durable=True)
            print("✅ Reconnected Soldier publisher to RabbitMQ")
        except Exception as e:
            print(f"❌ Failed to reconnect Soldier publisher: {e}")
            time.sleep(3)

    # --------------------------------------------------------
    # 🛰️ Publish status updates (with JWT token)
    # --------------------------------------------------------
    def publish_status(self, mission_update: dict, token: str = None):
        """
        Publishes mission status to 'status_queue' with optional JWT token.
        Token allows Commander to verify Soldier identity & expiry.
        """
        try:
            # 🟢 Attach current JWT token
            if token:
                mission_update["token"] = token
            else:
                print("⚠️ No token provided for status update!")

            message = json.dumps(mission_update)

            # 🛰️ Send to RabbitMQ
            self.channel.basic_publish(
                exchange='',
                routing_key='status_queue',
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            print(f"📤 Soldier sent update to status_queue: {message}")

        except pika.exceptions.AMQPConnectionError:
            print("⚠️ Lost connection to RabbitMQ — attempting to reconnect...")
            self._reconnect()
            self.publish_status(mission_update, token)

        except Exception as e:
            print(f"❌ Error publishing status: {e}")

    # --------------------------------------------------------
    # 🧹 Graceful shutdown
    # --------------------------------------------------------
    def close(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                print("🧹 Closed RabbitMQ connection for Soldier publisher")
        except Exception as e:
            print(f"⚠️ Error closing Soldier publisher: {e}")
