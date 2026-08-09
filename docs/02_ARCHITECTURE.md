# Architecture — AI-Powered Career Mentor

## Overview

```
┌─────────────────────┐        ┌──────────────────────────┐        ┌───────────────────┐
│   React Frontend     │  HTTP  │   FastAPI Backend         │        │   Supabase          │
│   (Vercel)            │◄──────►│   (Render/Railway)         │◄──────►│   Postgres + Auth    │
│                        │        │                            │        │                     │
│  - Intake forms        │        │  - /profile                │        └───────────────────┘
│  - Dashboard             │        │  - /score                    │
│  - Chat mentor UI          │        │  - /careers                    │        ┌───────────────────┐
└─────────────────────┘        │  - /mentor/chat                  │◄──────►│  LLM API            │
                                  │  - Scoring engine (pure Python)    │        │  (Gemini/OpenAI)      │
                                  └──────────────────────────┘        └───────────────────┘
```

## Components

### 1. Frontend (React, deployed on Vercel)
- **Pages:** Landing → Profile Intake (multi-step form) → Dashboard → Mentor Chat
- **State:** React Context or simple prop-drilling is fine at this scale — don't over-engineer with Redux
- **Charting:** Recharts for the RIASEC radar chart and suitability bar chart
- **Auth:** Supabase Auth client SDK (email/password or magic link) — or skip real auth and use a local session ID if time-constrained

### 2. Backend (FastAPI, deployed on Render or Railway)
- **Framework:** FastAPI + Pydantic for request/response validation (this is why FastAPI is a good pick — you get free input validation and auto-generated OpenAPI docs at `/docs`, which is genuinely useful to show judges)
- **Structure:**
```
backend/
  app/
    main.py                # FastAPI app, router registration
    models/
      schemas.py           # Pydantic request/response models
    routers/
      profile.py            # /profile endpoints
      careers.py             # /careers endpoints
      score.py                 # /score endpoint
      mentor.py                 # /mentor/chat endpoint
    services/
      scoring_engine.py       # pure-Python scoring logic (see 03_SCORING_ALGORITHM.md)
      llm_client.py             # wrapper around Gemini/OpenAI calls
      db.py                      # Supabase/Postgres client
    data/
      careers_seed.json          # curated career dataset (or loaded from DB)
  requirements.txt
  .env.example
```
- **Why this split:** `services/scoring_engine.py` has zero dependency on FastAPI or the DB — it's pure functions taking a profile dict and a career list, returning scores. This makes it independently testable and is a good thing to point at during judging ("here's our matching algorithm, here are unit tests for it").

### 3. Database (Supabase Postgres)
- Tables: `students`, `student_profiles`, `careers`, `courses`, `colleges`, `scholarships`, `certifications`, `career_matches` (optional — can also compute scores on the fly instead of storing them)
- See `02b_DATA_MODEL.md` for schema

### 4. AI Layer
Two distinct things, don't conflate them:
- **Scoring engine** = deterministic, explainable, your own weighted algorithm (RIASEC + academics + interests). This is the "data-driven" part.
- **LLM calls** = generative text layered on top of the scoring output — explanations, roadmaps, chat. Called via a single `llm_client.py` wrapper so you can swap providers or add caching/fallback in one place.

**Fallback strategy (important for demo safety):** if the LLM API call fails or times out, `llm_client.py` should catch the error and return a pre-written generic template response rather than crashing the request. Never let a flaky external API take down your live demo.

## API Contract (summary — full detail in 03)

| Method | Path | Purpose |
|---|---|---|
| POST | `/profile` | Save a student's intake data |
| GET | `/profile/{student_id}` | Fetch saved profile |
| GET | `/careers` | List all careers (for browsing/debug) |
| POST | `/score` | Given a profile, return ranked career matches |
| POST | `/mentor/chat` | Send a chat message, get an LLM-generated reply with profile context |

## Deployment

- **Frontend:** push to GitHub → connect repo to Vercel → auto-deploys on push to `main`
- **Backend:** push to GitHub → connect repo to Render/Railway → set env vars (`SUPABASE_URL`, `SUPABASE_KEY`, `LLM_API_KEY`) → auto-deploys on push
- **CORS:** FastAPI `CORSMiddleware` must allow the Vercel frontend origin
- Do a throwaway deploy on Day 2 to catch config issues early — don't wait until Day 6

## Environment Variables

```
# backend/.env
SUPABASE_URL=
SUPABASE_KEY=
LLM_API_KEY=
LLM_PROVIDER=gemini   # or openai
```
Never commit `.env` — commit `.env.example` with empty values instead.
