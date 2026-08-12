# Implementation Notes — As Built

This documents the system as it actually runs today, not the original plan
(see `02_ARCHITECTURE.md` for that, and how it diverged). Read this if
you're picking up the backend and want the real request flow, not the Day 1
scaffold description.

## Why MySQL instead of Supabase

The original plan called for Supabase Postgres with a fully normalized
schema (separate `courses`, `colleges`, `scholarships`, `certifications`
tables, each FK'd to `careers`). In practice:

- The team has a local MySQL instance and no Supabase project set up.
- The curated career dataset is small (~30 rows target) and doesn't change
  at runtime — the join overhead of 5 normalized tables buys nothing at
  this scale, and `docs/02b_DATA_MODEL.md` already called this out as an
  acceptable simplification ("Notes on scale").

So `careers` and `students` denormalize their list/dict fields into JSON
columns instead. `mentor_chat` and `roadmap_steps` stay normal FK-linked
tables since they grow per-interaction, not per-curated-item.

## Data model

4 tables, defined in `backend/database/schema.sql`, applied automatically
by `app/services/db.py:init_db()` on every startup (`CREATE TABLE IF NOT
EXISTS`, safe to re-run):

| Table | Purpose | Key columns |
|---|---|---|
| `students` | One row per student, created at signup | `email`, `password_hash` (bcrypt); `interests`, `hobbies`, `riasec_scores`, `academics`, `self_rated_skills` — all JSON, start empty |
| `careers` | One row per career, seeded from `careers_seed.json` | `riasec_tags`, `courses`, `colleges`, `scholarships`, `certifications` — all JSON; `emerging` boolean |
| `mentor_chat` | Full chat history | `student_id` FK, `sender` (`student`/`ai`), `message`, `created_at` |
| `roadmap_steps` | Roadmap progress tracking | `student_id` FK, `career`, `step_number`, `description`, `completed` |

Full column-level detail: `02b_DATA_MODEL.md`.

`app/services/db.py` is the *only* module that imports `pymysql`. Routers
and `scoring_engine.py` only ever call its plain-dict functions
(`create_account`, `get_student_auth_by_email`, `update_profile`,
`get_profile`, `get_all_careers`, `save_chat_message`, `get_chat_history`,
`save_roadmap`, `get_roadmap`, `update_roadmap_step`) — the storage layer
could change again without touching either.

## Auth

`app/services/auth.py` handles password hashing (bcrypt) and JWT
issuing/verification (PyJWT, HS256, secret from `JWT_SECRET`). Every
protected route depends on `get_current_student_id` — a FastAPI dependency
that reads the `Authorization: Bearer <token>` header, decodes it, and
returns the student_id from the token's `sub` claim (401 if missing,
malformed, or expired). No endpoint accepts `student_id` from the client —
identity comes entirely from the token, which is also why `/profile`,
`/score`, `/mentor/chat`, and `/roadmap` dropped `student_id` from their
request bodies/paths compared to earlier versions of this API.

## End-to-end request flow

