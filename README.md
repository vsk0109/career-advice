# AI-Powered Career Mentor

A personalized career guidance platform for students — built for [IDP at College] by Vaishnavi Sudarsan K, D Vaishnavi, Anushka, and Shalvi.

## What it does

Collects a student's interests, personality (RIASEC), academics, hobbies, and self-rated skills, then recommends the best-fit career paths, relevant courses/colleges, scholarships, and a personalized skill-development roadmap — combining a transparent scoring algorithm with LLM-generated explanations and a chat-based mentor.

## Repo structure

```
career-advice/
├── backend/     FastAPI backend — see backend/README.md
├── frontend/    React frontend — see frontend/SETUP.md
└── docs/        Design docs: architecture, data model, scoring algorithm, API spec, project plan
```

## Quick start

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Runs at http://localhost:8000 (docs at `/docs`).

**Frontend:** see `frontend/SETUP.md` for the one-time Vite scaffold step, then:
```bash
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173.

## Docs

- [`docs/01_PROJECT_PLAN.md`](docs/01_PROJECT_PLAN.md) — scope, team roles, day-by-day plan
- [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) — system architecture, deployment
- [`docs/02b_DATA_MODEL.md`](docs/02b_DATA_MODEL.md) — database schema
- [`docs/03_SCORING_ALGORITHM.md`](docs/03_SCORING_ALGORITHM.md) — how career matching works
- [`docs/04_API_SPEC.md`](docs/04_API_SPEC.md) — API endpoints
