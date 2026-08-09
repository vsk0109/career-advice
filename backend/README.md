# Backend — AI-Powered Career Mentor

FastAPI backend. See `../docs/` for architecture, data model, scoring algorithm, and API spec.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in SUPABASE_URL/KEY and LLM_API_KEY when ready
```

## Run

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

## Current state (Day 1 scaffold)

- All endpoints from `docs/04_API_SPEC.md` are implemented and runnable
- Data layer (`app/services/db.py`) is **in-memory** for now — profiles reset on server restart. Swap for real Supabase calls once the DB schema is set up (Anushka) — the function signatures (`save_profile`, `get_profile`, `get_all_careers`) are the contract, so routers won't need to change.
- LLM client (`app/services/llm_client.py`) returns safe fallback text until a real API key + provider call is wired in (Vaishnavi S, Day 4). This means the app is fully runnable and demoable even before the LLM integration is done.
- Career dataset (`app/data/careers_seed.json`) has 6 starter careers — expand to ~30 (Anushka, Day 2-3).

## Quick manual test

```bash
# 1. Create a profile
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "interests": ["technology", "problem-solving"],
    "hobbies": ["coding"],
    "riasec_answers": [2,2,5,5,2,1,2,3,3,2,3,3],
    "academics": {"Math": 90, "Physics": 85, "Computer Science": 88, "English": 60},
    "self_rated_skills": {"Python": 4, "Statistics": 2, "Coding": 5, "Communication": 3}
  }'
# Copy the "student_id" from the response

# 2. Get scored career matches
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"student_id": "PASTE_STUDENT_ID_HERE"}'
```

## Folder structure

```
app/
  main.py                    # FastAPI app + router registration + CORS
  models/schemas.py           # Pydantic request/response models
  routers/                     # one file per resource: profile, careers, score, mentor
  services/
    scoring_engine.py            # pure-Python scoring logic (unit-testable, no framework deps)
    llm_client.py                  # LLM API wrapper with safe fallback
    db.py                            # data access layer (in-memory now, Supabase later)
  data/
    careers_seed.json               # curated career dataset
    riasec_questions.py                # quiz question -> RIASEC dimension mapping
```
