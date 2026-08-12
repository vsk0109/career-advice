# Backend — AI-Powered Career Mentor

FastAPI backend. See `../docs/` for architecture, data model, scoring algorithm, and API spec.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in MYSQL_* (defaults match a local root/no-password install), JWT_SECRET, and LLM_API_KEY when ready
```

Generate a `JWT_SECRET` with `python3 -c "import secrets; print(secrets.token_hex(32))"`.

Requires a running local MySQL server. On startup the app creates the
`career_mentor` database and tables if missing, and seeds `careers` from
`app/data/careers_seed.json` on first run — no manual migration step needed.

## Run

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

## Current state

- All endpoints from `docs/04_API_SPEC.md` are implemented and runnable
- Real auth: `POST /auth/signup`/`POST /auth/login` (bcrypt + JWT). Every other endpoint except `GET /careers` requires `Authorization: Bearer <token>` and derives the student's identity from it — no endpoint takes `student_id` from the client.
- Data layer (`app/services/db.py`) is **MySQL-backed** (see `database/schema.sql`). `students` and `careers` store their list/dict fields as JSON columns — denormalized per `docs/02b_DATA_MODEL.md`'s "Notes on scale", since the dataset is small and curated.
- LLM client (`app/services/llm_client.py`) returns safe fallback text until a real API key + provider call is wired in. This means the app is fully runnable and demoable even before the LLM integration is done.
- Career dataset (`app/data/careers_seed.json`) has 6 starter careers — expand to ~30. It's the source of truth; edit it and delete rows from the `careers` table (or drop the table) to re-seed.
- Streamlit frontend lives in `../frontend` — see `../frontend/SETUP.md`.

## Quick manual test

```bash
# 1. Sign up
TOKEN=$(curl -s -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Student", "email": "test.student@example.com", "password": "supersecret"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

# 2. Submit intake
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{
    "interests": ["technology", "problem-solving"],
    "hobbies": ["coding"],
    "riasec_answers": [2,2,5,5,2,1,2,3,3,2,3,3],
    "academics": {"Math": 90, "Physics": 85, "Computer Science": 88, "English": 60},
    "self_rated_skills": {"Python": 4, "Statistics": 2, "Coding": 5, "Communication": 3}
  }'

# 3. Get scored career matches
curl -X POST http://localhost:8000/score -H "Authorization: Bearer $TOKEN"
```

## Folder structure

```
app/
  main.py                    # FastAPI app + router registration + CORS + DB init on startup
  models/schemas.py           # Pydantic request/response models
  routers/                     # one file per resource: auth, profile, careers, score, mentor, roadmap
  services/
    auth.py                       # password hashing (bcrypt) + JWT issuing/verification
    scoring_engine.py            # pure-Python scoring logic (unit-testable, no framework deps)
    llm_client.py                  # LLM API wrapper with safe fallback
    db.py                            # data access layer (MySQL via PyMySQL)
  data/
    careers_seed.json               # curated career dataset (source of truth for the `careers` table)
    riasec_questions.py                # quiz question -> RIASEC dimension mapping
database/
  schema.sql                 # MySQL DDL, applied automatically on startup
```