```
0. Signup / Login          POST /auth/signup  { name, email, password }
                            POST /auth/login   { email, password }
   ─────────────────────────────────────────────────────────────
   Signup hashes the password (bcrypt) and creates a `students` row with
   empty profile fields ([] / {}). Login looks up by email and verifies
   the hash. Both return a JWT (access_token) the client attaches as
   `Authorization: Bearer <token>` on every subsequent request.

1. Intake                POST /profile
   ─────────────────────────────────────────────────────────────
   Client sends: interests, hobbies, raw riasec_answers, academics,
   self_rated_skills (name/email already set at signup, not resent here).
   Server computes riasec_scores from riasec_answers server-side
   (never trusts client-computed scores) via
   scoring_engine.compute_riasec_scores(), UPDATEs the students row
   identified by the token's student_id.

2. Deterministic ranking  POST /score
   ─────────────────────────────────────────────────────────────
   Loads the profile row (via token) + all of `careers`. scoring_engine.rank_careers()
   computes, per career:
     - riasec_match   = cosine similarity of RIASEC vectors, 0-100
     - academic_fit   = avg marks in the career's relevant_subjects
     - interest_overlap = tag overlap between student interests/hobbies
                          and the career's interest_tags
     - skill_score    = avg self-rated level across required_skills
   Blends them 40/30/20/10 (riasec/academic/interest/skill), returns
   top 5 sorted by score. No LLM call — fast, deterministic, unit-testable
   in isolation (scoring_engine.py has zero FastAPI/DB imports).

3. AI-generated insights   POST /score/insights  { top_matches }
   ─────────────────────────────────────────────────────────────
   Sends profile + top_matches to whichever LLM is configured
   (llm_client.py: Gemini / OpenAI / local Ollama) for a 2-sentence
   explanation per career, a step-by-step roadmap, and an emerging-trend
   blurb. If the LLM call fails or the key is missing, falls back to
   static generic text — this endpoint never 500s because of the LLM.
   The generated roadmap for top_matches[0] is persisted via
   db.save_roadmap(student_id, career, roadmap_steps) — this DELETEs any
   prior roadmap for that student+career pair and inserts the fresh one,
   so regenerating insights doesn't accumulate duplicate roadmaps.

4. Roadmap progress        GET /roadmap
                            PATCH /roadmap/steps/{step_id}
   ─────────────────────────────────────────────────────────────
   Independent of scoring — reads/writes `roadmap_steps` directly.
   Lets the student check off steps across visits without re-running
   the scoring or LLM pipeline.

5. Mentor chat              POST /mentor/chat  { message }
                             GET /mentor/chat
   ─────────────────────────────────────────────────────────────
   Saves the student's message to `mentor_chat` first, then fetches the
   full history and passes the last 6 turns back into the LLM prompt as
   conversational context, then saves the AI's reply. GET replays the
   full history in order. Same fallback safety net as step 3 — a flaky
   LLM call returns a canned reply instead of failing the request.
```

## Frontend

Streamlit (`frontend/app.py`), not the originally-planned React/Vite app —
Python-only end to end, faster to build for this project's scope. It's a
plain HTTP client of the backend (`frontend/api_client.py` wraps `requests`
calls, attaching the JWT from `st.session_state`); no direct DB or LLM
access from the frontend. Pages: auth (login/signup tabs), assessment
(intake form), dashboard (score + on-demand AI insights), roadmap
(checkboxes), mentor (chat). The RIASEC questions and subject/skill/interest
vocabulary in `app.py` are hardcoded to match `riasec_questions.py` and
`careers_seed.json` — if either changes on the backend, the frontend lists
need updating too (no shared source of truth between them currently).

## Local dev

```bash
# backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in MYSQL_* and JWT_SECRET — defaults assume localhost/root
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Requires a running local MySQL server. `init_db()` on startup:
1. `CREATE DATABASE IF NOT EXISTS` the configured database name.
2. Runs every `CREATE TABLE IF NOT EXISTS` in `schema.sql`.
3. If `careers` is empty, seeds it from `app/data/careers_seed.json`.
4. Migrates `students` to add `email`/`password_hash` if the table predates them.

No manual migration step, no seed script to remember to run.

## Known gaps / next steps

- `/score` and `/score/insights` results aren't cached — every dashboard
  load recomputes the ranking and, if called, re-hits the LLM. Fine at
  demo scale; would want a `career_recommendations`-style cache table if
  this became a real product with repeat visits.
- `roadmap` is keyed by career **name** (`careers.name`), not `careers.id`
  — if a career gets renamed in `careers_seed.json`, existing roadmap rows
  for it become orphaned from the new row. Not an issue at current scale
  (careers are added, not renamed), but worth fixing with a proper FK if
  the dataset starts churning.
- JWTs can't be revoked before they expire (`JWT_EXPIRE_MINUTES`, default
  24h) — there's no server-side session/blocklist, so "logout" only clears
  the token client-side. Acceptable for a demo; a real deployment would
  want short-lived access tokens + refresh tokens, or a revocation list.
- `careers.riasec_tags` are hand-assigned during data curation (see
  `03_SCORING_ALGORITHM.md`), not derived from labor-market data — a
  reasonable simplification for a curated ~30-career dataset, but worth
  flagging if asked where the "ideal profile" per career comes from.
