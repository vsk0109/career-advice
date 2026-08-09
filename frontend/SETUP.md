# Frontend Setup

This folder is a placeholder — the actual React app needs to be scaffolded locally with `npm` (needs to run on your machine, not something that can be pre-built as static files).

## First-time setup (whoever owns frontend — D Vaishnavi)

From the `career-advice/` repo root:

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios recharts react-router-dom
```

When prompted "Current directory is not empty, remove existing files and continue?", say yes (it'll only remove this placeholder setup — just make sure `.env.example` is re-added after, or copy it back in from git history).

Copy `.env.example` to `.env` and set:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Run dev server

```bash
npm run dev
```

Runs on `http://localhost:5173` by default — this matches the CORS origin already whitelisted in `backend/app/main.py`.

## Suggested page structure

```
src/
  main.jsx
  App.jsx
  api/
    client.js          # axios instance using VITE_API_BASE_URL
  pages/
    Landing.jsx
    Intake.jsx           # multi-step form: interests, RIASEC quiz, academics, hobbies, skills
    Dashboard.jsx
    Mentor.jsx             # chat UI
  components/
    RiasecRadarChart.jsx
    CareerCard.jsx
    SkillGapChecklist.jsx
    ProgressTracker.jsx
```

## API calls this needs to make

See `../docs/04_API_SPEC.md` for full request/response shapes. Summary:

1. `POST /profile` — submit intake form → get back `student_id` + computed RIASEC scores
2. `POST /score` — get ranked career matches for `student_id`
3. `POST /score/insights` — get LLM explanations + roadmap for the top matches
4. `POST /mentor/chat` — send chat messages

Store `student_id` in React state (or localStorage) after intake so it can be reused across the Dashboard and Mentor pages.
