# AI-Powered Career Mentor — 1-Week Project Plan

**Team:** Vaishnavi Sudarsan K, D Vaishnavi, Anushka, Shalvi
**Stack:** Python (FastAPI) backend · React frontend · Supabase (Postgres) · Gemini/OpenAI API for AI text
**Goal:** A deployed, demoable MVP for expo — not the full spec, the *convincing slice* of it.

---

## Locked MVP Scope (do not expand this list mid-week)

In:
- Student signup/login (or even just a session with a name — skip real auth if time is short)
- Profile intake: interests, RIASEC-style personality quiz, academic marks by subject, hobbies, self-rated skills
- Scoring engine → top 5 career matches with % suitability
- Curated static dataset: ~30 careers × RIASEC tags, required subjects, skills, sample courses/colleges/certifications, 1-2 scholarships each
- Dashboard: profile summary, career suitability radar/bar chart, top career cards, course/college list, scholarships, skill-gap checklist, roadmap, progress tracker
- LLM-generated: "why this career fits you" text, personalized 3-step learning roadmap, and a simple chat mentor box
- Deployed live (Vercel + Render/Railway) with a public URL

Out (say this explicitly at the expo so judges know it's intentional, not a gap you missed):
- Report card OCR / file upload parsing
- Live scraping of real-time scholarship/job data
- Trained ML model (the scoring engine is a transparent weighted algorithm + LLM reasoning layer — call this "AI-assisted," it's honest and still impressive)
- Multi-language support, mobile app (web-responsive is enough)

---

## Team Roles

| Person | Owns |
|---|---|
| Vaishnavi Sudarsan K | FastAPI backend, scoring engine, LLM integration, API design |
| Shalvi | React frontend — dashboard UI, charts, layout |
| D Vaishnavi | Database schema (Supabase), career/course/scholarship dataset curation, seeding |
| Anushka | Profile intake forms + quiz UI, deployment, demo script/poster |

Everyone touches the integration on Day 5 — that's non-negotiable, budget for it.

---

## Day-by-Day

### Day 1 (Today) — Design & Setup
- Finalize this scope doc, data model, API contract (this session)
- Create GitHub repo, branch strategy (`main` + feature branches), agree on commit convention
- Set up Supabase project + FastAPI project skeleton + React project skeleton
- Anushka starts pulling career data into a spreadsheet (career name, RIASEC tags, subjects, skills, courses, colleges, scholarships, certifications) — this is the long pole, start immediately
- Everyone: get local dev environment running, push a "hello world" from each service

### Day 2 — Backend Core + Frontend Skeleton
- Vaishnavi S: FastAPI project structure, Pydantic models, DB connection, `/profile` and `/careers` endpoints (stub data)
- D Vaishnavi: React routing, page shells (Landing → Intake → Dashboard), component structure, connect to Supabase auth
- Anushka: finalize dataset schema, load first 15 careers into Supabase
- Shalvi: build intake form UI (interests, quiz, marks, hobbies) with local state, no backend yet

### Day 3 — Scoring Engine + Data Complete
- Vaishnavi S: implement scoring algorithm end-to-end (see `03_SCORING_ALGORITHM.md`), `/score` endpoint returns ranked careers
- Anushka: finish all ~30 careers in DB, write seed script
- Shalvi: wire intake form to POST `/profile`, handle validation
- D Vaishnavi: build dashboard skeleton (cards, chart placeholders) with mock data

### Day 4 — AI Layer + Dashboard Wiring
- Vaishnavi S: integrate LLM API — generate "why this fits," roadmap text, chat mentor endpoint (`/mentor/chat`)
- D Vaishnavi: connect dashboard to real `/score` + `/careers` data, build radar chart (RIASEC) and career cards
- Shalvi: skill-gap checklist UI + progress tracker (local logic: skills user has vs. skills career needs)
- Anushka: add scholarships + certifications data, help test API responses against real data

### Day 5 — Full Integration
- Whole team: connect every screen to real backend, fix broken contracts, handle loading/error states
- Chat mentor UI wired to backend
- Cut anything not working reliably — better a smaller polished demo than a broken big one

### Day 6 — Deploy + Test + Polish
- Deploy backend (Render/Railway) and frontend (Vercel)
- Fix CORS, env vars, production config
- Full run-through as a real student would use it, fix UX rough edges
- Add loading skeletons, basic responsive styling pass

### Day 7 — Demo Prep
- Write and rehearse a 3-4 minute demo script (see `04_DEMO_SCRIPT.md` — build this later in the week)
- Prepare poster/slides: problem, solution, architecture diagram, tech stack, screenshots
- Backup plan: record a screen-capture demo video in case live wifi/hosting fails at the expo
- Final rehearsal as a team, assign who talks about what

---

## Risk Notes
- **Dataset curation is the real bottleneck**, not code. Start Day 1, not Day 3.
- **LLM API keys**: get free-tier keys for Gemini or OpenAI on Day 1 so nobody is blocked later.
- **Have a fallback for the LLM calls** — if the API is slow/down during the demo, cache a few pre-generated responses to show instead of a spinner.
- **Deploy early, not on Day 6 only** — do a throwaway deploy on Day 2 just to confirm the pipeline works, so Day 6 isn't the first time you hit a hosting surprise.
