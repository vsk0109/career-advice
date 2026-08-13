"""
Career AI — Streamlit frontend for the AI-Powered Career Mentor backend.

Talks to the FastAPI backend (api_client.py) over HTTP with JWT auth.
Session state holds the token and cached responses; nothing here talks to
MySQL or the LLM directly.
"""

from html import escape

import altair as alt
import streamlit as st

import api_client as api

st.set_page_config(page_title="Career Mentor", page_icon="🧭", layout="wide")


# ---------------------------------------------------------------------------
# Design system — a single dark theme, configured natively via
# .streamlit/config.toml rather than CSS overrides. Streamlit uses that
# config to color every built-in widget itself (buttons, sliders,
# checkboxes, chat input, sidebar, header) correctly and consistently —
# previous attempts to force these via injected !important CSS fought
# Streamlit's own internal styling widget-by-widget and kept regressing.
# The CSS below only styles our own custom HTML (cards, tags, brand mark),
# which config.toml has no reach into.
# ---------------------------------------------------------------------------

BG = "#14120f"
SURFACE = "#1c1a16"
TEXT = "#f2efe9"
MUTED = "#a39d90"
BORDER = "#33302a"
ACCENT = "#d4a94c"

CUSTOM_CSS = f"""
<style>
.hero-title {{ font-size:1.9rem; font-weight:600; margin:0 0 4px; }}
.hero-subtitle {{ color:{MUTED}; font-size:.95rem; margin:0 0 24px; }}

.brand {{ display:flex; align-items:center; gap:8px; margin:4px 0 20px; }}
.brand-mark {{ color:{ACCENT}; display:flex; flex-shrink:0; }}
.brand-name {{ font-size:1.15rem; font-weight:700; letter-spacing:-.3px; color:{TEXT}; }}
.brand-name .accent-dot {{ color:{ACCENT}; }}

.card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:10px; padding:20px; height:100%; }}
.card h3 {{ font-size:.85rem; font-weight:600; margin:0 0 6px; text-transform:uppercase; letter-spacing:.5px; color:{MUTED}; }}
.muted {{ color:{MUTED} !important; }}
.accent {{ color:{ACCENT} !important; }}

.metric {{ font-size:2.1rem; font-weight:700; margin:8px 0 2px; color:{TEXT}; }}
.metric-small {{ font-size:1.5rem; }}

.career-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:10px; padding:18px; min-height:190px; }}
.career-name {{ font-size:1rem; font-weight:600; margin:6px 0; color:{TEXT}; }}
.score-badge {{ float:right; border:1px solid {ACCENT}; color:{ACCENT}; padding:2px 8px; border-radius:6px; font-size:.75rem; font-weight:600; }}

.ai-card {{ background:{SURFACE}; border:1px solid {ACCENT}; border-radius:10px; padding:20px; }}
.ai-card h3 {{ text-transform:none; letter-spacing:0; font-size:1rem; color:{TEXT}; }}
.ai-card p {{ color:{TEXT}; }}

.tag {{ display:inline-block; border:1px solid {BORDER}; border-radius:6px; padding:3px 9px; color:{MUTED}; font-size:.78rem; margin:4px 6px 0 0; }}

.roadmap-step {{ display:flex; gap:12px; align-items:flex-start; border-left:2px solid {BORDER}; padding:0 0 14px 14px; margin-left:6px; }}
.roadmap-step:last-child {{ padding-bottom:0; }}

.login-panel {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:10px; padding:36px; }}
.login-title {{ font-size:1.7rem; font-weight:600; margin:0 0 8px; }}
.login-subtitle {{ color:{MUTED}; font-size:.92rem; margin-bottom:18px; }}

#MainMenu, footer {{ visibility:hidden; }}
.block-container {{ max-width:1200px; padding-top:2rem; padding-bottom:3rem; }}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Logomark — a rounded badge with a compass-needle/signpost motif (guidance +
# direction), rendered as inline SVG so it stays crisp at any size and can
# reuse the app's accent color instead of needing a separate image asset.
BRAND_MARK_SVG = (
    "<svg class='brand-mark' width='30' height='30' viewBox='0 0 32 32' fill='none' "
    "xmlns='http://www.w3.org/2000/svg'>"
    f"<circle cx='16' cy='16' r='15' fill='{ACCENT}'/>"
    f"<circle cx='16' cy='16' r='15' stroke='{ACCENT}' stroke-opacity='0.35' stroke-width='1'/>"
    f"<path d='M16 7L19.5 14.5L27 16L19.5 17.5L16 25L12.5 17.5L5 16L12.5 14.5L16 7Z' fill='{BG}'/>"
    f"<circle cx='16' cy='16' r='2.4' fill='{ACCENT}'/>"
    "</svg>"
)
BRAND_HTML = f"<div class='brand'>{BRAND_MARK_SVG}<div class='brand-name'>Career<span class='accent-dot'> Mentor</span></div></div>"


def title(text: str, subtitle: str) -> None:
    st.markdown(
        f"<div class='hero-title'>{escape(text)}</div><div class='hero-subtitle'>{escape(subtitle)}</div>",
        unsafe_allow_html=True,
    )


def tags_html(items: list[str]) -> str:
    return "".join(f"<span class='tag'>{escape(str(item))}</span>" for item in items) or "<span class='muted'>None yet</span>"


RIASEC_INFO = {
    "R": ("Realistic", "Hands-on, practical — enjoys working with tools, machines, or the outdoors."),
    "I": ("Investigative", "Analytical, curious — enjoys research, data, and solving complex problems."),
    "A": ("Artistic", "Creative, expressive — enjoys design, writing, and original self-expression."),
    "S": ("Social", "Helpful, people-focused — enjoys teaching, counseling, and collaboration."),
    "E": ("Enterprising", "Persuasive, driven — enjoys leadership, business, and taking initiative."),
    "C": ("Conventional", "Organized, detail-oriented — enjoys structure, data accuracy, and process."),
}


def render_riasec_chart(riasec_scores: dict) -> None:
    """st.bar_chart has a fixed plot background/color scheme unrelated to
    our app's theme — Altair gives full control to match it instead."""
    import pandas as pd

    labels = {code: f"{code} · {RIASEC_INFO[code][0]}" for code in riasec_scores}
    df = pd.DataFrame({
        "dimension": [labels[code] for code in riasec_scores],
        "score": list(riasec_scores.values()),
    })

    top_code = max(riasec_scores, key=riasec_scores.get)
    top_name, top_desc = RIASEC_INFO[top_code]

    chart = (
        alt.Chart(df)
        .mark_bar(color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("dimension", sort=None, title=None, axis=alt.Axis(labelColor=TEXT, domainColor=BORDER, tickColor=BORDER)),
            y=alt.Y("score", title=None, axis=alt.Axis(labelColor=MUTED, gridColor=BORDER, domainColor=BORDER, tickColor=BORDER)),
        )
        .properties(background=SURFACE, height=280)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown(
        f"<div class='card' style='margin-bottom:16px;'>"
        f"<h3>Your dominant trait: {escape(top_name)}</h3>"
        f"<p class='muted' style='margin:0;'>{escape(top_desc)}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    legend_items = "".join(
        f"<div style='padding:10px 0;border-bottom:1px solid {BORDER};'>"
        f"<span class='accent' style='font-weight:700;'>{code}</span> — "
        f"<strong>{escape(name)}</strong>: <span class='muted'>{escape(desc)}</span>"
        f"</div>"
        for code, (name, desc) in RIASEC_INFO.items()
    )
    st.markdown(f"<div class='card'>{legend_items}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Fixed vocab — must match backend/app/data/careers_seed.json and
# riasec_questions.py so scoring actually has something to match against.
# ---------------------------------------------------------------------------

RIASEC_QUESTIONS = [
    ("I enjoy fixing, building, or working with tools and machines.", "R"),
    ("I like working outdoors or with my hands.", "R"),
    ("I enjoy solving puzzles, analyzing data, or doing research.", "I"),
    ("I like understanding how and why things work.", "I"),
    ("I enjoy creative writing, art, music, or design.", "A"),
    ("I like expressing myself in original or unconventional ways.", "A"),
    ("I enjoy helping, teaching, or counseling other people.", "S"),
    ("I like working in teams and communicating with others.", "S"),
    ("I enjoy leading projects, persuading people, or starting new ventures.", "E"),
    ("I like taking initiative and being in charge.", "E"),
    ("I enjoy organizing information, following procedures, and being detail-oriented.", "C"),
    ("I like structured tasks with clear rules and steps.", "C"),
]

SUBJECTS = ["Art", "Biology", "Business Studies", "Chemistry", "Computer Science",
            "Economics", "English", "Geography", "Math", "Physics", "Psychology", "Statistics"]

SKILLS = ["Active Listening", "Coding", "Communication", "Creativity", "Data Analysis",
          "Debugging", "Design Tools", "Empathy", "Fieldwork", "Financial Literacy",
          "Leadership", "Machine Learning", "Problem Solving", "Python", "Report Writing",
          "Research", "Risk-Taking", "Statistics", "Teamwork", "User Research"]

INTEREST_TAGS = ["art", "business", "coding", "counseling", "creativity", "data", "design",
                  "environment", "healthcare", "helping", "innovation", "leadership",
                  "problem-solving", "psychology", "research", "science", "sustainability", "technology"]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "access_token": None, "student_id": None, "name": None, "email": None, "is_admin": False,
        "nav_page": "Dashboard", "profile": None, "score": None, "insights": None,
        "insights_checked": False, "bookmark_ids": None, "all_careers": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def is_authenticated() -> bool:
    return st.session_state.access_token is not None


def has_completed_profile() -> bool:
    profile = st.session_state.profile
    return bool(profile and profile.get("riasec_scores"))


def logout() -> None:
    for key in ("access_token", "student_id", "name", "email", "is_admin", "profile", "score",
                "insights", "insights_checked", "bookmark_ids", "all_careers"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()


def refresh_profile() -> None:
    try:
        st.session_state.profile = api.get_profile()
    except api.APIError as e:
        st.error(f"Couldn't load your profile: {e.detail}")


def restore_session_from_url() -> None:
    """Streamlit's session_state lives only for the current WebSocket
    connection — a browser refresh starts a brand-new one and wipes it, which
    would otherwise force a re-login on every reload. Keeping the JWT in the
    URL query string lets a fresh session recover it and restore state."""
    if st.session_state.access_token is not None:
        return
    token = st.query_params.get("token")
    if not token:
        return

    st.session_state.access_token = token
    try:
        me = api.get_me()
        st.session_state.student_id = me["student_id"]
        st.session_state.name = me["name"]
        st.session_state.email = me["email"]
        st.session_state.is_admin = me.get("is_admin", False)
        refresh_profile()
    except api.APIError:
        # Token expired/invalid — drop it rather than get stuck in a loop.
        st.session_state.access_token = None
        st.query_params.clear()


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------

def render_auth() -> None:
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        st.markdown(
            "<div class='login-panel'>"
            f"{BRAND_HTML}"
            "<h1 class='login-title'>Find your path</h1>"
            "<div class='login-subtitle'>Personalized career guidance, backed by your own profile.</div>",
            unsafe_allow_html=True,
        )

        login_tab, signup_tab, forgot_tab = st.tabs(["Log in", "Sign up", "Forgot password?"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.warning("Enter both email and password.")
                else:
                    try:
                        result = api.login(email, password)
                        _apply_auth_result(result)
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.detail)

        with signup_tab:
            with st.form("signup_form"):
                name = st.text_input("Name", placeholder="Your name", key="signup_name")
                email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password",
                                          help="Minimum 8 characters")
                submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                if not name or not email or not password:
                    st.warning("Fill in name, email, and password.")
                elif len(password) < 8:
                    st.warning("Password must be at least 8 characters.")
                else:
                    try:
                        result = api.signup(name, email, password)
                        _apply_auth_result(result)
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.detail)

        with forgot_tab:
            st.markdown(
                "<p class='muted'>Email delivery isn't wired up yet, so the reset token is shown "
                "directly below instead of being emailed — for local/demo use only.</p>",
                unsafe_allow_html=True,
            )
            with st.form("forgot_form"):
                forgot_email = st.text_input("Email", placeholder="you@example.com", key="forgot_email")
                requested = st.form_submit_button("Request reset token", use_container_width=True)
            if requested:
                if not forgot_email:
                    st.warning("Enter your email.")
                else:
                    try:
                        result = api.forgot_password(forgot_email)
                        if result.get("reset_token"):
                            st.success("Reset token generated — copy it below (valid for 30 minutes).")
                            st.code(result["reset_token"])
                        else:
                            st.info(result["detail"])
                    except api.APIError as e:
                        st.error(e.detail)

            with st.form("reset_form"):
                reset_token = st.text_input("Reset token", key="reset_token_input")
                new_password = st.text_input("New password", type="password", key="reset_new_password",
                                              help="Minimum 8 characters")
                reset_submitted = st.form_submit_button("Reset password", use_container_width=True)
            if reset_submitted:
                if not reset_token or not new_password:
                    st.warning("Enter both the reset token and a new password.")
                elif len(new_password) < 8:
                    st.warning("Password must be at least 8 characters.")
                else:
                    try:
                        result = api.reset_password(reset_token, new_password)
                        st.success(result["detail"])
                    except api.APIError as e:
                        st.error(e.detail)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            "<div class='card' style='min-height:520px;display:flex;flex-direction:column;justify-content:center;'>"
            "<h2 style='text-transform:none;letter-spacing:0;font-size:1.8rem;'>Every interest can become "
            "a <span class='accent'>future</span>.</h2>"
            "<p class='muted'>Take a short personality and skills assessment, and get ranked career "
            "matches with real courses, colleges, and scholarships.</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def _apply_auth_result(result: dict) -> None:
    st.session_state.access_token = result["access_token"]
    st.session_state.student_id = result["student_id"]
    st.session_state.name = result["name"]
    st.session_state.email = result["email"]
    st.session_state.is_admin = result.get("is_admin", False)
    st.query_params["token"] = result["access_token"]
    refresh_profile()


def get_bookmark_ids() -> set:
    if st.session_state.bookmark_ids is None:
        try:
            st.session_state.bookmark_ids = {c["id"] for c in api.get_bookmarks()}
        except api.APIError:
            st.session_state.bookmark_ids = set()
    return st.session_state.bookmark_ids


def toggle_bookmark(career_id: str) -> bool | None:
    """Returns True if the career is now bookmarked, False if unbookmarked, None on error."""
    try:
        if career_id in get_bookmark_ids():
            api.remove_bookmark(career_id)
            st.session_state.bookmark_ids.discard(career_id)
            return False
        else:
            api.add_bookmark(career_id)
            st.session_state.bookmark_ids.add(career_id)
            return True
    except api.APIError as e:
        st.error(f"Couldn't update bookmark: {e.detail}")
        return None


# ---------------------------------------------------------------------------
# Assessment (intake form)
# ---------------------------------------------------------------------------

def render_assessment() -> None:
    title("Let's get to know you", "Your answers drive your career matches — you can retake this anytime.")
    profile = st.session_state.profile or {}
    saved_answers = profile.get("riasec_answers") or []
    saved_academics = profile.get("academics") or {}
    saved_skills = profile.get("self_rated_skills") or {}

    with st.form("assessment_form"):
        st.markdown("<div class='card'><h3>Personality (RIASEC)</h3>"
                     "<p class='muted'>Rate how much each statement sounds like you, 1 (not at all) to 5 (very much).</p></div>",
                     unsafe_allow_html=True)
        riasec_answers = []
        cols = st.columns(2)
        for i, (statement, _dim) in enumerate(RIASEC_QUESTIONS):
            default = saved_answers[i] if i < len(saved_answers) else 3
            with cols[i % 2]:
                riasec_answers.append(st.slider(statement, 1, 5, default, key=f"riasec_{i}"))

        st.markdown("<div class='card'><h3>Academics</h3>"
                     "<p class='muted'>Enter marks (0-100) only for subjects you've taken — leave others at 0.</p></div>",
                     unsafe_allow_html=True)
        academics = {}
        cols = st.columns(3)
        for i, subject in enumerate(SUBJECTS):
            with cols[i % 3]:
                mark = st.number_input(subject, min_value=0, max_value=100,
                                        value=int(saved_academics.get(subject, 0)), step=1, key=f"academic_{subject}")
                if mark > 0:
                    academics[subject] = mark

        st.markdown("<div class='card'><h3>Self-rated skills</h3>"
                     "<p class='muted'>Rate skills you actually have, 1-5 — leave others at 0 to skip.</p></div>",
                     unsafe_allow_html=True)
        self_rated_skills = {}
        cols = st.columns(4)
        for i, skill in enumerate(SKILLS):
            with cols[i % 4]:
                level = st.slider(skill, 0, 5, int(saved_skills.get(skill, 0)), key=f"skill_{skill}")
                if level > 0:
                    self_rated_skills[skill] = level

        st.markdown("<div class='card'><h3>Interests &amp; hobbies</h3></div>", unsafe_allow_html=True)
        interests = st.multiselect("Interests", INTEREST_TAGS, default=profile.get("interests") or [], key="interests")
        hobbies_default = ", ".join(profile.get("hobbies") or [])
        hobbies_raw = st.text_input("Hobbies (comma-separated)", value=hobbies_default,
                                     placeholder="e.g. reading, chess, painting", key="hobbies")
        hobbies = [h.strip() for h in hobbies_raw.split(",") if h.strip()]

        submitted = st.form_submit_button("Save and see my matches", use_container_width=True)

    if submitted:
        if not interests:
            st.warning("Pick at least one interest.")
            return
        try:
            api.submit_profile({
                "interests": interests,
                "hobbies": hobbies,
                "riasec_answers": riasec_answers,
                "academics": academics,
                "self_rated_skills": self_rated_skills,
            })
            refresh_profile()
            st.session_state.score = None
            st.session_state.insights = None
            st.session_state.insights_checked = False
            st.session_state.nav_page = "Dashboard"
            st.rerun()
        except api.APIError as e:
            st.error(f"Couldn't save your profile: {e.detail}")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    profile = st.session_state.profile
    title(f"Good to see you, {profile['name']}", "Here's where your profile points you.")

    if st.session_state.score is None:
        with st.spinner("Computing your career matches..."):
            try:
                st.session_state.score = api.get_score()
            except api.APIError as e:
                st.error(f"Couldn't compute matches: {e.detail}")
                return
        st.rerun()

    matches = st.session_state.score["top_matches"]
    top = matches[0]

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='card'><h3>Top match</h3><div class='metric metric-small'>{escape(top['career'])}</div>"
                     f"<p class='accent'>{top['score']}% suitability</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='card'><h3>RIASEC match</h3><div class='metric'>{top['riasec_match']}%</div>"
                     f"<p class='muted'>Personality fit for {escape(top['career'])}</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='card'><h3>Academic fit</h3><div class='metric'>{top['academic_fit']}%</div>"
                     f"<p class='muted'>Based on your entered marks</p></div>", unsafe_allow_html=True)

    st.markdown("<h2>Your RIASEC profile</h2>", unsafe_allow_html=True)
    render_riasec_chart(profile["riasec_scores"])

    st.markdown("<h2>Top career matches</h2>", unsafe_allow_html=True)
    cols = st.columns(len(matches))
    for col, match in zip(cols, matches):
        with col:
            st.markdown(
                f"<div class='career-card'><span class='score-badge'>{match['score']}%</span>"
                f"<div class='career-name'>{escape(match['career'])}</div>"
                f"<p class='muted'>Skill gaps:</p>{tags_html(match['skill_gaps'])}</div>",
                unsafe_allow_html=True,
            )
            bookmarked = match["career_id"] in get_bookmark_ids()
            if st.button("★ Bookmarked" if bookmarked else "☆ Bookmark", key=f"bookmark_{match['career_id']}",
                         use_container_width=True):
                toggle_bookmark(match["career_id"])
                st.rerun()

            with st.expander("Resume & interview prep"):
                if st.button("Ask mentor for resume & interview prep", key=f"prep_{match['career_id']}",
                             use_container_width=True):
                    with st.spinner("Asking the AI mentor..."):
                        try:
                            api.send_chat_message(
                                f"Can you suggest a few resume bullet points and likely interview questions "
                                f"for a career as a {match['career']}, based on my profile?"
                            )
                            st.session_state.nav_page = "Mentor"
                            st.rerun()
                        except api.APIError as e:
                            st.error(f"Couldn't reach the mentor: {e.detail}")

    st.markdown("<h2>AI insights</h2>", unsafe_allow_html=True)
    if st.session_state.insights is None and not st.session_state.insights_checked:
        st.session_state.insights_checked = True
        try:
            st.session_state.insights = api.get_saved_insights()
        except api.APIError as e:
            st.error(f"Couldn't load saved insights: {e.detail}")
        if st.session_state.insights is not None:
            st.rerun()

    if st.session_state.insights is None:
        if st.button("Get AI explanations and roadmap"):
            with st.spinner("Asking the AI mentor for explanations and a roadmap — this can take up to a minute..."):
                try:
                    st.session_state.insights = api.get_insights(matches)
                    st.rerun()
                except api.APIError as e:
                    st.error(f"Couldn't generate insights: {e.detail}")
    else:
        insights = st.session_state.insights
        for career, explanation in insights["explanations"].items():
            st.markdown(
                f"<div class='ai-card'><h3>{escape(career)}</h3><p>{escape(explanation)}</p></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div class='card'><h3>Emerging trend</h3><p class='muted'>{escape(insights['emerging_trend'])}</p></div>",
            unsafe_allow_html=True,
        )
        st.info("A roadmap for your top match has been saved — see the Roadmap page to track progress.")

        if st.button("Regenerate AI insights"):
            with st.spinner("Asking the AI mentor for explanations and a roadmap — this can take up to a minute..."):
                try:
                    st.session_state.insights = api.get_insights(matches)
                    st.rerun()
                except api.APIError as e:
                    st.error(f"Couldn't regenerate insights: {e.detail}")

    if st.button("Recompute matches (after updating your profile)"):
        st.session_state.score = None
        st.session_state.insights = None
        st.session_state.insights_checked = False
        st.rerun()


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

def render_roadmap() -> None:
    title("Your roadmap", "Track progress on the steps generated for your top career match.")
    try:
        steps = api.get_roadmap()["steps"]
    except api.APIError as e:
        st.error(f"Couldn't load your roadmap: {e.detail}")
        return

    if not steps:
        st.info("No roadmap yet — visit the Dashboard and generate AI insights first.")
        return

    careers_in_roadmap = sorted({s["career"] for s in steps})
    for career in careers_in_roadmap:
        st.markdown(f"<h3>{escape(career)}</h3>", unsafe_allow_html=True)
        for step in [s for s in steps if s["career"] == career]:
            checked = st.checkbox(step["description"], value=step["completed"], key=f"step_{step['step_id']}")
            if checked != step["completed"]:
                try:
                    api.update_roadmap_step(step["step_id"], checked)
                    st.rerun()
                except api.APIError as e:
                    st.error(f"Couldn't update step: {e.detail}")


# ---------------------------------------------------------------------------
# Mentor chat
# ---------------------------------------------------------------------------

def render_mentor() -> None:
    title("Mentor", "Ask anything about your career matches.")
    try:
        history = api.get_chat_history()["messages"]
    except api.APIError as e:
        st.error(f"Couldn't load chat history: {e.detail}")
        history = []

    for msg in history:
        role = "user" if msg["sender"] == "student" else "assistant"
        with st.chat_message(role):
            st.write(msg["message"])

    prompt = st.chat_input("Ask your mentor a question...")
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        try:
            reply = api.send_chat_message(prompt)["reply"]
            with st.chat_message("assistant"):
                st.write(reply)
        except api.APIError as e:
            st.error(f"Couldn't get a reply: {e.detail}")


# ---------------------------------------------------------------------------
# Explore — compare careers, bookmarks, deadlines, directory
# ---------------------------------------------------------------------------

def get_all_careers() -> list:
    if st.session_state.all_careers is None:
        try:
            st.session_state.all_careers = api.get_careers()
        except api.APIError as e:
            st.error(f"Couldn't load careers: {e.detail}")
            st.session_state.all_careers = []
    return st.session_state.all_careers


def render_explore() -> None:
    title("Explore", "Compare careers, revisit saved picks, track deadlines, and browse courses & colleges.")
    compare_tab, bookmarks_tab, deadlines_tab, directory_tab = st.tabs(
        ["Compare careers", "Bookmarks", "Deadlines", "Directory"]
    )

    all_careers = get_all_careers()
    matches_by_id = {m["career_id"]: m for m in (st.session_state.score or {}).get("top_matches", [])}

    with compare_tab:
        options = {c["name"]: c["id"] for c in all_careers}
        selected_names = st.multiselect("Pick 2-3 careers to compare", list(options.keys()), max_selections=3)
        if len(selected_names) < 2:
            st.info("Pick at least 2 careers to compare.")
        else:
            selected_ids = {options[n] for n in selected_names}
            selected = [c for c in all_careers if c["id"] in selected_ids]
            cols = st.columns(len(selected))
            for col, career in zip(cols, selected):
                match = matches_by_id.get(career["id"])
                score_line = (f"<p class='accent'>{match['score']}% suitability for you</p>" if match
                              else "<p class='muted'>Not in your current top matches</p>")
                gaps = tags_html(match["skill_gaps"]) if match else "<span class='muted'>Retake the assessment to see this</span>"
                with col:
                    st.markdown(
                        f"<div class='card'><h3>{escape(career['name'])}</h3>{score_line}"
                        f"<p class='muted'>{escape(career['description'])}</p>"
                        f"<p class='muted'>Required skills:</p>{tags_html(career['required_skills'])}"
                        f"<p class='muted'>Skill gaps:</p>{gaps}"
                        f"<p class='muted'>Courses:</p>{tags_html([c['name'] for c in career['courses']])}"
                        f"<p class='muted'>Colleges:</p>{tags_html([c['name'] for c in career['colleges']])}"
                        "</div>",
                        unsafe_allow_html=True,
                    )

    with bookmarks_tab:
        try:
            bookmarked = api.get_bookmarks()
        except api.APIError as e:
            st.error(f"Couldn't load bookmarks: {e.detail}")
            bookmarked = []
        if not bookmarked:
            st.info("No bookmarks yet — star a career from your Dashboard matches to save it here.")
        else:
            cols = st.columns(min(3, len(bookmarked)))
            for i, career in enumerate(bookmarked):
                with cols[i % len(cols)]:
                    st.markdown(
                        f"<div class='career-card'><div class='career-name'>{escape(career['name'])}</div>"
                        f"<p class='muted'>{escape(career['description'])}</p></div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("Remove bookmark", key=f"unbookmark_{career['id']}", use_container_width=True):
                        try:
                            api.remove_bookmark(career["id"])
                            st.session_state.bookmark_ids = None
                            st.rerun()
                        except api.APIError as e:
                            st.error(f"Couldn't remove bookmark: {e.detail}")

    with deadlines_tab:
        st.markdown(
            "<p class='muted'>Scholarship cycles shift year to year — treat these as a starting point and "
            "confirm exact dates on the official page before applying.</p>",
            unsafe_allow_html=True,
        )
        try:
            bookmarked = api.get_bookmarks()
        except api.APIError:
            bookmarked = []
        tracked_ids = set(matches_by_id.keys()) | {c["id"] for c in bookmarked}
        tracked = [c for c in all_careers if c["id"] in tracked_ids] or all_careers

        seen = set()
        rows = []
        for career in tracked:
            for sch in career.get("scholarships", []):
                key = (sch["name"], career["id"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append((career["name"], sch))

        if not rows:
            st.info("No scholarships to show yet.")
        for career_name, sch in rows:
            st.markdown(
                f"<div class='card' style='margin-bottom:12px;'>"
                f"<h3>{escape(sch['name'])}</h3>"
                f"<p class='muted'>For: {escape(career_name)}</p>"
                f"<p>{escape(sch.get('typical_deadline') or 'No timing info available yet.')}</p>"
                f"<p class='muted'>{escape(sch.get('eligibility') or '')}</p>"
                "</div>",
                unsafe_allow_html=True,
            )

    with directory_tab:
        search = st.text_input("Search colleges or courses", key="directory_search")
        colleges_map, courses_map = {}, {}
        for career in all_careers:
            for college in career.get("colleges", []):
                entry = colleges_map.setdefault(college["name"], {"location": college.get("location"), "careers": []})
                entry["careers"].append(career["name"])
            for course in career.get("courses", []):
                entry = courses_map.setdefault(course["name"], {"level": course.get("level"), "careers": []})
                entry["careers"].append(career["name"])

        st.markdown("<h3>Colleges</h3>", unsafe_allow_html=True)
        for name, info in sorted(colleges_map.items()):
            if search and search.lower() not in name.lower():
                continue
            location = f" — {escape(info['location'])}" if info["location"] else ""
            st.markdown(
                f"<div class='card' style='margin-bottom:10px;'><strong>{escape(name)}</strong>{location}"
                f"<p class='muted' style='margin:4px 0 0;'>Relevant for: {escape(', '.join(sorted(set(info['careers']))))}</p></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<h3>Courses</h3>", unsafe_allow_html=True)
        for name, info in sorted(courses_map.items()):
            if search and search.lower() not in name.lower():
                continue
            level = f" ({escape(info['level'])})" if info["level"] else ""
            st.markdown(
                f"<div class='card' style='margin-bottom:10px;'><strong>{escape(name)}</strong>{level}"
                f"<p class='muted' style='margin:4px 0 0;'>Relevant for: {escape(', '.join(sorted(set(info['careers']))))}</p></div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Admin — manage the shared career/course/college dataset
# ---------------------------------------------------------------------------

def render_admin() -> None:
    import json

    title("Admin", "Manage the shared careers dataset — courses, colleges, scholarships, certifications.")

    try:
        careers = api.admin_list_careers()
    except api.APIError as e:
        st.error(f"Couldn't load careers: {e.detail}")
        return

    names_by_id = {c["id"]: c["name"] for c in careers}
    choice = st.selectbox("Select a career to edit, or add a new one",
                           ["+ New career"] + [f"{cid} — {name}" for cid, name in names_by_id.items()])
    editing = choice != "+ New career"
    existing = next((c for c in careers if choice.startswith(c["id"] + " —")), None) if editing else None

    with st.form("admin_career_form"):
        career_id = st.text_input("Career ID (lowercase-with-dashes, immutable once created)",
                                   value=existing["id"] if existing else "", disabled=editing)
        name = st.text_input("Name", value=existing["name"] if existing else "")
        description = st.text_area("Description", value=existing["description"] if existing else "")

        st.markdown("**RIASEC tag weights (0-10)**")
        riasec_cols = st.columns(6)
        riasec_defaults = existing["riasec_tags"] if existing else {}
        riasec_tags = {}
        for col, code in zip(riasec_cols, "RIASEC"):
            with col:
                riasec_tags[code] = st.number_input(code, min_value=0, max_value=10,
                                                      value=int(riasec_defaults.get(code, 0)), key=f"admin_riasec_{code}")

        relevant_subjects = st.multiselect("Relevant subjects", SUBJECTS,
                                            default=existing["relevant_subjects"] if existing else [])
        required_skills = st.multiselect("Required skills", SKILLS,
                                          default=existing["required_skills"] if existing else [])
        interest_tags = st.multiselect("Interest tags", INTEREST_TAGS,
                                        default=existing["interest_tags"] if existing else [])
        emerging = st.checkbox("Emerging field", value=existing["emerging"] if existing else False)

        st.markdown("**Courses / colleges / scholarships / certifications**")
        st.caption("Edit as JSON lists — e.g. courses: "
                   '[{"name": "B.Tech Computer Science", "level": "undergrad"}]')
        courses_raw = st.text_area("Courses (JSON)",
                                    value=json.dumps(existing["courses"] if existing else [], indent=2), height=100)
        colleges_raw = st.text_area("Colleges (JSON)",
                                     value=json.dumps(existing["colleges"] if existing else [], indent=2), height=100)
        scholarships_raw = st.text_area("Scholarships (JSON)",
                                         value=json.dumps(existing["scholarships"] if existing else [], indent=2), height=100)
        certifications_raw = st.text_area("Certifications (JSON)",
                                           value=json.dumps(existing["certifications"] if existing else [], indent=2), height=100)

        submitted = st.form_submit_button("Save career", use_container_width=True)

    if submitted:
        try:
            payload = {
                "id": career_id.strip() if not editing else existing["id"],
                "name": name,
                "description": description,
                "riasec_tags": riasec_tags,
                "relevant_subjects": relevant_subjects,
                "required_skills": required_skills,
                "interest_tags": interest_tags,
                "courses": json.loads(courses_raw),
                "colleges": json.loads(colleges_raw),
                "scholarships": json.loads(scholarships_raw),
                "certifications": json.loads(certifications_raw),
                "emerging": emerging,
            }
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in one of the list fields: {e}")
            return

        if not payload["id"] or not name or not description:
            st.warning("Career ID, name, and description are required.")
            return

        try:
            if editing:
                api.admin_update_career(payload["id"], payload)
                st.success(f"Updated {name}.")
            else:
                api.admin_create_career(payload)
                st.success(f"Created {name}.")
            st.session_state.all_careers = None
            st.rerun()
        except api.APIError as e:
            st.error(f"Couldn't save career: {e.detail}")

    if editing:
        st.markdown("---")
        confirm = st.checkbox(f"Confirm permanent deletion of {existing['name']}", key="admin_confirm_delete")
        if st.button("Delete career", disabled=not confirm):
            try:
                api.admin_delete_career(existing["id"])
                st.session_state.all_careers = None
                st.success(f"Deleted {existing['name']}.")
                st.rerun()
            except api.APIError as e:
                st.error(f"Couldn't delete career: {e.detail}")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

PAGES = ("Dashboard", "Assessment", "Roadmap", "Mentor", "Explore")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(BRAND_HTML,
                     unsafe_allow_html=True)

        nav_pages = ("Roadmap", "Mentor", "Explore") if st.session_state.is_admin else PAGES
        for page in nav_pages:
            active = st.session_state.nav_page == page
            if st.button(page, key=f"nav_{page}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.nav_page = page
                st.rerun()

        if st.session_state.is_admin:
            active = st.session_state.nav_page == "Admin"
            if st.button("Admin", key="nav_Admin", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.nav_page = "Admin"
                st.rerun()

        st.markdown("---")
        st.markdown(f"<p class='muted'>Signed in as</p><h3 style='margin-top:-8px'>{escape(st.session_state.name)}</h3>",
                     unsafe_allow_html=True)

        with st.expander("Change password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current password", type="password", key="current_password")
                new_password = st.text_input("New password", type="password", key="new_password_input",
                                              help="Minimum 8 characters")
                change_submitted = st.form_submit_button("Update password", use_container_width=True)
            if change_submitted:
                if not current_password or not new_password:
                    st.warning("Fill in both fields.")
                elif len(new_password) < 8:
                    st.warning("New password must be at least 8 characters.")
                else:
                    try:
                        result = api.change_password(current_password, new_password)
                        st.success(result["detail"])
                    except api.APIError as e:
                        st.error(e.detail)

        if st.button("Log out", use_container_width=True):
            logout()


def render_app() -> None:
    if st.session_state.is_admin:
        if st.session_state.nav_page in ("Dashboard", "Assessment"):
            st.session_state.nav_page = "Admin"
    elif not has_completed_profile() and st.session_state.nav_page != "Assessment":
        st.session_state.nav_page = "Assessment"

    render_sidebar()
    page = st.session_state.nav_page
    if st.session_state.is_admin:
        if page == "Admin":
            render_admin()
        elif page == "Roadmap":
            render_roadmap()
        elif page == "Mentor":
            render_mentor()
        elif page == "Explore":
            render_explore()
        else:
            render_admin()
        return

    if page == "Assessment":
        render_assessment()
    elif not has_completed_profile():
        render_assessment()
    elif page == "Dashboard":
        render_dashboard()
    elif page == "Roadmap":
        render_roadmap()
    elif page == "Mentor":
        render_mentor()
    elif page == "Explore":
        render_explore()


def main() -> None:
    init_state()
    inject_styles()
    restore_session_from_url()
    if not is_authenticated():
        render_auth()
        return
    render_app()


if __name__ == "__main__":
    main()
