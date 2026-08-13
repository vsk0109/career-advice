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
       GEMINI_MODEL=gemini-1.5-flash   # optional, defaults to this
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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

FALLBACK_EXPLANATION = (
    "This career aligns well with your interests, personality profile, and academic strengths. "
    "Explore the recommended courses and certifications below to start building relevant experience."
)

FALLBACK_ROADMAP = [
    "Step 1 (Next 3 months): Strengthen your foundation in the core subjects relevant to this career and shortlist 2-3 undergraduate courses/colleges that match your interests.",
    "Step 2 (Next 6 months): Enroll in a beginner-friendly certification or online course to validate your interest and build a foundational skill.",
    "Step 3 (Next 6-12 months): Apply that skill in a small real project, internship, or volunteering role you can show in a portfolio or resume.",
    "Step 4 (Next 12-18 months): Close your biggest skill gap with an intermediate certification, and connect with 1-2 professionals in the field for informational interviews.",
    "Step 5 (Ongoing): Track entrance exams, scholarship deadlines, and application windows for your shortlisted colleges/courses so you don't miss key dates.",
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

FALLBACK_RESUME_BULLETS = [
    "Completed a structured self-assessment of interests, academic strengths, and skills relevant to this career.",
    "Identify a small project, internship, or volunteering opportunity in this field to add real, specific experience here.",
    "List any relevant coursework, certifications, or tools once completed — recruiters look for concrete evidence, not just interest.",
]

FALLBACK_INTERVIEW_QUESTIONS = [
    "Why are you interested in this career path, and what have you done so far to explore it?",
    "Walk me through a time you solved a problem using a skill relevant to this field.",
    "What do you think is the biggest challenge facing this industry right now, and how would you approach it?",
]


def _call_gemini(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=LLM_API_KEY)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=LLM_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _call_ollama(prompt: str, json_mode: bool = False) -> str:
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

    payload = {
        "model": model, "prompt": prompt, "stream": False,
        # Without this, Ollama falls back to a low default generation
        # length and silently truncates longer JSON responses (e.g. the
        # multi-career insights prompt) mid-object, breaking JSON parsing.
        "options": {"num_predict": 1024, "temperature": 0.3},
    }
    if json_mode:
        # Constrains decoding to syntactically valid JSON — small models
        # (e.g. llama3.2:3b) drop commas/braces often enough on free-form
        # "please output JSON" prompts that this, not just retrying, is what
        # makes structured output actually reliable.
        payload["format"] = "json"

    response = requests.post(f"{host}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"]


def _call_llm(prompt: str, json_mode: bool = False) -> str:
    """Routes to the configured provider. Raises on any failure — callers handle fallback."""
    if LLM_PROVIDER == "ollama":
        # Ollama runs locally and needs no API key — skip the key check entirely.
        return _call_ollama(prompt, json_mode=json_mode)

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


def _call_llm_json(prompt: str, retries: int = 2) -> dict:
    """
    Small local models (e.g. llama3.2:3b via Ollama) occasionally return
    slightly malformed JSON (a dropped comma, an unescaped character) even
    when the prompt and response length are otherwise fine — it's model
    flakiness, not a deterministic bug, so a retry succeeds most of the time
    without the caller ever needing to fall back to generic text.
    """
    last_error = None
    for _ in range(retries + 1):
        try:
            raw = _call_llm(prompt, json_mode=True)
            return _extract_json(raw)
        except Exception as e:
            last_error = e
    raise last_error


def generate_career_insights(student_profile: dict, top_matches: list[dict]) -> dict:
    """
    Returns {"explanations": {career_name: text}, "roadmap": [...], "emerging_trend": str}
    Falls back to safe generic content if the LLM call fails or returns unparseable output.
    """
    career_names = [m["career"] for m in top_matches]
    top_match = top_matches[0] if top_matches else {}
    top_skill_gaps = top_match.get("skill_gaps", [])
    top_courses = top_match.get("courses", [])
    top_colleges = top_match.get("colleges", [])
    top_certifications = top_match.get("certifications", [])

    prompt = f"""You are a career mentor AI helping a student understand their career match results.

Student profile:
- Interests: {student_profile.get('interests')}
- Hobbies: {student_profile.get('hobbies')}
- Academic strengths: {student_profile.get('academics')}
- Self-rated skills: {student_profile.get('self_rated_skills')}

Top career matches (name, suitability score out of 100):
{json.dumps([{"career": m["career"], "score": m["score"]} for m in top_matches], indent=2)}

For the top match ({career_names[0] if career_names else 'N/A'}):
- Skill gaps: {top_skill_gaps}
- Recommended courses: {top_courses}
- Recommended colleges: {top_colleges}
- Relevant certifications: {top_certifications}

Respond with ONLY a valid JSON object (no markdown fences, no extra text) in exactly this shape:
{{
  "explanations": {{
    "<career name>": "2-sentence encouraging explanation of why this career fits this student, referencing their actual profile details"
  }},
  "roadmap": [
    "Step 1 (timeframe, e.g. 'Next 3 months'): ...",
    "Step 2 (timeframe): ...",
    "Step 3 (timeframe): ...",
    "Step 4 (timeframe): ...",
    "Step 5 (timeframe): ..."
  ],
  "emerging_trend": "1-2 sentences on an emerging trend related to the top career match"
}}

Include an entry in "explanations" for every career listed above. Write exactly 5 roadmap steps, each prefixed with a
concrete timeframe (e.g. "Next 3 months", "6-12 months", "Ongoing") so the plan reads like a practical timeline, not
a vague checklist. Ground the steps in real, actionable moves for closing the listed skill gaps — naming specific
courses, colleges, certifications, or project ideas from the data above where relevant, rather than generic advice."""

    try:
        parsed = _call_llm_json(prompt)

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


def generate_chat_reply(student_profile: dict, message: str, history: list[dict] | None = None) -> str:
    history_block = ""
    if history:
        turns = "\n".join(f"{h['sender']}: {h['message']}" for h in history[-6:])
        history_block = f"\nRecent conversation so far:\n{turns}\n"

    prompt = f"""You are a warm, encouraging career mentor AI for a student career guidance app.

Student profile:
- Interests: {student_profile.get('interests')}
- Hobbies: {student_profile.get('hobbies')}
- Academic strengths: {student_profile.get('academics')}
- Self-rated skills: {student_profile.get('self_rated_skills')}
{history_block}
The student asks: "{message}"

Give a helpful, specific, encouraging answer in 3-5 sentences. Reference their actual profile
details where relevant. Do not use markdown formatting — plain conversational text only."""

    try:
        reply = _call_llm(prompt)
        return reply.strip()
    except Exception as e:
        print(f"[llm_client] generate_chat_reply failed, using fallback: {e}")
        return FALLBACK_CHAT_REPLY


def generate_career_prep(student_profile: dict, career: dict) -> dict:
    """
    Returns {"resume_bullets": [...], "interview_questions": [...]} tailored to
    one specific career and this student's profile. Falls back to safe
    generic content if the LLM call fails or returns unparseable output.
    """
    prompt = f"""You are a career mentor AI helping a student prepare application materials for a specific career.

Student profile:
- Interests: {student_profile.get('interests')}
- Hobbies: {student_profile.get('hobbies')}
- Academic strengths: {student_profile.get('academics')}
- Self-rated skills: {student_profile.get('self_rated_skills')}

Target career: {career.get('name')}
Career description: {career.get('description')}
Required skills for this career: {career.get('required_skills')}

Respond with ONLY a valid JSON object (no markdown fences, no extra text) in exactly this shape:
{{
  "resume_bullets": [
    "3-4 resume bullet points a student at this stage could realistically write or work toward, phrased as achievements/actions"
  ],
  "interview_questions": [
    "3-4 realistic entry-level/college-admission interview questions for this career, tailored to this student's background"
  ]
}}

Ground the resume bullets in this student's actual profile (their interests, academics, self-rated skills) rather than
generic advice — if they lack direct experience, phrase bullets as concrete next steps (a project, certification, or
activity) they could complete to earn that bullet, not as if they already have years of experience."""

    try:
        parsed = _call_llm_json(prompt)

        resume_bullets = parsed.get("resume_bullets") or FALLBACK_RESUME_BULLETS
        interview_questions = parsed.get("interview_questions") or FALLBACK_INTERVIEW_QUESTIONS

        return {"resume_bullets": resume_bullets, "interview_questions": interview_questions}

    except Exception as e:
        print(f"[llm_client] generate_career_prep failed, using fallback: {e}")
        return {"resume_bullets": FALLBACK_RESUME_BULLETS, "interview_questions": FALLBACK_INTERVIEW_QUESTIONS}
