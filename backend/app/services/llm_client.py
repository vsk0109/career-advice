"""
Wrapper around the LLM API (Gemini or OpenAI).

Kept in one place so the rest of the app never talks to the LLM provider
directly — this makes it easy to swap providers and, critically, guarantees
a safe fallback so a flaky API call (or a missing/expired key) never crashes
the live demo.

Setup:
  1. Get a free Gemini API key: https://aistudio.google.com/apikey
     (or an OpenAI key: https://platform.openai.com/api-keys)
  2. In backend/.env set:
       LLM_PROVIDER=gemini
       LLM_API_KEY=your_key_here
  3. pip install -r requirements.txt (google-generativeai is included)

If LLM_API_KEY is empty, or the API call fails for any reason (network,
quota, malformed response), every function here silently falls back to the
FALLBACK_* templates below rather than raising — the app stays fully
demoable even if the LLM is unavailable.
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
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

FALLBACK_TREND = (
    "This field is seeing growing demand as industries increasingly adopt new technology "
    "and data-driven approaches."
)

FALLBACK_CHAT_REPLY = (
    "That's a great question to explore! Based on your profile, I'd suggest looking closely "
    "at the top career matches on your dashboard and comparing the required skills against "
    "your own strengths. (Note: live AI responses are temporarily unavailable — this is a fallback reply.)"
)


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=LLM_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=LLM_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _call_ollama(prompt: str) -> str:
    """
    Calls a locally running Ollama server — no API key needed.
    Requires `ollama serve` running (it runs automatically in the background
    once you install the Ollama app) and a model already pulled, e.g.:
        ollama pull llama3.2
    Set OLLAMA_MODEL in .env to match whichever model you pulled.
    """
    import requests

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    response = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"]


def _call_llm(prompt: str) -> str:
    """Routes to the configured provider. Raises on any failure — callers handle fallback."""
    if LLM_PROVIDER == "ollama":
        # Ollama runs locally and needs no API key — skip the key check entirely.
        return _call_ollama(prompt)

    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY not set.")

    if LLM_PROVIDER == "gemini":
        return _call_gemini(prompt)
    elif LLM_PROVIDER == "openai":
        return _call_openai(prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def _extract_json(text: str) -> dict:
    """
    LLMs often wrap JSON in markdown code fences or add stray text around it.
    Pull out the first {...} block and parse it.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(match.group(0))


def generate_career_insights(student_profile: dict, top_matches: list[dict]) -> dict:
    """
    Returns {"explanations": {career_name: text}, "roadmap": [...], "emerging_trend": str}
    Falls back to safe generic content if the LLM call fails or returns unparseable output.
    """
    career_names = [m["career"] for m in top_matches]
    top_skill_gaps = top_matches[0].get("skill_gaps", []) if top_matches else []

    prompt = f"""You are a career mentor AI helping a student understand their career match results.

Student profile:
- Interests: {student_profile.get('interests')}
- Hobbies: {student_profile.get('hobbies')}
- Academic strengths: {student_profile.get('academics')}
- Self-rated skills: {student_profile.get('self_rated_skills')}

Top career matches (name, suitability score out of 100):
{json.dumps([{"career": m["career"], "score": m["score"]} for m in top_matches], indent=2)}

Skill gaps for the top match ({career_names[0] if career_names else 'N/A'}): {top_skill_gaps}

Respond with ONLY a valid JSON object (no markdown fences, no extra text) in exactly this shape:
{{
  "explanations": {{
    "<career name>": "2-sentence encouraging explanation of why this career fits this student, referencing their actual profile details"
  }},
  "roadmap": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "emerging_trend": "1-2 sentences on an emerging trend related to the top career match"
}}

Include an entry in "explanations" for every career listed above. Keep the roadmap specific to closing the listed skill gaps."""

    try:
        raw = _call_llm(prompt)
        parsed = _extract_json(raw)

        explanations = parsed.get("explanations", {})
        roadmap = parsed.get("roadmap", [])
        emerging_trend = parsed.get("emerging_trend", "")

        # Fill in any missing careers with the fallback line rather than failing outright
        for name in career_names:
            if name not in explanations or not explanations[name]:
                explanations[name] = FALLBACK_EXPLANATION

        if not roadmap:
            roadmap = FALLBACK_ROADMAP
        if not emerging_trend:
            emerging_trend = FALLBACK_TREND

        return {
            "explanations": explanations,
            "roadmap": roadmap,
            "emerging_trend": emerging_trend,
        }

    except Exception as e:
        print(f"[llm_client] generate_career_insights failed, using fallback: {e}")
        return {
            "explanations": {name: FALLBACK_EXPLANATION for name in career_names},
            "roadmap": FALLBACK_ROADMAP,
            "emerging_trend": FALLBACK_TREND,
        }


def generate_chat_reply(student_profile: dict, message: str) -> str:
    prompt = f"""You are a warm, encouraging career mentor AI for a student career guidance app.

Student profile:
- Interests: {student_profile.get('interests')}
- Hobbies: {student_profile.get('hobbies')}
- Academic strengths: {student_profile.get('academics')}
- Self-rated skills: {student_profile.get('self_rated_skills')}

The student asks: "{message}"

Give a helpful, specific, encouraging answer in 3-5 sentences. Reference their actual profile
details where relevant. Do not use markdown formatting — plain conversational text only."""

    try:
        reply = _call_llm(prompt)
        return reply.strip()
    except Exception as e:
        print(f"[llm_client] generate_chat_reply failed, using fallback: {e}")
        return FALLBACK_CHAT_REPLY
