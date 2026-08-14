# Architecture — AI-Powered Career Mentor

> See [`05_IMPLEMENTATION.md`](05_IMPLEMENTATION.md) for the as-built system
> and end-to-end request flow. This doc is the original design; MySQL
> replaced the planned Supabase/Postgres backend, Streamlit replaced the
> planned React/Vite frontend, and real signup/login (JWT) was added during
> implementation.

## Overview

```
┌───────────────────────────┐   HTTP (JWT Bearer)   ┌──────────────────────────────┐
│  Streamlit Frontend         │◄─────────────────────►│  FastAPI Backend               │
│  (Streamlit Community Cloud)│                        │  (Render, free web service)     │
│                              │                        │                                   │
│  - Auth (login/signup/reset)│                        │  /auth  /profile  /careers        │
│  - Assessment (RIASEC+marks)│                        │  /score  /mentor  /roadmap        │
│  - Dashboard (matches)      │                        │  /admin  /bookmarks  /colleges    │
│  - Roadmap checklist        │                        │                                    │
│  - Mentor chat              │                        │  services/                        │
│  - Explore (compare/        │                        │   auth.py (bcrypt+JWT)            │
│    bookmarks/deadlines/dir) │                        │   scoring_engine.py (pure Python) │
│  - Colleges directory       │                        │   llm_client.py (Gemini/OpenAI/   │
│  - Scholarships catalog     │                        │                  Ollama, w/ fallback)│
│  - Admin CRUD (careers/     │                        │   db.py (PyMySQL, init_db on boot)│
│    colleges/courses/scholar)│                        └───────────┬──────────────┬────────┘
└───────────────────────────┘                                    │ SQL (TLS)    │ HTTPS
                                                                    ▼              ▼
                                                    ┌───────────────────────┐  ┌───────────────────┐
                                                    │  MySQL (Aiven managed)│  │  LLM API            │
                                                    │  9 tables — see       │  │  (Gemini/OpenAI/    │
                                                    │  02b_DATA_MODEL.md    │  │   Ollama)            │
                                                    └───────────────────────┘  └───────────────────┘

External: scripts/keep-alive.sh (or an external ping service) hits GET /health every ~10 min
to stop Render's free tier from sleeping the backend after 15 min idle.
```

## Components

### 1. Frontend (Streamlit — see `05_IMPLEMENTATION.md` for why this replaced the planned React app)
- **Pages:** Auth (login/signup/forgot-password) → Assessment (RIASEC + marks + skills intake) → Dashboard (ranked matches) → Roadmap (persisted checklist) → Mentor (chat) → Explore (compare careers / bookmarks / deadlines / college directory sub-tabs) → Colleges (standalone directory, filter/search) → Scholarships (catalog across all careers) → Admin (career/college/course/scholarship CRUD, admin-only)
- **State:** `st.session_state` holds the JWT and cached API responses (profile, score, insights, bookmarks, all_careers); JWT is also mirrored into the URL query string so a page refresh doesn't log the user out
- **Auth:** real signup/login against the backend (`POST /auth/signup`/`/auth/login`), JWT stored client-side for the session
- **Admin:** any account whose email is in the backend's `ADMIN_EMAILS` env var is promoted to `is_admin=true` on login/signup and gets the Admin page

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
      auth.py                # /auth/signup, /auth/login, /auth/me, /auth/change-password, /auth/forgot-password, /auth/reset-password
      profile.py            # /profile endpoints
      careers.py             # /careers endpoints
      score.py                 # /score, /score/insights endpoints
      mentor.py                 # /mentor/chat endpoints (chat + history)
      roadmap.py                 # /roadmap endpoints (list + mark step complete)
      admin.py                    # /admin/careers CRUD (create/update/delete), admin-only
      bookmarks.py                 # /bookmarks endpoints (star/unstar/list careers)
      colleges.py                   # /colleges endpoint (full directory)
    services:
      auth.py                # password hashing (bcrypt) + JWT issuing/verification
      scoring_engine.py       # pure-Python scoring logic (see 03_SCORING_ALGORITHM.md)
      llm_client.py             # wrapper around Gemini/OpenAI/Ollama calls
      db.py                      # MySQL data access layer (PyMySQL)
    data/
      careers_seed.json          # curated career dataset — source of truth, auto-seeded into MySQL
      colleges_seed.json         # Indian college/university directory — auto-seeded into MySQL
      riasec_questions.py        # the 12-question RIASEC personality inventory used by the Assessment page
  database/
    schema.sql                # MySQL DDL, applied automatically on startup
  requirements.txt
  .env.example
