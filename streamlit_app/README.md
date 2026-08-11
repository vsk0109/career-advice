# Career Compass AI — Streamlit App

## Setup

```bash
cd streamlit_app
python3 -m venv st-venv
source st-venv/bin/activate
pip install -r requirements.txt
```

## Step 1 — Generate real password hashes

Open `generate_hashes.py`, edit the `plain_passwords` list with real passwords, then run:

```bash
python3 generate_hashes.py
```

Copy each printed hash into `auth_config.yaml`, replacing the `REPLACE_WITH_HASH_FROM_generate_hashes.py` placeholders — match each hash to the right username.

## Step 2 — Set a real cookie secret

In `auth_config.yaml`, change `cookie.key` to any random string (this signs the login cookie — don't leave it as the placeholder).

## Step 3 — Start your FastAPI backend (separate terminal)

```bash
cd ../backend
source ca-venv/bin/activate
python3 -m uvicorn app.main:app --reload --reload-dir app
```

The Streamlit app calls this at `http://localhost:8000` — if it's not running, every page falls back to mock data automatically (see `api_client.py`), so the UI still works, just without real personalization.

## Step 4 — Run the Streamlit app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Log in with a username/password from `auth_config.yaml`, fill out the Intake form, then check the Dashboard and AI Mentor pages.

## For expo day

Set up a shared `guest` login (already stubbed in `auth_config.yaml`) with an easy password, and post it near your booth so visitors can log in without you creating an account for each person.

## Files

- `app.py` — main app: auth, intake form, dashboard, mentor chat
- `auth_config.yaml` — usernames/hashed passwords/cookie config
- `generate_hashes.py` — one-time script to hash passwords before adding them to the YAML
- `api_client.py` — wraps calls to the FastAPI backend, with fallback to mock data if it's unreachable
