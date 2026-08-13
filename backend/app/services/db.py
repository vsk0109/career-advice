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
COLLEGES_SEED_PATH = Path(__file__).parent.parent / "data" / "colleges_seed.json"
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

# Managed MySQL providers (Aiven, PlanetScale, RDS, ...) require TLS and give
# you a CA certificate to verify against. Local MySQL has no such cert, so
# this stays opt-in — unset locally, DB_CONFIG is unchanged from before.
_ssl_ca = os.getenv("MYSQL_SSL_CA")
if _ssl_ca:
    DB_CONFIG["ssl_ca"] = _ssl_ca
    DB_CONFIG["ssl_verify_cert"] = True

_JSON_CAREER_FIELDS = (
    "riasec_tags", "relevant_subjects", "required_skills", "interest_tags",
    "courses", "colleges", "scholarships", "certifications",
)
_JSON_STUDENT_FIELDS = ("interests", "hobbies", "riasec_answers", "riasec_scores", "academics", "self_rated_skills")
_JSON_COLLEGE_FIELDS = ("known_for",)


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

        cur.execute("SELECT COUNT(*) AS n FROM colleges")
        if cur.fetchone()["n"] == 0:
            _seed_colleges(cur)

        _ensure_column(cur, "students", "email", "VARCHAR(255) UNIQUE AFTER name")
        _ensure_column(cur, "students", "password_hash", "VARCHAR(255) AFTER email")
        _ensure_column(cur, "students", "is_admin", "BOOLEAN NOT NULL DEFAULT FALSE AFTER password_hash")
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


def _seed_colleges(cur):
    colleges = json.loads(COLLEGES_SEED_PATH.read_text())
    for c in colleges:
        cur.execute(
            """
            INSERT INTO colleges (id, name, location, state, type, established, website, known_for)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                c["id"], c["name"], c["location"], c["state"], c["type"],
                c.get("established"), c.get("website"),
                json.dumps(c.get("known_for", [])),
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


def get_all_colleges() -> list[dict]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM colleges ORDER BY name ASC")
        rows = cur.fetchall()
    for row in rows:
        _parse_json_fields(row, _JSON_COLLEGE_FIELDS)
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
    """Returns {student_id, name, email, password_hash, is_admin} for login, or None."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT student_id, name, email, password_hash, is_admin FROM students WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
    if row:
        row["is_admin"] = bool(row["is_admin"])
    return row


def get_student_auth_by_id(student_id: str) -> dict | None:
    """Returns {student_id, name, email, password_hash, is_admin} for the
    authenticated caller — used by change-password and the admin dependency."""
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT student_id, name, email, password_hash, is_admin FROM students WHERE student_id = %s",
            (numeric_id,),
        )
        row = cur.fetchone()
    if row:
        row["is_admin"] = bool(row["is_admin"])
    return row


def sync_admin_flag(student_id: str, email: str) -> bool:
    """Promotes the account to admin if its email is listed in the
    ADMIN_EMAILS env var — the bootstrap mechanism for granting the first
    admin(s) without needing a manual SQL UPDATE. Called on every login/signup;
    idempotent, and never demotes an account (removing an email from the env
    var does not revoke access already granted). Returns the resulting is_admin."""
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return False

    admin_emails = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}
    with get_connection() as conn, conn.cursor() as cur:
        if email.lower() in admin_emails:
            cur.execute("UPDATE students SET is_admin = TRUE WHERE student_id = %s", (numeric_id,))
        cur.execute("SELECT is_admin FROM students WHERE student_id = %s", (numeric_id,))
        row = cur.fetchone()
    return bool(row["is_admin"]) if row else False


def update_password_hash(student_id: str, password_hash: str) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE students SET password_hash = %s WHERE student_id = %s",
            (password_hash, numeric_id),
        )


# ---- password reset ----

def create_password_reset(student_id: str, token_hash: str, expires_at) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO password_resets (student_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (numeric_id, token_hash, expires_at),
        )


def get_valid_password_reset(token_hash: str) -> dict | None:
    """Returns {reset_id, student_id} if token_hash is unused and unexpired, else None."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT reset_id, student_id FROM password_resets
            WHERE token_hash = %s AND used = FALSE AND expires_at > UTC_TIMESTAMP()
            """,
            (token_hash,),
        )
        return cur.fetchone()


