# Frontend Setup

Streamlit app that talks to the FastAPI backend over HTTP (with a JWT from
login/signup attached as a Bearer token). Python-only — no npm/Vite step.

## Setup

```bash
cd frontend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # set API_BASE_URL if the backend isn't on localhost:8000
```

## Run

```bash
streamlit run app.py
```

Runs on `http://localhost:8501` by default. Requires the backend
(`cd ../backend && uvicorn app.main:app --reload`) running and its MySQL
database up — see `../backend/README.md`.

## Pages

```
app.py           # everything: styles, auth, assessment, dashboard, roadmap, mentor chat
api_client.py     # thin requests wrapper around the backend, attaches the JWT from st.session_state
```

- **Log in / Sign up** — calls `POST /auth/login` or `POST /auth/signup`, stores the returned JWT in `st.session_state`.
- **Assessment** — RIASEC quiz (12 sliders), academics, self-rated skills, interests/hobbies → `POST /profile`. Shown automatically until the student has a saved RIASEC profile.
- **Dashboard** — `POST /score` for ranked matches, `POST /score/insights` (on demand, since it calls the LLM) for explanations + roadmap.
- **Roadmap** — `GET /roadmap` + `PATCH /roadmap/steps/{step_id}` checkboxes.
- **Mentor** — `GET`/`POST /mentor/chat`, rendered with `st.chat_message`.

The RIASEC questions and the subject/skill/interest vocabulary in `app.py`
must match `backend/app/data/riasec_questions.py` and `careers_seed.json` —
that's what the scoring engine actually matches against. If either changes
on the backend, update the corresponding lists in `app.py`.
