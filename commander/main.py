from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import uuid
import json
import os
import time
import threading

# ✅ Import publisher & listener
from commander.mq_publisher import MissionPublisher
from commander.mq_listner import StatusListener   

# ===============================
# 🔧 Redis setup with retry logic
# ===============================
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
r = None
for attempt in range(1, 6):
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        r.ping()
        print(f"✅ Connected to Redis at {REDIS_HOST}")
        break
    except Exception as e:
        print(f"⚠️ Redis not ready yet ({attempt}/5): {e}")
        time.sleep(3)

if not r:
    raise Exception("❌ Could not connect to Redis after retries")

# ===============================
# 🚀 FastAPI App Setup
# ===============================
app = FastAPI(title="🪖 Commander Mission Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# 🛰️ Safe Background Listener Startup
# ===============================
@app.on_event("startup")
def on_startup():
    """Start the background listener safely after API is up."""
    def start_listener_in_thread():
        try:
            listener = StatusListener()
            thread = threading.Thread(target=listener.start, daemon=True)
            thread.start()
            print("🛰️ Commander background listener started ✅")
        except Exception as e:
            print(f"❌ Failed to start listener: {e}")

    # Start in a separate thread after a small delay to ensure RabbitMQ is ready
    threading.Timer(5.0, start_listener_in_thread).start()


# ===============================
# 📦 Mission Model
# ===============================
class Mission(BaseModel):
    soldier_id: str
    objective: str
    priority: str


# ===============================
# 🏠 Root Route
# ===============================
@app.get("/")
def root():
    return {"message": "Commander API running 🚀"}


# ===============================
# 🎯 Create Mission
# ===============================
@app.post("/missions")
def create_mission(mission: Mission):
    """Create a mission, save to Redis, and publish to RabbitMQ."""
    try:
        mission_id = str(uuid.uuid4())
        mission_data = {
            "mission_id": mission_id,
            "soldier_id": mission.soldier_id,
            "objective": mission.objective,
            "priority": mission.priority,
            "status": "QUEUED"
        }

        # ✅ Step 1: Save mission in Redis immediately
        r.set(f"mission:{mission_id}", json.dumps(mission_data))
        print(f"💾 Mission saved to Redis: mission:{mission_id}")

        # ✅ Step 2: Publish to RabbitMQ
        publisher = MissionPublisher()
        publisher.publish_mission(mission_data)
        publisher.close()

        return {"message": "Mission assigned", "mission_id": mission_id}

    except Exception as e:
        print(f"❌ Error creating mission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 📋 Get All Missions
# ===============================
@app.get("/missions")
def get_all_missions():
    """Fetch all missions from Redis (with latest status)."""
    try:
        keys = r.keys("mission:*")
        missions = []
        for k in keys:
            data = r.get(k)
            if not data:
                continue
            try:
                mission = json.loads(data)
                missions.append(mission)
            except Exception as e:
                print(f"⚠️ Could not decode Redis data for {k}: {e}")
        return missions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 🔍 Get Specific Mission by ID
# ===============================
@app.get("/missions/{mission_id}")
def get_mission_status(mission_id: str):
    """Return specific mission by ID"""
    data = r.get(f"mission:{mission_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Mission not found")
    return json.loads(data)
