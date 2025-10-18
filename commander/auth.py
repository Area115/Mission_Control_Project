import os
import jwt
import time
from datetime import datetime, timedelta
from jwt import ExpiredSignatureError, InvalidTokenError

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret_key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 30  # Token valid for 30s

active_tokens = {}
def issue_token(soldier_id: str):
    """Issue a short-lived JWT token for the given soldier."""
    now = datetime.utcnow()
    payload = {
        "sub": soldier_id,
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_EXPIRY_SECONDS),
        "scope": "status:publish"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    active_tokens[soldier_id] = {
        "token": token,
        "expires_at": (now + timedelta(seconds=TOKEN_EXPIRY_SECONDS)).isoformat()
    }
    print(f"🔐 Issued new token for Soldier {soldier_id} (valid 30s)")
    return token


def verify_token(token: str):
    """Verify the JWT token received from a soldier."""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except ExpiredSignatureError:
        print("⚠️ Received expired token from soldier")
        return None
    except InvalidTokenError:
        print("⚠️ Invalid token received")
        return None
