import requests
import time
import json

# ===============================
# ⚙️ Configuration
# ===============================
COMMANDER_URL = "http://localhost:8000"
MISSIONS_ENDPOINT = f"{COMMANDER_URL}/missions"

# Define test missions
TEST_MISSIONS = [
    {"soldier_id": "1", "objective": "Secure North Base", "priority": "HIGH"},
    {"soldier_id": "2", "objective": "Scan CCTV Feeds", "priority": "MEDIUM"},
    {"soldier_id": "1", "objective": "Guard Entry Gate", "priority": "LOW"}
]


# ===============================
# 🪖 Helper Functions
# ===============================

def wait_for_commander():
    """Wait for Commander API to become available."""
    print("⏳ Checking Commander API availability...")
    for i in range(10):
        try:
            res = requests.get(COMMANDER_URL, timeout=3)
            if res.status_code == 200:
                print("✅ Commander API is online!")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"⚠️ Commander not ready (retry {i+1}/10)...")
        time.sleep(3)
    print("❌ Commander API not reachable. Please ensure docker compose is running.")
    return False


def create_mission(mission):
    """POST a mission to Commander."""
    try:
        res = requests.post(MISSIONS_ENDPOINT, json=mission, timeout=5)
        if res.status_code == 200:
            mission_id = res.json().get("mission_id")
            print(f"🪖 Mission created → {mission_id} for Soldier {mission['soldier_id']}")
            return mission_id
        else:
            print(f"⚠️ Failed to create mission ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ Error creating mission: {e}")
    return None


def get_mission_status(mission_id):
    """Fetch a specific mission’s status."""
    try:
        res = requests.get(f"{MISSIONS_ENDPOINT}/{mission_id}", timeout=5)
        if res.status_code == 200:
            return res.json().get("status")
    except Exception as e:
        print(f"⚠️ Error fetching status for {mission_id}: {e}")
    return None


# ===============================
# 🧪 Test Flow
# ===============================
def run_test():
    print("\n🚀 Starting Distributed Mission System Test (LOCAL MODE)...\n")

    # Step 1️⃣ — Ensure Commander is running
    if not wait_for_commander():
        return

    # Step 2️⃣ — Create test missions
    mission_ids = []
    for mission in TEST_MISSIONS:
        mission_id = create_mission(mission)
        if mission_id:
            mission_ids.append(mission_id)

    if not mission_ids:
        print("❌ No missions created. Exiting test.")
        return

    print("\n⏳ Monitoring mission progress...\n")

    # Step 3️⃣ — Poll missions for up to 60s
    start_time = time.time()
    completed = {}

    while time.time() - start_time < 60:
        all_done = True
        for mission_id in mission_ids:
            if mission_id in completed:
                continue

            status = get_mission_status(mission_id)
            if not status:
                continue

            print(f"📡 Mission {mission_id[:8]} → {status}")

            if status == "COMPLETED":
                completed[mission_id] = "✅ COMPLETED"
            elif status == "FAILED":
                completed[mission_id] = "❌ FAILED"
            else:
                all_done = False

        if all_done:
            break
        time.sleep(3)

    # Step 4️⃣ — Final Report
    print("\n🧾 FINAL MISSION REPORT")
    print("-" * 40)
    for mid in mission_ids:
        result = completed.get(mid, "⏳ TIMEOUT or UNKNOWN")
        print(f"🪖 {mid[:8]} → {result}")
    print("-" * 40)
    print("\n🎯 Local Test Completed!\n")


# ===============================
# 🏁 Entry Point
# ===============================
if __name__ == "__main__":
    run_test()
