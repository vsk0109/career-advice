"""
Data access layer.

For Day 1-2 this is an in-memory store so the team isn't blocked on Supabase
setup before writing/testing API logic. Swap the internals for real Supabase
calls once the DB is ready — the function signatures below are the contract
the routers depend on, so routers shouldn't need to change when you swap this.

TODO (Anushka): replace with real Supabase client calls once schema is live.
See docs/02b_DATA_MODEL.md for the target schema.
"""

import json
import uuid
from pathlib import Path

CAREERS_SEED_PATH = Path(__file__).parent.parent / "data" / "careers_seed.json"

# ---- in-memory "tables" ----
_profiles: dict[str, dict] = {}
_careers: list[dict] = []


def _load_careers():
    global _careers
    if not _careers:
        with open(CAREERS_SEED_PATH) as f:
            _careers = json.load(f)
    return _careers


def get_all_careers() -> list[dict]:
    return _load_careers()


def save_profile(profile_data: dict) -> str:
    student_id = str(uuid.uuid4())
    _profiles[student_id] = profile_data
    return student_id


def get_profile(student_id: str) -> dict | None:
    return _profiles.get(student_id)