def mark_password_reset_used(reset_id: int) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE password_resets SET used = TRUE WHERE reset_id = %s", (reset_id,))


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


# ---- admin: career management ----

def get_career_by_id(career_id: str) -> dict | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM careers WHERE id = %s", (career_id,))
        row = cur.fetchone()
    if not row:
        return None
    _parse_json_fields(row, _JSON_CAREER_FIELDS)
    row["emerging"] = bool(row["emerging"])
    return row


def create_career(career: dict) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO careers
                (id, name, description, riasec_tags, relevant_subjects, required_skills,
                 interest_tags, courses, colleges, scholarships, certifications, emerging)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                career["id"], career["name"], career["description"],
                json.dumps(career["riasec_tags"]),
                json.dumps(career.get("relevant_subjects", [])),
                json.dumps(career.get("required_skills", [])),
                json.dumps(career.get("interest_tags", [])),
                json.dumps(career.get("courses", [])),
                json.dumps(career.get("colleges", [])),
                json.dumps(career.get("scholarships", [])),
                json.dumps(career.get("certifications", [])),
                career.get("emerging", False),
            ),
        )


def update_career(career_id: str, career: dict) -> None:
    """id is taken from the URL path, not the payload — the row's id never changes."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE careers SET
                name = %s, description = %s, riasec_tags = %s, relevant_subjects = %s,
                required_skills = %s, interest_tags = %s, courses = %s, colleges = %s,
                scholarships = %s, certifications = %s, emerging = %s
            WHERE id = %s
            """,
            (
                career["name"], career["description"],
                json.dumps(career["riasec_tags"]),
                json.dumps(career.get("relevant_subjects", [])),
                json.dumps(career.get("required_skills", [])),
                json.dumps(career.get("interest_tags", [])),
                json.dumps(career.get("courses", [])),
                json.dumps(career.get("colleges", [])),
                json.dumps(career.get("scholarships", [])),
                json.dumps(career.get("certifications", [])),
                career.get("emerging", False),
                career_id,
            ),
        )


def delete_career(career_id: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM careers WHERE id = %s", (career_id,))


# ---- bookmarks ----

def add_bookmark(student_id: str, career_id: str) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT IGNORE INTO bookmarks (student_id, career_id) VALUES (%s, %s)",
            (numeric_id, career_id),
        )


def remove_bookmark(student_id: str, career_id: str) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM bookmarks WHERE student_id = %s AND career_id = %s",
            (numeric_id, career_id),
        )


def get_bookmarked_career_ids(student_id: str) -> list[str]:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT career_id FROM bookmarks WHERE student_id = %s", (numeric_id,))
        rows = cur.fetchall()
    return [row["career_id"] for row in rows]


def get_bookmarked_careers(student_id: str) -> list[dict]:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT c.* FROM careers c JOIN bookmarks b ON b.career_id = c.id "
            "WHERE b.student_id = %s ORDER BY b.created_at DESC",
            (numeric_id,),
        )
        rows = cur.fetchall()
    for row in rows:
        _parse_json_fields(row, _JSON_CAREER_FIELDS)
        row["emerging"] = bool(row["emerging"])
    return rows


# ---- career prep (resume bullets + interview questions, cached per student+career) ----

def save_career_prep(student_id: str, career_id: str, resume_bullets: list[str], interview_questions: list[str]) -> None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO career_prep (student_id, career_id, resume_bullets, interview_questions)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                resume_bullets = VALUES(resume_bullets),
                interview_questions = VALUES(interview_questions)
            """,
            (numeric_id, career_id, json.dumps(resume_bullets), json.dumps(interview_questions)),
        )


def get_career_prep(student_id: str, career_id: str) -> dict | None:
    numeric_id = _to_int(student_id)
    if numeric_id is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT resume_bullets, interview_questions FROM career_prep "
            "WHERE student_id = %s AND career_id = %s",
            (numeric_id, career_id),
        )
        row = cur.fetchone()
    if not row:
        return None
    if isinstance(row["resume_bullets"], str):
        row["resume_bullets"] = json.loads(row["resume_bullets"])
    if isinstance(row["interview_questions"], str):
        row["interview_questions"] = json.loads(row["interview_questions"])
    return row
