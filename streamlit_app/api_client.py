"""
Thin wrapper around your FastAPI backend. Falls back to mock data if the
backend isn't reachable, so the Streamlit UI is never fully broken during
dev or a demo — same safety principle as llm_client.py's fallback design.
"""

import requests

API_BASE = "http://localhost:8000"
TIMEOUT = 5

MOCK_TOP_MATCHES = [
    {"career": "AI Engineer", "score": 94.0, "skill_gaps": ["Deep Learning", "MLOps"]},
    {"career": "Data Scientist", "score": 91.0, "skill_gaps": ["Statistics", "Machine Learning"]},
    {"career": "Software Engineer", "score": 89.0, "skill_gaps": ["System Design"]},
    {"career": "Robotics Engineer", "score": 84.0, "skill_gaps": ["Control Systems"]},
]

MOCK_INSIGHTS = {
    "explanations": {
        "AI Engineer": "Your strong Math and Investigative profile point clearly toward AI engineering roles.",
    },
    "roadmap": [
        "Step 1: Strengthen Python and statistics fundamentals.",
        "Step 2: Build a small machine learning project.",
        "Step 3: Take an intro certification in ML/AI.",
    ],
    "emerging_trend": "AI-augmented roles are among the fastest-growing career categories right now.",
}


def create_profile(profile_data: dict) -> dict | None:
    """POST /profile. Returns the response dict, or None if the backend is unreachable."""
    try:
        r = requests.post(f"{API_BASE}/profile", json=profile_data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def get_score(student_id: str) -> list[dict]:
    """POST /score. Falls back to mock top matches if the backend is unreachable."""
    try:
        r = requests.post(f"{API_BASE}/score", json={"student_id": student_id}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["top_matches"]
    except requests.RequestException:
        return MOCK_TOP_MATCHES


def get_insights(student_id: str, top_matches: list[dict]) -> dict:
    """POST /score/insights. Falls back to mock insights if unreachable."""
    try:
        r = requests.post(
            f"{API_BASE}/score/insights",
            json={"student_id": student_id, "top_matches": top_matches},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return MOCK_INSIGHTS


MOCK_CAREERS = [
    {
        "id": "ai-engineer", "name": "AI Engineer",
        "description": "Builds and deploys machine learning systems in production.",
        "courses": [{"name": "B.Tech AI & ML", "level": "undergrad"}],
        "colleges": [{"name": "IIT Bombay", "location": "Mumbai"}],
        "scholarships": [{"name": "AICTE Pragati Scholarship", "eligibility": "Girl students in technical courses"}],
        "certifications": [{"name": "DeepLearning.AI TensorFlow Certificate", "provider": "Coursera"}],
        "emerging": True,
    },
    {
        "id": "data-scientist", "name": "Data Scientist",
        "description": "Analyzes large datasets to uncover patterns and drive decisions.",
        "courses": [{"name": "B.Sc Statistics", "level": "undergrad"}],
        "colleges": [{"name": "ISI Kolkata", "location": "Kolkata"}],
        "scholarships": [{"name": "Central Sector Scholarship", "eligibility": "Merit-based"}],
        "certifications": [{"name": "Google Data Analytics Certificate", "provider": "Coursera"}],
        "emerging": True,
    },
]


_careers_cache: list[dict] | None = None


def get_all_careers() -> list[dict]:
    """
    GET /careers. Cached in-process after the first successful call since
    the career dataset is static and doesn't change per-student — avoids
    re-fetching it on every page navigation. Falls back to a small mock
    list if the backend is unreachable (and doesn't cache that fallback,
    so it'll retry the real backend next time).
    """
    global _careers_cache
    if _careers_cache is not None:
        return _careers_cache
    try:
        r = requests.get(f"{API_BASE}/careers", timeout=TIMEOUT)
        r.raise_for_status()
        _careers_cache = r.json()
        return _careers_cache
    except requests.RequestException:
        return MOCK_CAREERS


def get_profile(student_id: str) -> dict | None:
    """GET /profile/{student_id}. Returns None if unreachable or not found."""
    try:
        r = requests.get(f"{API_BASE}/profile/{student_id}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def send_chat_message(student_id: str, message: str) -> str:
    """POST /mentor/chat. Falls back to a generic reply if unreachable."""
    try:
        r = requests.post(
            f"{API_BASE}/mentor/chat",
            json={"student_id": student_id, "message": message},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["reply"]
    except requests.RequestException:
        return "(Backend not reachable — this is a placeholder reply. Start your FastAPI server to get real answers.)"
