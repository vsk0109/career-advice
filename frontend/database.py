from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import uuid
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "career_ai_demo.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_states (
                email TEXT PRIMARY KEY,
                state_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email)
            )
        """)


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000,
    ).hex()


def create_user(name: str, email: str, password: str):
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as connection:
            student_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO users
                (student_id, name, email, password_salt, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, name.strip().title(), email, salt, password_hash),
            )
            connection.execute(
                "INSERT INTO student_states (email, state_json) VALUES (?, ?)",
                (email, "{}"),
            )

        return {
            "student_id": student_id,
            "name": name.strip().title(),
            "email": email,
        }, ""

    except sqlite3.IntegrityError:
        return None, "An account with this email already exists. Please log in instead."


def authenticate_user(email: str, password: str):
    email = email.strip().lower()

    with get_connection() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user:
        return None, "No account was found with this email. Please create an account first."

    entered_hash = hash_password(password, user["password_salt"])

    if not hmac.compare_digest(entered_hash, user["password_hash"]):
        return None, "Incorrect password. Please try again."

    return {
        "student_id": user["student_id"],
        "name": user["name"],
        "email": user["email"],
    }, ""


def save_student_state(email: str, state: dict):
    safe_state = json.dumps(state, ensure_ascii=False, default=str)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO student_states (email, state_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (email.strip().lower(), safe_state),
        )


def load_student_state(email: str) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT state_json FROM student_states WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    if not row:
        return {}

    try:
        return json.loads(row["state_json"])
    except json.JSONDecodeError:
        return {}


def list_users() -> list[dict[str, str]]:
    """Return non-sensitive account details for the protected admin page."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT student_id, name, email, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_user(email: str) -> bool:
    """Permanently delete a user and their saved quiz/profile data."""
    clean_email = email.strip().lower()
    with get_connection() as connection:
        connection.execute("DELETE FROM student_states WHERE email = ?", (clean_email,))
        result = connection.execute("DELETE FROM users WHERE email = ?", (clean_email,))
    return result.rowcount > 0
