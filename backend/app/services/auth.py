"""
Password hashing and JWT issuing/verification for /auth/signup and
/auth/login. Every other protected route depends on get_current_student_id
to identify the caller — no endpoint accepts student_id from the client.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
RESET_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_reset_token() -> tuple[str, str, datetime]:
    """Returns (raw_token, token_hash, expires_at). The raw token is what
    gets sent back to the requester; only its hash is stored in the DB —
    same principle as password_hash, so a DB leak alone can't be used to
    reset accounts."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return raw_token, token_hash, expires_at


def hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(student_id: str) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not set in the environment")
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": student_id, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_student_id(authorization: str = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return payload["sub"]


def get_current_admin_id(authorization: str = Header(default=None)) -> str:
    """Same identity check as get_current_student_id, plus an is_admin gate —
    use this dependency on any route that manages shared data (careers, etc.)
    rather than a single student's own records."""
    from app.services import db

    student_id = get_current_student_id(authorization)
    student = db.get_student_auth_by_id(student_id)
    if not student or not student["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return student_id
