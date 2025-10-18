# 🪖 Commander–Soldier Distributed Mission Control System

A **fully containerized distributed system** built with **FastAPI**, **RabbitMQ**, **Redis**, and **Docker Compose**.  
The **Commander** issues missions, and multiple **Soldiers** execute them in parallel — with live mission tracking, **JWT-based authentication**, and **task queueing**.

---

## 🌍 Project Overview

This project simulates a **real-time distributed control system** where:

- 🧭 **Commander (FastAPI app)** assigns missions to multiple Soldiers.  
- ⚙️ **Each Soldier (Python worker)** executes tasks asynchronously and reports progress.  
- 📬 **RabbitMQ** handles message-based communication.  
- 💾 **Redis** stores mission statuses for real-time tracking.  
- 🐳 **Docker Compose** orchestrates everything for easy deployment.

> 🪶 **Note:**  
> This system is configured for **two soldiers only**.  
> Missions for other soldier IDs will remain **queued**.

### ✅ Example Missions

```json
{
  "soldier_id": "2",
  "objective": "Climb Tiger Hill",
  "priority": "MEDIUM"
}
```

```json
{
  "soldier_id": "2",
  "objective": "Check CCTV",
  "priority": "LOW"
}
```

```json
{
  "soldier_id": "1",
  "objective": "Attend Morning Parade",
  "priority": "HIGH"
}
```

---



| Component | Technology | Purpose |
|------------|-------------|----------|
| **Backend API** | FastAPI (Python) | Commander interface to send & query missions |
| **Messaging Queue** | RabbitMQ | Async communication between Commander and Soldiers |
| **Data Store** | Redis | Persistent tracking of mission statuses |
| **Auth** | JWT Tokens | Secure communication per soldier |
| **Containerization** | Docker & Docker Compose | Seamless multi-service orchestration |

---

![image alt](https://github.com/Area115/Mission_Control_Project/blob/6e59ca0f1d988d73e2114d7149b90ef2d56251e3/MCP.png)


## ⚙️ System Workflow

1. Commander issues a mission via `/missions` API.  
2. Mission is **published** to RabbitMQ (`orders_queue`).  
3. Soldiers **consume** their respective missions and simulate execution.  
4. Soldiers **send updates** to `status_queue`.  
5. Commander **updates mission status** in Redis.  
6. JWT tokens for soldiers are **auto-refreshed every 25 seconds**.

---

## 🚀 Getting Started

### 1️⃣ Prerequisites

- Install **Docker Desktop**  
- Verify installation:

```bash
docker --version
docker compose version
```

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/commander-soldier-control.git
cd commander-soldier-control
```

---

### 3️⃣ (Optional) Create a `.env` File

```bash
# .env
JWT_SECRET=supersecret_change_me
REDIS_HOST=redis
RABBITMQ_HOST=rabbitmq
COMMANDER_BASE=http://commander:8000
JOB_EXECUTION_TIME=10
```

---

### 4️⃣ Start the System

```bash
docker compose up --build
```

This will:

- Build all Docker images  
- Start Commander, Soldiers, Redis, and RabbitMQ  
- Connect all services automatically  

You should see logs like:

```
✅ Commander connected to RabbitMQ (rabbitmq)
🪖 Soldier started with ID=1
🔐 Received JWT for soldier 1
```

---

### 5️⃣ Test the API

Open Swagger UI:

👉 [http://localhost:8000/docs](http://localhost:8000/docs)

**POST /missions**

```json
{
  "soldier_id": "1",
  "objective": "Secure Tiger Hill",
  "priority": "HIGH"
}
```

**Response:**

```json
{
  "mission_id": "abcd-1234...",
  "status": "QUEUED"
}
```

**GET /missions/{mission_id}**

Status will change as:

```
QUEUED → IN_PROGRESS → COMPLETED
```

---

### 6️⃣ View RabbitMQ Dashboard

👉 [http://localhost:15672](http://localhost:15672)

```
Username: guest
Password: guest
```

You’ll see:

- `orders_queue` → new missions  
- `status_queue` → soldier status updates

---

### 7️⃣ View Redis Data (Optional)

```bash
docker exec -it redis redis-cli
keys *
get mission:<mission_id>
```

---

### 8️⃣ Stop the System

```bash
docker compose down
```

Clean everything (remove volumes):

```bash
docker compose down --volumes
```

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/missions` | Assign new mission to soldier |
| `GET`  | `/missions/{mission_id}` | Get mission status |
| `GET`  | `/auth/token` | Fetch JWT token for a soldier |
| `GET`  | `/soldiers/status` | *(Optional)* Get list of active soldiers and their current missions |

---

## 🧱 Project Structure

```
MCP/
├── commander/
│   ├── main.py                # FastAPI app (Commander)
│   ├── auth.py                # JWT issue/verify logic
│   ├── mq_publisher.py        # Publishes missions to RabbitMQ
│   ├── mq_listener.py         # Listens for status updates
│   └── redis_client.py        # Redis storage layer
│
├── soldier/
│   ├── worker.py              # Soldier task worker
│   ├── executer.py            # Simulates mission execution
│   ├── auth_client.py         # Handles JWT token refresh
│   ├── mq_consumer.py         # Consumes mission queue
│   └── mq_publisher.py        # Sends status updates
│
├── docker-compose.yml         # Multi-container orchestration
├── Dockerfile.commander       # Build Commander image
├── Dockerfile.soldier         # Build Soldier image
├── .env                       # Environment configuration
└── README.md                  # You’re here 🚀
```

---

## 🧰 Useful Docker Commands

| Action | Command |
|--------|----------|
| Start everything | `docker compose up --build` |
| Stop containers | `docker compose down` |
| Check logs | `docker logs commander --tail 50 -f` |
| Rebuild after code change | `docker compose up -d --build` |
| List containers | `docker ps` |
| Enter container | `docker exec -it commander bash` |

---


