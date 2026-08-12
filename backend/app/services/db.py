"""
Data access layer — MySQL-backed.

Tables (see database/schema.sql):
  students     — one row per student, created by /auth/signup and uniquely
                 identified by email. Profile fields (interests, hobbies,
                 riasec_scores, academics, self_rated_skills) start empty
                 and are filled in later via update_profile.
  careers      — one row per career, auto-seeded from data/careers_seed.json.
  mentor_chat  — chat history, one row per message.
  roadmap_steps — roadmap steps generated per student+career.

Function signatures are the contract routers depend on.
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
_JSON_STUDENT_FIELDS = ("interests", "hobbies", "riasec_answers", "riasec_scores", "academics", "self_rated_skills")


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

        _ensure_column(cur, "students", "email", "VARCHAR(255) UNIQUE AFTER name")
        _ensure_column(cur, "students", "password_hash", "VARCHAR(255) AFTER email")
        _ensure_column(cur, "students", "riasec_answers", "JSON AFTER hobbies")


def _ensure_column(cur, table: str, column: str, ddl_fragment: str):
    """Migrate tables created before this column existed (schema.sql's
    CREATE TABLE IF NOT EXISTS won't add it to an already-existing table)."""
    cur.execute(
        "SELECT COUNT(*) AS n FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
        (DB_NAME, table, column),
    )
    if cur.fetchone()["n"] == 0:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_fragment}")


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


def create_account(name: str, email: str, password_hash: str) -> str:
    """Signup: creates the student row with empty profile fields, filled in
    later via update_profile once the student completes the intake form."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO students (name, email, password_hash, interests, hobbies,
                                   riasec_scores, academics, self_rated_skills)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, password_hash, "[]", "[]", "{}", "{}", "{}"),
        )
        return str(cur.lastrowid)


def get_student_auth_by_email(email: str) -> dict | None:
    """Returns {student_id, name, email, password_hash} for login, or None."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT student_id, name, email, password_hash FROM students WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def update_profile(student_id: str, profile_fields: dict) -> None:
    """Overwrites the intake fields for an existing student (created at signup)."""
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE students
            SET interests = %s, hobbies = %s, riasec_answers = %s, riasec_scores = %s,
                academics = %s, self_rated_skills = %s
            WHERE student_id = %s
            """,
            (
                json.dumps(profile_fields["interests"]),
                json.dumps(profile_fields["hobbies"]),
                json.dumps(profile_fields["riasec_answers"]),
                json.dumps(profile_fields["riasec_scores"]),
                json.dumps(profile_fields["academics"]),
                json.dumps(profile_fields["self_rated_skills"]),
                numeric_id,
            ),
        )


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
    row.pop("password_hash", None)
    row = _parse_json_fields(row, _JSON_STUDENT_FIELDS)
    if row["riasec_answers"] is None:
        row["riasec_answers"] = []
    return row


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


# ---- AI insights (persisted so the dashboard doesn't lose them on reload) ----

def save_insights(student_id: str, top_career: str, explanations: dict, emerging_trend: str) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO insights (student_id, top_career, explanations, emerging_trend)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                top_career = VALUES(top_career),
                explanations = VALUES(explanations),
                emerging_trend = VALUES(emerging_trend)
            """,
            (numeric_id, top_career, json.dumps(explanations), emerging_trend),
        )


def get_insights(student_id: str) -> dict | None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT top_career, explanations, emerging_trend FROM insights WHERE student_id = %s",
            (numeric_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    if isinstance(row["explanations"], str):
        row["explanations"] = json.loads(row["explanations"])
    return row
