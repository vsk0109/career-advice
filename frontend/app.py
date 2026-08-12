"""
Career AI — Streamlit frontend for the AI-Powered Career Mentor backend.

Talks to the FastAPI backend (api_client.py) over HTTP with JWT auth.
Session state holds the token and cached responses; nothing here talks to
MySQL or the LLM directly.
"""

from html import escape

import streamlit as st

import api_client as api

st.set_page_config(page_title="Career AI", page_icon="🦋", layout="wide")


# ---------------------------------------------------------------------------
# Design system — dark violet theme
# ---------------------------------------------------------------------------

def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root { --bg:#0d0820; --panel:#1a1037; --panel2:#28194e; --line:rgba(196,165,255,.22); --muted:#c0b5d8; --violet:#9664ff; --pink:#ef5e7d; --mint:#70e1ba; }
        * { font-family:'DM Sans', sans-serif; }
        .stApp { background:radial-gradient(circle at 78% 5%, #34206c 0, #170b31 37%, var(--bg) 100%); color:#faf8ff; }
        #MainMenu, footer { visibility:hidden; }
        header { background:transparent; }
        [data-testid='stHeader'] { background:transparent; }
        [data-testid='stAppViewContainer'] > .main { background:transparent; }
        .block-container { max-width:1400px; padding-top:2.2rem; padding-bottom:3rem; }
        [data-testid='stSidebar'] { background:#0b061c; border-right:1px solid var(--line); }
        [data-testid='stSidebar'] * { color:#eeeaff !important; }
        h1,h2,h3 { font-family:'Space Grotesk', sans-serif; color:#fff; letter-spacing:-.6px; }
        label,p,li { color:#eeeaff; }
        .hero-title { font-family:'Space Grotesk', sans-serif; color:#fff; font-size:2.55rem; font-weight:700; letter-spacing:-1.6px; margin:0 0 5px; }
        .hero-subtitle { color:var(--muted); font-size:1.05rem; margin:0 0 26px; }
        .brand { display:flex; align-items:center; gap:11px; margin:8px 0 23px; }
        .brand-mark { display:grid; place-items:center; width:42px; height:42px; border-radius:14px; background:linear-gradient(135deg,#de3e66,#7947ed); box-shadow:0 10px 25px rgba(216,61,143,.3); font-size:25px; }
        .brand-name { font-family:'Space Grotesk', sans-serif; font-size:1.45rem; font-weight:700; color:#fff; }.brand-name span{color:#f2617c;}
        .card { background:linear-gradient(145deg,rgba(43,27,84,.94),rgba(20,12,48,.94)); border:1px solid var(--line); border-radius:20px; padding:22px; box-shadow:0 17px 42px rgba(0,0,0,.22); height:100%; }
        .card h3 { font-size:1.08rem; margin:0 0 8px; }.muted{color:var(--muted)!important;}.accent{color:#c8aeff;}.mint{color:var(--mint);font-weight:700;}
        .metric { font-family:'Space Grotesk', sans-serif; color:#fff; font-size:2.6rem; font-weight:700; margin:12px 0 3px; }.metric-small{font-size:1.85rem;}
        .career-card { background:linear-gradient(145deg,rgba(38,24,76,.94),rgba(18,11,44,.96)); border:1px solid var(--line); border-radius:18px; padding:20px; min-height:205px; }.career-name{font-size:1.08rem;font-weight:700;color:#fff;margin:8px 0;}.score-badge{float:right;background:rgba(102,222,181,.14);color:var(--mint);padding:5px 9px;border-radius:9px;font-size:.8rem;font-weight:700;}
        .ai-card { background:linear-gradient(135deg,rgba(122,67,199,.43),rgba(207,72,131,.18)); border:1px solid rgba(238,126,193,.34); border-radius:20px; padding:22px; }.ai-card h3{margin:0 0 8px;}.ai-card p{color:#e4dafa;}
        .tag { display:inline-block; border-radius:999px; padding:5px 10px; background:rgba(151,100,255,.15); color:#d6c1ff; font-size:.82rem; margin:4px 5px 0 0; }
        .roadmap-step { display:flex; gap:12px; align-items:flex-start; border-left:2px solid rgba(169,126,255,.36); padding:0 0 16px 15px; margin-left:8px; }.roadmap-step:last-child{padding-bottom:0;}
        .login-panel { background:rgba(16,9,38,.75); border:1px solid var(--line); border-radius:30px; padding:44px; box-shadow:0 25px 70px rgba(0,0,0,.35); }.login-title { font-family:'Space Grotesk', sans-serif; font-size:2.5rem; line-height:1.05; margin:0 0 10px; color:#fff; letter-spacing:-1.6px; }.login-subtitle{color:#c5aaf8;font-size:1.05rem;margin-bottom:20px;}
        div[data-baseweb='input']>div, div[data-baseweb='select']>div { background:rgba(16,10,39,.8)!important; border-color:rgba(188,148,255,.42)!important; color:#fff!important; }input{color:#fff!important;}
        .stButton>button,button[kind='primary'] { background:linear-gradient(90deg,#7c3cff,#ef5978); color:#fff; border:0; border-radius:11px; font-weight:700; min-height:43px; }
        .stButton>button:hover{border:0;filter:brightness(1.1);}
        .stProgress>div>div>div{background:linear-gradient(90deg,#7c3cff,#ef5978);}
        [data-testid="stChatMessage"] { background:rgba(28,17,58,.7); border:1px solid var(--line); border-radius:16px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def title(text: str, subtitle: str) -> None:
    st.markdown(
        f"<div class='hero-title'>{escape(text)}</div><div class='hero-subtitle'>{escape(subtitle)}</div>",
        unsafe_allow_html=True,
    )


def tags_html(items: list[str]) -> str:
    return "".join(f"<span class='tag'>{escape(str(item))}</span>" for item in items) or "<span class='muted'>None yet</span>"


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
        "access_token": None, "student_id": None, "name": None, "email": None,
        "nav_page": "Dashboard", "profile": None, "score": None, "insights": None,
        "insights_checked": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def is_authenticated() -> bool:
    return st.session_state.access_token is not None


def has_completed_profile() -> bool:
    profile = st.session_state.profile
    return bool(profile and profile.get("riasec_scores"))


def logout() -> None:
    for key in ("access_token", "student_id", "name", "email", "profile", "score", "insights", "insights_checked"):
        st.session_state.pop(key, None)
    st.rerun()


def refresh_profile() -> None:
    try:
        st.session_state.profile = api.get_profile()
    except api.APIError as e:
        st.error(f"Couldn't load your profile: {e.detail}")


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------

def render_auth() -> None:
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        st.markdown(
            "<div class='login-panel'>"
            "<div class='brand'><div class='brand-mark'>🦋</div><div class='brand-name'>Career <span>AI</span></div></div>"
            "<h1 class='login-title'>Find your path</h1>"
            "<div class='login-subtitle'>Personalized career guidance, backed by your own profile.</div>",
            unsafe_allow_html=True,
        )

        login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in →", use_container_width=True)
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
                submitted = st.form_submit_button("Create account →", use_container_width=True)
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

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            "<div class='card' style='min-height:520px;display:flex;flex-direction:column;justify-content:center;text-align:center;'>"
            "<h2 style='font-size:2.4rem;'>Every interest can<br>become a <span class='accent'>future.</span></h2>"
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
    refresh_profile()


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
        st.markdown("<div class='card'><h3>🧭 Personality (RIASEC)</h3>"
                     "<p class='muted'>Rate how much each statement sounds like you, 1 (not at all) to 5 (very much).</p></div>",
                     unsafe_allow_html=True)
        riasec_answers = []
        cols = st.columns(2)
        for i, (statement, _dim) in enumerate(RIASEC_QUESTIONS):
            default = saved_answers[i] if i < len(saved_answers) else 3
            with cols[i % 2]:
                riasec_answers.append(st.slider(statement, 1, 5, default, key=f"riasec_{i}"))

        st.markdown("<div class='card'><h3>📚 Academics</h3>"
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

        st.markdown("<div class='card'><h3>🛠 Self-rated skills</h3>"
                     "<p class='muted'>Rate skills you actually have, 1-5 — leave others at 0 to skip.</p></div>",
                     unsafe_allow_html=True)
        self_rated_skills = {}
        cols = st.columns(4)
        for i, skill in enumerate(SKILLS):
            with cols[i % 4]:
                level = st.slider(skill, 0, 5, int(saved_skills.get(skill, 0)), key=f"skill_{skill}")
                if level > 0:
                    self_rated_skills[skill] = level

        st.markdown("<div class='card'><h3>💡 Interests &amp; hobbies</h3></div>", unsafe_allow_html=True)
        interests = st.multiselect("Interests", INTEREST_TAGS, default=profile.get("interests") or [], key="interests")
        hobbies_default = ", ".join(profile.get("hobbies") or [])
        hobbies_raw = st.text_input("Hobbies (comma-separated)", value=hobbies_default,
                                     placeholder="e.g. reading, chess, painting", key="hobbies")
        hobbies = [h.strip() for h in hobbies_raw.split(",") if h.strip()]

        submitted = st.form_submit_button("Save and see my matches →", use_container_width=True)

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
    title(f"Good to see you, {profile['name']}! 👋", "Here's where your profile points you.")

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
        st.markdown(f"<div class='card'><h3>🎯 Top match</h3><div class='metric metric-small'>{escape(top['career'])}</div>"
                     f"<p class='mint'>{top['score']}% suitability</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='card'><h3>🧭 RIASEC match</h3><div class='metric'>{top['riasec_match']}%</div>"
                     f"<p class='muted'>Personality fit for {escape(top['career'])}</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='card'><h3>📚 Academic fit</h3><div class='metric'>{top['academic_fit']}%</div>"
                     f"<p class='muted'>Based on your entered marks</p></div>", unsafe_allow_html=True)

    st.markdown("<h2>Your RIASEC profile</h2>", unsafe_allow_html=True)
    st.bar_chart(profile["riasec_scores"])

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
        if st.button("Get AI explanations + roadmap →"):
            try:
                st.session_state.insights = api.get_insights(matches)
                st.rerun()
            except api.APIError as e:
                st.error(f"Couldn't generate insights: {e.detail}")
    else:
        insights = st.session_state.insights
        for career, explanation in insights["explanations"].items():
            st.markdown(
                f"<div class='ai-card'><h3>✦ {escape(career)}</h3><p>{escape(explanation)}</p></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div class='card'><h3>📈 Emerging trend</h3><p class='muted'>{escape(insights['emerging_trend'])}</p></div>",
            unsafe_allow_html=True,
        )
        st.info("A roadmap for your top match has been saved — see the Roadmap page to track progress.")

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
    title("AI Mentor", "Ask anything about your career matches.")
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
# Navigation
# ---------------------------------------------------------------------------

PAGES = ("Dashboard", "Assessment", "Roadmap", "Mentor")
PAGE_ICONS = {"Dashboard": "⌂", "Assessment": "🧭", "Roadmap": "↗", "Mentor": "✧"}


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("<div class='brand'><div class='brand-mark'>🦋</div><div class='brand-name'>Career <span>AI</span></div></div>",
                     unsafe_allow_html=True)
        choices = [f"{PAGE_ICONS[p]}  {p}" for p in PAGES]
        selected_label = st.radio("Navigation", choices, index=PAGES.index(st.session_state.nav_page), label_visibility="collapsed")
        selected_page = selected_label[3:]
        st.session_state.nav_page = selected_page
        st.markdown("---")
        st.markdown(f"<p class='muted'>Signed in as</p><h3 style='margin-top:-8px'>{escape(st.session_state.name)}</h3>",
                     unsafe_allow_html=True)
        if st.button("Log out", use_container_width=True):
            logout()
    return selected_page


def render_app() -> None:
    if not has_completed_profile() and st.session_state.nav_page != "Assessment":
        st.session_state.nav_page = "Assessment"

    page = render_sidebar()
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


def main() -> None:
    inject_styles()
    init_state()
    if not is_authenticated():
        render_auth()
        return
    render_app()


if __name__ == "__main__":
    main()
