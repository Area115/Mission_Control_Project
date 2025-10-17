import os
import time
import uuid
import traceback
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from collections import defaultdict
# Commander modules
from commander.auth import issue_token, verify_token
from commander.redis_client import MissionStore
from commander.mq_publisher import MissionPublisher
from commander.mq_listner import StatusListener  # ✅ correct spelling and placement

# -------------------------------------------------------------------
# 🧩 Global setup
# -------------------------------------------------------------------

# Track active soldiers and their tokens
active_soldiers = {}

# Shared mission storage (Redis)
mission_store = MissionStore()

# RabbitMQ publisher
mission_publisher = MissionPublisher()

# Start background status listener (thread)
from threading import Thread

def start_status_listener():
    listener = StatusListener(mission_store)
    listener.start_listening()

listener_thread = Thread(target=start_status_listener, daemon=True)
listener_thread.start()


# -------------------------------------------------------------------
# 🧠 FastAPI App Initialization
# -------------------------------------------------------------------

app = FastAPI(title="Commander's Camp API", version="1.0")


# -------------------------------------------------------------------
# 🔐 AUTH ENDPOINT — Issues JWT Token
# -------------------------------------------------------------------
@app.get("/auth/token")
def get_token(soldier_id: str = Query(..., description="Soldier ID requesting token")):
    try:
        token = issue_token(soldier_id)
        return {"token": token, "ttl_seconds": int(os.getenv("JWT_TTL_SECONDS", 30))}
    except Exception as e:
        print("AUTH TOKEN ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to issue token: {e}")


# -------------------------------------------------------------------
# 🎯 Mission Request Model
# -------------------------------------------------------------------
class MissionRequest(BaseModel):
    soldier_id: str = Field(..., description="Target soldier ID (string or numeric-as-string)")
    objective: str
    priority: str = "MEDIUM"


# -------------------------------------------------------------------
# 🚀 CREATE MISSION ENDPOINT
# -------------------------------------------------------------------
@app.post("/missions", status_code=202)
def create_mission(mission: MissionRequest):

    mission_id = str(uuid.uuid4())

    # ✅ 1️⃣ Check if soldier already has an active mission
    active_missions = mission_store.get_all_missions_for_soldier(mission.soldier_id)
    if any(m["status"] in ["QUEUED", "IN_PROGRESS"] for m in active_missions):
        return {"detail": f"Soldier {mission.soldier_id} already has an active mission."}

    # ✅ 2️⃣ Issue or reuse token
    if mission.soldier_id not in active_soldiers:
        token = issue_token(mission.soldier_id)
        active_soldiers[mission.soldier_id] = {"token": token, "issued_at": time.time()}
        print(f"🎫 Issued new token for soldier {mission.soldier_id}")
    else:
        token = active_soldiers[mission.soldier_id]["token"]

    # ✅ 3️⃣ Prepare mission payload
    mission_payload = {
        "mission_id": mission_id,
        "soldier_id": mission.soldier_id,
        "objective": mission.objective,
        "priority": mission.priority,
        "status": "QUEUED",
        "token": token,
    }

    # ✅ 4️⃣ Store mission & publish to RabbitMQ
    mission_store.add_mission(mission_id, mission_payload)
    mission_publisher.publish(mission_payload)

    print(f"📤 Mission published to orders_queue: {mission_payload}")
    return {"mission_id": mission_id, "status": "QUEUED"}


# -------------------------------------------------------------------
# 📡 GET MISSION STATUS ENDPOINT
# -------------------------------------------------------------------
@app.get("/missions/{mission_id}")
def get_mission_status(mission_id: str):
    mission = mission_store.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"mission_id": mission_id, "status": mission.get("status", "UNKNOWN")}


# -------------------------------------------------------------------
# 🧹 Graceful Shutdown
# -------------------------------------------------------------------
@app.on_event("shutdown")
def shutdown_event():
    try:
        mission_publisher.close()
        print("Closed MissionPublisher connection.")
    except Exception:
        pass


@app.get("/soldiers/status")
def get_all_soldier_status():
    all_missions = mission_store.get_all_missions()

    # Group by soldier_id
    grouped = defaultdict(list)
    for mission in all_missions:
        soldier_id = mission.get("soldier_id", "unknown")
        grouped[soldier_id].append({
            "mission_id": mission.get("mission_id"),
            "objective": mission.get("objective"),
            "status": mission.get("status", "UNKNOWN"),
        })

    # Convert to list of dicts
    response = []
    for soldier_id, missions in grouped.items():
        response.append({
            "soldier_id": soldier_id,
            "missions": missions
        })

    return response
