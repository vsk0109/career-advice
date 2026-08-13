# Architecture — AI-Powered Career Mentor

> See [`05_IMPLEMENTATION.md`](05_IMPLEMENTATION.md) for the as-built system
> and end-to-end request flow. This doc is the original design; MySQL
> replaced the planned Supabase/Postgres backend, Streamlit replaced the
> planned React/Vite frontend, and real signup/login (JWT) was added during
> implementation.

## Overview

```
┌─────────────────────┐        ┌──────────────────────────┐        ┌───────────────────┐
│   Streamlit Frontend  │  HTTP  │   FastAPI Backend         │        │   MySQL              │
│   (local / hosted)     │◄──────►│   (Render/Railway)         │◄──────►│   (local / hosted)    │
│                        │        │                            │        │                     │
│  - Login/Signup         │        │  - /auth/signup, /login       │        └───────────────────┘
│  - Assessment form         │        │  - /profile                     │
│  - Dashboard                 │        │  - /score                          │        ┌───────────────────┐
│  - Roadmap                      │        │  - /careers                          │◄──────►│  LLM API            │
│  - Chat mentor UI                  │        │  - /mentor/chat                        │        │  (Gemini/OpenAI/Ollama) │
└─────────────────────┘        │  - /roadmap                                │        └───────────────────┘
                                  │  - Scoring engine (pure Python)              │
                                  └──────────────────────────┘
```

## Components

### 1. Frontend (Streamlit — see `05_IMPLEMENTATION.md` for why this replaced the planned React app)
- **Pages:** Login/Signup → Assessment (intake form) → Dashboard → Roadmap → Mentor Chat
- **State:** `st.session_state` holds the JWT and cached API responses (score, insights)
- **Auth:** real signup/login against the backend (`POST /auth/signup`/`/auth/login`), JWT stored client-side for the session

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
      auth.py                # /auth/signup, /auth/login
      profile.py            # /profile endpoints
      careers.py             # /careers endpoints
      score.py                 # /score, /score/insights endpoints
      mentor.py                 # /mentor/chat endpoints (chat + history)
      roadmap.py                 # /roadmap endpoints (list + mark step complete)
    services/
      auth.py                # password hashing (bcrypt) + JWT issuing/verification
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
- Tables: `students` (email/password_hash + profile JSON), `careers`, `mentor_chat`, `roadmap_steps` — `students`/`careers` denormalize their list/dict fields into JSON columns rather than separate join tables (small curated dataset, not worth the join overhead)
- See `02b_DATA_MODEL.md` for schema, `05_IMPLEMENTATION.md` for why this differs from the original Supabase plan

### 4. Auth
Real signup/login, not a placeholder: `POST /auth/signup` hashes the
password (bcrypt) and creates the student row; `POST /auth/login` verifies
it and both return a JWT. Every other endpoint (except `GET /careers`)
requires `Authorization: Bearer <token>` and derives the student's identity
from it — no endpoint accepts `student_id` from the client. See
`05_IMPLEMENTATION.md` for the dependency that enforces this
(`get_current_student_id`).

### 5. AI Layer
Two distinct things, don't conflate them:
- **Scoring engine** = deterministic, explainable, your own weighted algorithm (RIASEC + academics + interests). This is the "data-driven" part.
- **LLM calls** = generative text layered on top of the scoring output — explanations, roadmaps, chat. Called via a single `llm_client.py` wrapper so you can swap providers or add caching/fallback in one place.

**Fallback strategy (important for demo safety):** if the LLM API call fails or times out, `llm_client.py` catches the error and returns a pre-written generic template response rather than crashing the request. Never let a flaky external API take down your live demo. The mentor chat also passes the last 6 turns of `mentor_chat` history back into the prompt for conversational continuity.

