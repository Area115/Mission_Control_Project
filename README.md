🪖 Commander–Soldier Distributed Mission Control System

A fully containerized distributed system built with FastAPI, RabbitMQ, Redis, and Docker Compose.
The Commander issues missions, and multiple Soldiers execute them in parallel — with live mission tracking, JWT-based soldier authentication, and task queueing.

🌍 Project Overview

This project simulates a real-time distributed control system where:

The Commander (FastAPI app) assigns missions to multiple Soldiers.

Each Soldier (Python worker) executes tasks asynchronously and reports progress.

Communication happens via RabbitMQ message queues.

Mission status is stored in Redis for real-time tracking.

Everything is orchestrated using Docker Compose, so anyone can run it instantly.
🚀 Note : This system is made up for two soldiers, so only soldier_id: 1 or 2 will be processed others will be in queue and not being processed.
Example : 
{
  "soldier_id": "2",
  "objective": "Climb Tiger Hill",
  "priority": "MEDIUM"
}

{
  "soldier_id": "2",
  "objective": "Check CCTV",
  "priority": "LOW"
}

{
  "soldier_id": "1",
  "objective": "Attend Morning parade",
  "priority": "HIGH"
}
These are acceptable.
graph LR
    A[Commander API (FastAPI)] -->|Publishes Mission| B[(RabbitMQ Orders Queue)]
    B --> C1[Soldier #1 Worker]
    B --> C2[Soldier #2 Worker]
    C1 -->|Status Updates| D[(RabbitMQ Status Queue)]
    C2 -->|Status Updates| D
    D -->|Update Redis| E[(Redis Mission Store)]
    E -->|Queried by| A
| Component            | Technology              | Purpose                                               |
| -------------------- | ----------------------- | ----------------------------------------------------- |
| **Backend API**      | FastAPI (Python)        | Commander interface to send & query missions          |
| **Messaging Queue**  | RabbitMQ                | Async communication between Commander and Soldiers    |
| **Data Store**       | Redis                   | Persistent tracking of mission statuses               |
| **Auth**             | JWT Tokens              | Temporary tokens per soldier for secure communication |
| **Containerization** | Docker & Docker Compose | Seamless multi-service orchestration                  |

⚙️ System Workflow

Commander issues a mission
→ Sends mission JSON via /missions API.

Mission is published to RabbitMQ (orders_queue).

Soldiers consume their respective missions, execute them, and simulate progress.

Soldiers send updates back to status_queue.

Commander listens for updates and stores mission status in Redis.

JWT tokens for each soldier are refreshed every 25 seconds automatically.


🚀 Getting Started (for anyone)
1️⃣ Prerequisites

Install Docker Desktop

Verify installation:

docker --version
docker compose version

2️⃣ Clone or unzip the project
git clone https://github.com/<your-username>/commander-soldier-control.git
cd commander-soldier-control

3️⃣ (Optional) Create .env file

In the project root:

# .env
JWT_SECRET=supersecret_change_me
REDIS_HOST=redis
RABBITMQ_HOST=rabbitmq
COMMANDER_BASE=http://commander:8000
JOB_EXECUTION_TIME=10

4️⃣ Start the system
docker compose up --build


This will:

Build all Docker images

Start Commander, Soldiers, Redis, and RabbitMQ

Automatically connect all services

Wait until logs show messages like:

✅ Commander connected to RabbitMQ (rabbitmq)
🪖 Soldier started with ID=1
🔐 Received JWT for soldier 1

5️⃣ Test the API

Open the interactive Swagger UI:

👉 http://localhost:8000/docs

Use the POST /missions endpoint:

{
  "soldier_id": "1",
  "objective": "Secure Tiger Hill",
  "priority": "HIGH"
}


You’ll get a response:

{
  "mission_id": "abcd-1234...",
  "status": "QUEUED"
}


Then check mission progress:

GET /missions/{mission_id}


It will change as:

QUEUED → IN_PROGRESS → COMPLETED

6️⃣ View RabbitMQ Dashboard

👉 http://localhost:15672

Username: guest
Password: guest

You’ll see:

orders_queue → new missions

status_queue → soldier status updates

7️⃣ View Redis Data (optional)

You can enter the Redis container:

docker exec -it redis redis-cli
keys *
get mission:<mission_id>

8️⃣ Stop the system
docker compose down

Clean everything (remove volumes):

docker compose down --volumes

| Method | Endpoint                 | Description                                                         |
| ------ | ------------------------ | ------------------------------------------------------------------- |
| `POST` | `/missions`              | Assign new mission to soldier                                       |
| `GET`  | `/missions/{mission_id}` | Get mission status                                                  |
| `GET`  | `/auth/token`            | Fetch JWT token for a soldier                                       |
| `GET`  | `/soldiers/status`       | *(Optional)* Get list of active soldiers and their current missions |

🧱 Project Structure
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

🧰 Useful Docker Commands
| Action                    | Command                              |
| ------------------------- | ------------------------------------ |
| Start everything          | `docker compose up --build`          |
| Stop containers           | `docker compose down`                |
| Check logs                | `docker logs commander --tail 50 -f` |
| Rebuild after code change | `docker compose up -d --build`       |
| List containers           | `docker ps`                          |
| Enter container           | `docker exec -it commander bash`     |

