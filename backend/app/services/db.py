"""
Data access layer — MySQL-backed.

Two tables (see database/schema.sql):
  students — one row per profile, list/dict fields stored as JSON columns.
  careers  — one row per career, auto-seeded from data/careers_seed.json.

Function signatures (save_profile, get_profile, get_all_careers) are the
contract the routers depend on.
"""

import json
import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

CAREERS_SEED_PATH = Path(__file__).parent.parent / "data" / "careers_seed.json"
SCHEMA_PATH = Path(__file__).parent.parent.parent / "database" / "schema.sql"

DB_NAME = os.getenv("MYSQL_DATABASE", "career_mentor")
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "cursorclass": DictCursor,
    "autocommit": True,
}

_JSON_CAREER_FIELDS = (
    "riasec_tags", "relevant_subjects", "required_skills", "interest_tags",
    "courses", "colleges", "scholarships", "certifications",
)
_JSON_STUDENT_FIELDS = ("interests", "hobbies", "riasec_scores", "academics", "self_rated_skills")


@contextmanager
def get_connection():
    conn = pymysql.connect(database=DB_NAME, **DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the database/tables if missing, and seed careers on first run."""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    finally:
        conn.close()

    with get_connection() as conn, conn.cursor() as cur:
        schema_sql = "\n".join(
            line for line in SCHEMA_PATH.read_text().splitlines()
            if not line.strip().startswith("--")
        )
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                cur.execute(statement)

        cur.execute("SELECT COUNT(*) AS n FROM careers")
        if cur.fetchone()["n"] == 0:
            _seed_careers(cur)


def _seed_careers(cur):
    careers = json.loads(CAREERS_SEED_PATH.read_text())
    for c in careers:
        cur.execute(
            """
            INSERT INTO careers
                (id, name, description, riasec_tags, relevant_subjects, required_skills,
                 interest_tags, courses, colleges, scholarships, certifications, emerging)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                c["id"], c["name"], c["description"],
                json.dumps(c["riasec_tags"]),
                json.dumps(c.get("relevant_subjects", [])),
                json.dumps(c.get("required_skills", [])),
                json.dumps(c.get("interest_tags", [])),
                json.dumps(c.get("courses", [])),
                json.dumps(c.get("colleges", [])),
                json.dumps(c.get("scholarships", [])),
                json.dumps(c.get("certifications", [])),
                c.get("emerging", False),
            ),
        )


def _parse_json_fields(row: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if isinstance(row[field], str):
            row[field] = json.loads(row[field])
    return row


def get_all_careers() -> list[dict]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM careers")
        rows = cur.fetchall()
    for row in rows:
        _parse_json_fields(row, _JSON_CAREER_FIELDS)
        row["emerging"] = bool(row["emerging"])
    return rows


def save_profile(profile_data: dict) -> str:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO students (name, interests, hobbies, riasec_scores, academics, self_rated_skills)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                profile_data["name"],
                json.dumps(profile_data["interests"]),
                json.dumps(profile_data["hobbies"]),
                json.dumps(profile_data["riasec_scores"]),
                json.dumps(profile_data["academics"]),
                json.dumps(profile_data["self_rated_skills"]),
            ),
        )
        return str(cur.lastrowid)


def _to_int(student_id: str) -> int | None:
    try:
        return int(student_id)
    except ValueError:
        return None


def get_profile(student_id: str) -> dict | None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return None

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM students WHERE student_id = %s", (numeric_id,))
        row = cur.fetchone()

    if not row:
        return None

    row.pop("student_id", None)
    row.pop("created_at", None)
    return _parse_json_fields(row, _JSON_STUDENT_FIELDS)


# ---- mentor chat history ----

def save_chat_message(student_id: str, sender: str, message: str) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO mentor_chat (student_id, sender, message) VALUES (%s, %s, %s)",
            (numeric_id, sender, message),
        )


def get_chat_history(student_id: str) -> list[dict]:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT sender, message, created_at FROM mentor_chat "
            "WHERE student_id = %s ORDER BY message_id ASC",
            (numeric_id,),
        )
        rows = cur.fetchall()
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return rows


# ---- roadmap progress ----

def save_roadmap(student_id: str, career: str, steps: list[str]) -> list[dict]:
    """Replace any existing roadmap for this student+career with a fresh one."""
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return []

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM roadmap_steps WHERE student_id = %s AND career = %s",
            (numeric_id, career),
        )
        for i, description in enumerate(steps, start=1):
            cur.execute(
                "INSERT INTO roadmap_steps (student_id, career, step_number, description) "
                "VALUES (%s, %s, %s, %s)",
                (numeric_id, career, i, description),
            )

        cur.execute(
            "SELECT step_id, career, step_number, description, completed FROM roadmap_steps "
            "WHERE student_id = %s AND career = %s ORDER BY step_number ASC",
            (numeric_id, career),
        )
        rows = cur.fetchall()

    for row in rows:
        row["completed"] = bool(row["completed"])
    return rows


def get_roadmap(student_id: str) -> list[dict]:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT step_id, career, step_number, description, completed FROM roadmap_steps "
            "WHERE student_id = %s ORDER BY career ASC, step_number ASC",
            (numeric_id,),
        )
        rows = cur.fetchall()
    for row in rows:
        row["completed"] = bool(row["completed"])
    return rows


def update_roadmap_step(student_id: str, step_id: int, completed: bool) -> dict | None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE roadmap_steps SET completed = %s WHERE step_id = %s AND student_id = %s",
            (completed, step_id, numeric_id),
        )
        if cur.rowcount == 0:
            return None
        cur.execute(
            "SELECT step_id, career, step_number, description, completed FROM roadmap_steps "
            "WHERE step_id = %s",
            (step_id,),
        )
        row = cur.fetchone()
    row["completed"] = bool(row["completed"])
    return row
