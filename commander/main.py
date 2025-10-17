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
# @app.get("/auth/token")
# def get_token(soldier_id: str = Query(..., description="Soldier ID requesting token")):
#     try:
#         token = issue_token(soldier_id)
#         return {"token": token, "ttl_seconds": int(os.getenv("JWT_TTL_SECONDS", 30))}
#     except Exception as e:
#         print("AUTH TOKEN ERROR:")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Failed to issue token: {e}")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", 30))

@app.get("/auth/token")
def get_token(soldier_id: str = Query(...)):
    """Issue a new JWT for a soldier."""
    token = issue_token(soldier_id)
    issued_at = time.time()
    expires_at = issued_at + JWT_TTL_SECONDS
    active_soldiers[soldier_id] = {
        "token": token,
        "issued_at": issued_at,
        "expires_at": expires_at
    }
    return {"token": token, "ttl_seconds": JWT_TTL_SECONDS}


@app.get("/auth/current-token")
def get_current_token(soldier_id: str = Query(...)):
    """Return the current active JWT for a soldier, if available."""
    token_info = active_soldiers.get(soldier_id)
    if not token_info:
        raise HTTPException(status_code=404, detail=f"No active token found for soldier {soldier_id}")

    # fallback for old tokens that don’t have 'expires_at'
    issued_at = token_info.get("issued_at", time.time())
    expires_at = token_info.get("expires_at", issued_at + JWT_TTL_SECONDS)

    remaining = max(0, int(expires_at - time.time()))
    return {
        "soldier_id": soldier_id,
        "current_token": token_info.get("token", "unknown"),
        "expires_in": remaining
    }


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
    token = issue_token(mission.soldier_id)
    mission_payload = {
        "mission_id": mission_id,
        "soldier_id": mission.soldier_id,
        "objective": mission.objective,
        "priority": mission.priority,
        "status": "QUEUED",
        "token": token
    }

    # Check if soldier is already busy
    active_missions = mission_store.get_all_missions_for_soldier(mission.soldier_id)
    busy = any(m["status"] == "IN_PROGRESS" for m in active_missions)


    # commander/main.py in POST /missions (busy path)
    if busy:
        mission_payload["token"] = issue_token(mission.soldier_id)
        mission_store.enqueue_mission_for_soldier(mission.soldier_id, mission_payload)
        mission_store.add_mission(mission_id, mission_payload)
        return {"mission_id": mission_id, "status": "QUEUED (waiting)"}



    # If soldier is free
    mission_store.add_mission(mission_id, mission_payload)
    publisher = MissionPublisher()
    publisher.publish(mission_payload)
    print(f"📤 Mission published immediately → {mission_payload}")
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