## API Contract (summary — full detail in `04_API_SPEC.md`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create an account (name, email, password) → JWT |
| POST | `/auth/login` | Authenticate → JWT |
| POST | `/profile` | Save the authenticated student's intake data |
| GET | `/profile` | Fetch the authenticated student's saved profile |
| GET | `/careers` | List all careers (for browsing/debug); no auth |
| POST | `/score` | Ranked career matches for the authenticated student (deterministic, no LLM) |
| POST | `/score/insights` | LLM explanations + roadmap for the top matches; persists the roadmap |
| POST | `/mentor/chat` | Send a chat message, get an LLM-generated reply with profile + history context |
| GET | `/mentor/chat` | Full chat history |
| GET | `/roadmap` | Roadmap steps + completion status |
| PATCH | `/roadmap/steps/{step_id}` | Mark a step complete/incomplete |

## Deployment

Chosen stack: **Streamlit Community Cloud** (frontend) + **Render** free web service (backend) +
**Aiven** free MySQL (database). All free, no usage-credit expiry to worry about, at the cost of
a ~30-50s cold start on the backend after 15 minutes idle.

**1. Database (Aiven MySQL, do this first — the backend needs its connection details)**
- Create a free Aiven account → new MySQL service (any region) → wait for it to go "Running"
- From the service overview page, copy: host, port, user, password, database name
- Download the CA certificate Aiven provides — managed MySQL requires TLS, unlike local MySQL
- `init_db()` creates the schema and seeds careers/colleges on first boot — no manual migration

**2. Backend (Render)**
- Push this repo to GitHub, then in Render: New → Blueprint → point at the repo (uses `render.yaml`
  at the repo root, which sets the build/start commands and declares which env vars it needs)
- Fill in the env vars Render prompts for (marked `sync: false` in `render.yaml`, so they're not
  stored in the blueprint itself): `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`,
  `MYSQL_DATABASE` (all from Aiven), `MYSQL_SSL_CA` (paste the downloaded CA cert's contents, or
  upload it as a Render "Secret File" and point this at its mounted path), `ADMIN_EMAILS`,
  `LLM_API_KEY` (a free Gemini key from https://aistudio.google.com/apikey)
- `JWT_SECRET` is auto-generated by the blueprint (`generateValue: true`) — don't reuse a local dev value
- `LLM_PROVIDER=gemini` for production — Ollama needs a persistent server with the model resident
  in memory, which free hosting tiers don't give you. (If Gemini failed locally behind a corporate
  proxy like Zscaler, that's a local network restriction — it won't affect a cloud-hosted backend.)
- Render gives you a public URL like `https://career-mentor-api.onrender.com` — note it for the next step

**3. Frontend (Streamlit Community Cloud)**
- New app → point at this repo → main file path: `frontend/app.py`
- In the app's Settings → Secrets, add: `API_BASE_URL = "https://career-mentor-api.onrender.com"`
  (the Render URL from step 2). `api_client.py` checks `st.secrets` for this since Streamlit Cloud
  doesn't inject secrets.toml values into `os.environ` the way a local `.env` file does.
- Streamlit talks to the backend server-to-server (Python `requests`, not browser JS), so CORS
  doesn't apply to it the way it would for a React frontend — no origin config needed on the backend

**4. After first deploy**
- Sign up through the deployed frontend once with whichever email you put in `ADMIN_EMAILS`, to get
  the admin dashboard
- The first request after any idle period will be slow (Render free tier cold start) — expected,
  not a bug

## Environment Variables

```
# backend/.env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=career_mentor
MYSQL_SSL_CA=            # only needed for managed MySQL (Aiven, PlanetScale, RDS, ...)
JWT_SECRET=
JWT_EXPIRE_MINUTES=1440
ADMIN_EMAILS=            # comma-separated; auto-promoted to admin on next login/signup
LLM_API_KEY=
LLM_PROVIDER=gemini      # or openai, or ollama
GEMINI_MODEL=gemini-1.5-flash   # optional, only used when LLM_PROVIDER=gemini

# frontend/.env (local) or Streamlit Cloud → Settings → Secrets (deployed)
API_BASE_URL=http://localhost:8000
```
Never commit `.env` — commit `.env.example` with empty values instead.

