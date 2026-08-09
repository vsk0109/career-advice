"""
Wrapper around the LLM API (Gemini or OpenAI).

Kept in one place so the rest of the app never talks to the LLM provider
directly — this makes it easy to swap providers and, critically, to add a
safe fallback so a flaky API call never crashes the live demo.

Fill in the actual API call in `_call_llm` once you have an API key.
Until then, this returns the FALLBACK_* templates so the rest of the app
is fully testable without a key.
"""

import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

FALLBACK_EXPLANATION = (
    "This career aligns well with your interests, personality profile, and academic strengths. "
    "Explore the recommended courses and certifications below to start building relevant experience."
)

FALLBACK_ROADMAP = [
    "Step 1: Strengthen your foundation in the core subjects relevant to this career.",
    "Step 2: Take an introductory certification course to build practical skills.",
    "Step 3: Work on a small personal project to apply what you've learned.",
]

FALLBACK_TREND = "This field is seeing growing demand as industries increasingly adopt new technology and data-driven approaches."


def _call_llm(prompt: str) -> str:
    """
    Replace this with a real API call once you have a key, e.g.:

    import google.generativeai as genai
    genai.configure(api_key=LLM_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

    Keep this function's signature (str in, str out) so callers don't change.
    """
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY not set — using fallback response.")

    # TODO: implement real provider call here (Gemini or OpenAI).
    raise NotImplementedError("LLM provider call not yet implemented.")


def generate_career_insights(student_profile: dict, top_matches: list[dict]) -> dict:
    """
    Returns {"explanations": {career_name: text}, "roadmap": [...], "emerging_trend": str}
    Falls back to safe generic content if the LLM call fails for any reason.
    """
    try:
        careers_summary = "; ".join(
            f"{m['career']} (score {m['score']})" for m in top_matches
        )
        prompt = (
            f"Student profile: interests={student_profile.get('interests')}, "
            f"academics={student_profile.get('academics')}. "
            f"Top career matches: {careers_summary}. "
            f"For each career, write a 2-sentence explanation of why it fits. "
            f"Then write a 3-step personalized learning roadmap for the top match, "
            f"addressing these skill gaps: {top_matches[0].get('skill_gaps') if top_matches else []}. "
            f"Finally, name one emerging trend related to the top match."
        )
        _call_llm(prompt)
        # TODO: parse the real LLM response into this shape once _call_llm is implemented.
        raise NotImplementedError
    except Exception:
        explanations = {m["career"]: FALLBACK_EXPLANATION for m in top_matches}
        return {
            "explanations": explanations,
            "roadmap": FALLBACK_ROADMAP,
            "emerging_trend": FALLBACK_TREND,
        }


def generate_chat_reply(student_profile: dict, message: str) -> str:
    try:
        prompt = (
            f"You are a career mentor. Student profile: {student_profile}. "
            f"Student asks: {message}. Give a helpful, encouraging, specific answer."
        )
        return _call_llm(prompt)
    except Exception:
        return (
            "That's a great question to explore! Based on your profile, I'd suggest looking closely "
            "at the top career matches on your dashboard and comparing the required skills against "
            "your own strengths. (Note: live AI responses are temporarily unavailable — this is a fallback reply.)"
        )
