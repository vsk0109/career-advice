"""
Thin requests-based client for the FastAPI backend. All calls that need
auth pull the JWT from st.session_state (set by login/signup) and attach it
as a Bearer token — this module is the only place that talks HTTP.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _auth_headers() -> dict:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle(resp: requests.Response):
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    return resp.json()


def signup(name: str, email: str, password: str) -> dict:
    resp = requests.post(f"{API_BASE_URL}/auth/signup", json={"name": name, "email": email, "password": password})
    return _handle(resp)


def login(email: str, password: str) -> dict:
    resp = requests.post(f"{API_BASE_URL}/auth/login", json={"email": email, "password": password})
    return _handle(resp)


def get_me() -> dict:
    return _handle(requests.get(f"{API_BASE_URL}/auth/me", headers=_auth_headers()))


def change_password(current_password: str, new_password: str) -> dict:
    return _handle(requests.post(
        f"{API_BASE_URL}/auth/change-password",
        json={"current_password": current_password, "new_password": new_password},
        headers=_auth_headers(),
    ))


def forgot_password(email: str) -> dict:
    return _handle(requests.post(f"{API_BASE_URL}/auth/forgot-password", json={"email": email}))


def reset_password(token: str, new_password: str) -> dict:
    return _handle(requests.post(
        f"{API_BASE_URL}/auth/reset-password", json={"token": token, "new_password": new_password}
    ))


def get_profile() -> dict:
    return _handle(requests.get(f"{API_BASE_URL}/profile", headers=_auth_headers()))


def submit_profile(payload: dict) -> dict:
    return _handle(requests.post(f"{API_BASE_URL}/profile", json=payload, headers=_auth_headers()))


def get_careers() -> list:
    return _handle(requests.get(f"{API_BASE_URL}/careers"))


def get_score() -> dict:
    return _handle(requests.post(f"{API_BASE_URL}/score", headers=_auth_headers()))


def get_insights(top_matches: list) -> dict:
    return _handle(requests.post(
        f"{API_BASE_URL}/score/insights", json={"top_matches": top_matches}, headers=_auth_headers()
    ))


def get_saved_insights() -> dict | None:
    """Returns previously generated insights, or None if none exist yet (404)."""
    resp = requests.get(f"{API_BASE_URL}/score/insights", headers=_auth_headers())
    if resp.status_code == 404:
        return None
    return _handle(resp)


def get_roadmap() -> dict:
    return _handle(requests.get(f"{API_BASE_URL}/roadmap", headers=_auth_headers()))


def update_roadmap_step(step_id: int, completed: bool) -> dict:
    return _handle(requests.patch(
        f"{API_BASE_URL}/roadmap/steps/{step_id}", json={"completed": completed}, headers=_auth_headers()
    ))


def get_chat_history() -> dict:
    return _handle(requests.get(f"{API_BASE_URL}/mentor/chat", headers=_auth_headers()))


def send_chat_message(message: str) -> dict:
    return _handle(requests.post(
        f"{API_BASE_URL}/mentor/chat", json={"message": message}, headers=_auth_headers()
    ))


def get_bookmarks() -> list:
    return _handle(requests.get(f"{API_BASE_URL}/bookmarks", headers=_auth_headers()))


def add_bookmark(career_id: str) -> dict:
    return _handle(requests.post(f"{API_BASE_URL}/bookmarks/{career_id}", headers=_auth_headers()))


def remove_bookmark(career_id: str) -> dict:
    return _handle(requests.delete(f"{API_BASE_URL}/bookmarks/{career_id}", headers=_auth_headers()))


def get_career_prep(career_id: str, force_refresh: bool = False) -> dict:
    return _handle(requests.post(
        f"{API_BASE_URL}/prep",
        json={"career_id": career_id, "force_refresh": force_refresh},
        headers=_auth_headers(),
    ))


def admin_list_careers() -> list:
    return _handle(requests.get(f"{API_BASE_URL}/admin/careers", headers=_auth_headers()))


def admin_create_career(payload: dict) -> dict:
    return _handle(requests.post(f"{API_BASE_URL}/admin/careers", json=payload, headers=_auth_headers()))


def admin_update_career(career_id: str, payload: dict) -> dict:
    return _handle(requests.put(f"{API_BASE_URL}/admin/careers/{career_id}", json=payload, headers=_auth_headers()))


def admin_delete_career(career_id: str) -> dict:
    return _handle(requests.delete(f"{API_BASE_URL}/admin/careers/{career_id}", headers=_auth_headers()))
