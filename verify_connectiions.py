import redis
import pika

print("🔹 Checking Redis...")
try:
    r = redis.Redis(host="localhost", port=6379)
    r.ping()
    print("✅ Redis connection OK")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")

print("\n🔹 Checking RabbitMQ...")
try:
    conn = pika.BlockingConnection(pika.ConnectionParameters(host="localhost", port=5672))
    ch = conn.channel()
    print("✅ RabbitMQ connection OK")
    conn.close()
except Exception as e:
    print(f"❌ RabbitMQ connection failed: {e}")
