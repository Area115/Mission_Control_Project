import os
import time
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read from .env
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret_change_me")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", 30))

def issue_token(soldier_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": soldier_id,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
        "scope": "status:publish"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token

def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