```
- **Why this split:** `services/scoring_engine.py` has zero dependency on FastAPI or the DB — it's pure functions taking a profile dict and a career list, returning scores. This makes it independently testable and is a good thing to point at during judging ("here's our matching algorithm, here are unit tests for it"). Likewise `db.py` is the only module that imports `pymysql` — routers and the scoring engine never see SQL, so storage can change again without touching either.

### 3. Database (MySQL)
9 tables, all created idempotently (`CREATE TABLE IF NOT EXISTS`) by `init_db()` on backend startup, with `ALTER TABLE` migration checks for columns added after initial launch:
- `students` — accounts + profile JSON (`interests`, `hobbies`, `riasec_answers`, `riasec_scores`, `academics`, `self_rated_skills`), plus `email`/`password_hash`/`is_admin`
- `careers` — ~30 curated careers, JSON columns for `riasec_tags`, `relevant_subjects`, `required_skills`, `interest_tags`, `courses`, `colleges`, `scholarships`, `certifications`
- `colleges` — 100+ Indian colleges/universities (name, location, state, type, established, website, `known_for` JSON)
- `mentor_chat` — chat history (`student_id`, `sender`, `message`)
- `roadmap_steps` — persisted roadmap checklist per student/career
- `insights` — cached LLM explanations + emerging trend per student
- `bookmarks` — starred careers per student (unique on student_id+career_id)
- `career_prep` — cached resume bullets + interview questions per student/career pair
- `password_resets` — forgot-password tokens (SHA256 hash, 30-min expiry, single use)

`students`/`careers`/`colleges` denormalize their list/dict fields into JSON columns rather than separate join tables (small curated dataset, not worth the join overhead). See `02b_DATA_MODEL.md` for full schema, `05_IMPLEMENTATION.md` for why this differs from the original Supabase plan

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
| GET | `/auth/me` | Fetch the authenticated caller's account info |
| POST | `/auth/change-password` | Change password while authenticated |
| POST | `/auth/forgot-password` | Issue a password-reset token (shown in UI, not emailed) |
| POST | `/auth/reset-password` | Consume a reset token, set a new password |
| POST | `/profile` | Save the authenticated student's intake data |
| GET | `/profile` | Fetch the authenticated student's saved profile |
| GET | `/careers` | List all careers (for browsing/debug); no auth |
| GET | `/colleges` | List the full college/university directory; no auth |
| POST | `/score` | Ranked career matches for the authenticated student (deterministic, no LLM) |
| POST | `/score/insights` | LLM explanations + roadmap for the top matches; persists the roadmap |
| GET | `/score/insights` | Fetch cached LLM explanations/roadmap without recomputing |
| POST | `/mentor/chat` | Send a chat message, get an LLM-generated reply with profile + history context |
| GET | `/mentor/chat` | Full chat history |
| GET | `/roadmap` | Roadmap steps + completion status |
| PATCH | `/roadmap/steps/{step_id}` | Mark a step complete/incomplete |
| GET | `/bookmarks` | List the authenticated student's bookmarked careers |
| POST | `/bookmarks/{career_id}` | Bookmark a career |
| DELETE | `/bookmarks/{career_id}` | Remove a bookmark |
| GET | `/admin/careers` | List all careers with full editable JSON (admin-only) |
| POST | `/admin/careers` | Create a career (admin-only) |
| PUT | `/admin/careers/{id}` | Update a career (admin-only) |
| DELETE | `/admin/careers/{id}` | Delete a career (admin-only) |

Every endpoint except `GET /careers`, `GET /colleges`, and the `/auth/*` entry points requires `Authorization: Bearer <token>`; admin endpoints additionally check `is_admin` on the resolved student.

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

**5. Keeping the free tier awake**
- Render's free web services sleep after 15 minutes idle; `scripts/keep-alive.sh` curls both the
  backend `GET /health` and the frontend URL every ~10 minutes to prevent that. Run it as a cron job
  (`*/10 * * * * /path/to/scripts/keep-alive.sh`) or point an external uptime-ping service (e.g.
  UptimeRobot, cron-job.org) at the same two URLs instead of running it yourself — a GitHub Actions
  cron was tried first and dropped in favor of this because Actions schedules aren't reliably timed
  on the free tier.

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

