# Architecture — AI-Powered Career Mentor

> See [`05_IMPLEMENTATION.md`](05_IMPLEMENTATION.md) for the as-built system
> and end-to-end request flow. This doc is the original design; MySQL
> replaced the planned Supabase/Postgres backend during implementation.

## Overview

```
┌─────────────────────┐        ┌──────────────────────────┐        ┌───────────────────┐
│   React Frontend     │  HTTP  │   FastAPI Backend         │        │   MySQL              │
│   (Vercel)            │◄──────►│   (Render/Railway)         │◄──────►│   (local / hosted)    │
│                        │        │                            │        │                     │
│  - Intake forms        │        │  - /profile                │        └───────────────────┘
│  - Dashboard             │        │  - /score                    │
│  - Chat mentor UI          │        │  - /careers                    │        ┌───────────────────┐
└─────────────────────┘        │  - /mentor/chat                  │◄──────►│  LLM API            │
                                  │  - /roadmap                        │        │  (Gemini/OpenAI/Ollama) │
                                  │  - Scoring engine (pure Python)    │        └───────────────────┘
                                  └──────────────────────────┘
```

## Components

### 1. Frontend (React, deployed on Vercel)
- **Pages:** Landing → Profile Intake (multi-step form) → Dashboard → Mentor Chat
- **State:** React Context or simple prop-drilling is fine at this scale — don't over-engineer with Redux
- **Charting:** Recharts for the RIASEC radar chart and suitability bar chart
- **Auth:** not implemented — `student_id` returned from `/profile` is the only session concept; add real auth later if this goes beyond a demo

### 2. Backend (FastAPI, deployed on Render or Railway)
- **Framework:** FastAPI + Pydantic for request/response validation (this is why FastAPI is a good pick — you get free input validation and auto-generated OpenAPI docs at `/docs`, which is genuinely useful to show judges)
- **Structure:**
```
backend/
  app/
    main.py                # FastAPI app, router registration, DB init on startup
    models/
      schemas.py           # Pydantic request/response models
    routers/
      profile.py            # /profile endpoints
      careers.py             # /careers endpoints
      score.py                 # /score, /score/insights endpoints
      mentor.py                 # /mentor/chat endpoints (chat + history)
      roadmap.py                 # /roadmap endpoints (list + mark step complete)
    services/
      scoring_engine.py       # pure-Python scoring logic (see 03_SCORING_ALGORITHM.md)
      llm_client.py             # wrapper around Gemini/OpenAI/Ollama calls
      db.py                      # MySQL data access layer (PyMySQL)
    data/
      careers_seed.json          # curated career dataset — source of truth, auto-seeded into MySQL
  database/
    schema.sql                # MySQL DDL, applied automatically on startup
  requirements.txt
  .env.example
```
- **Why this split:** `services/scoring_engine.py` has zero dependency on FastAPI or the DB — it's pure functions taking a profile dict and a career list, returning scores. This makes it independently testable and is a good thing to point at during judging ("here's our matching algorithm, here are unit tests for it"). Likewise `db.py` is the only module that imports `pymysql` — routers and the scoring engine never see SQL, so storage can change again without touching either.

### 3. Database (MySQL)
- Tables: `students`, `careers`, `mentor_chat`, `roadmap_steps` — `students`/`careers` denormalize their list/dict fields into JSON columns rather than separate join tables (small curated dataset, not worth the join overhead)
- See `02b_DATA_MODEL.md` for schema, `05_IMPLEMENTATION.md` for why this differs from the original Supabase plan

### 4. AI Layer
Two distinct things, don't conflate them:
- **Scoring engine** = deterministic, explainable, your own weighted algorithm (RIASEC + academics + interests). This is the "data-driven" part.
- **LLM calls** = generative text layered on top of the scoring output — explanations, roadmaps, chat. Called via a single `llm_client.py` wrapper so you can swap providers or add caching/fallback in one place.

**Fallback strategy (important for demo safety):** if the LLM API call fails or times out, `llm_client.py` catches the error and returns a pre-written generic template response rather than crashing the request. Never let a flaky external API take down your live demo. The mentor chat also passes the last 6 turns of `mentor_chat` history back into the prompt for conversational continuity.

## API Contract (summary — full detail in `04_API_SPEC.md`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/profile` | Save a student's intake data |
| GET | `/profile/{student_id}` | Fetch saved profile |
| GET | `/careers` | List all careers (for browsing/debug) |
| POST | `/score` | Given a profile, return ranked career matches (deterministic, no LLM) |
| POST | `/score/insights` | LLM explanations + roadmap for the top matches; persists the roadmap |
| POST | `/mentor/chat` | Send a chat message, get an LLM-generated reply with profile + history context |
| GET | `/mentor/chat/{student_id}` | Full chat history |
| GET | `/roadmap/{student_id}` | Roadmap steps + completion status |
| PATCH | `/roadmap/{student_id}/steps/{step_id}` | Mark a step complete/incomplete |

## Deployment

- **Frontend:** push to GitHub → connect repo to Vercel → auto-deploys on push to `main`
- **Backend:** push to GitHub → connect repo to Render/Railway → set env vars (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `LLM_API_KEY`) → auto-deploys on push. Point `MYSQL_HOST`/etc at a hosted MySQL instance (PlanetScale, RDS, Railway's own MySQL addon, ...) — `init_db()` creates the schema and seeds careers on first boot, no manual migration step.
- **CORS:** FastAPI `CORSMiddleware` must allow the Vercel frontend origin
- Do a throwaway deploy on Day 2 to catch config issues early — don't wait until Day 6

## Environment Variables

```
# backend/.env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=career_mentor
LLM_API_KEY=
LLM_PROVIDER=gemini   # or openai, or ollama
```
Never commit `.env` — commit `.env.example` with empty values instead.

