"""Career AI — Streamlit frontend prototype.

This version intentionally keeps authentication and recommendations local so
the interface can be demonstrated without a database or API. Replace the
demo login and recommendation function when backend services are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

import streamlit as st


# ---------------------------------------------------------------------------
# App setup and design tokens
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Career AI", page_icon="🦋", layout="wide")


def inject_styles() -> None:
    """Load the shared dark-purple design system once per Streamlit rerun."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root { --bg:#0d0820; --panel:#1a1037; --panel2:#28194e; --line:rgba(196,165,255,.22); --muted:#c0b5d8; --violet:#9664ff; --pink:#ef5e7d; --mint:#70e1ba; }
        * { font-family:'DM Sans', sans-serif; }
        .stApp { background:radial-gradient(circle at 78% 5%, #34206c 0, #170b31 37%, var(--bg) 100%); color:#faf8ff; }
        #MainMenu, footer, header { visibility:hidden; }
        [data-testid='stAppViewContainer'] > .main { background:transparent; }
        .block-container { max-width:1400px; padding-top:2.2rem; padding-bottom:3rem; }
        [data-testid='stSidebar'] { background:#0b061c; border-right:1px solid var(--line); }
        [data-testid='stSidebar'] * { color:#eeeaff !important; }
        [data-testid='stSidebar'] .stRadio label { border-radius:10px; padding:6px 4px; }
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
        .career-card { background:linear-gradient(145deg,rgba(38,24,76,.94),rgba(18,11,44,.96)); border:1px solid var(--line); border-radius:18px; padding:20px; min-height:205px; }.career-icon{font-size:2rem;}.career-name{font-size:1.08rem;font-weight:700;color:#fff;margin:8px 0;}.score-badge{float:right;background:rgba(102,222,181,.14);color:var(--mint);padding:5px 9px;border-radius:9px;font-size:.8rem;font-weight:700;}
        .ai-card { background:linear-gradient(135deg,rgba(122,67,199,.43),rgba(207,72,131,.18)); border:1px solid rgba(238,126,193,.34); border-radius:20px; padding:22px; }.ai-card h3{margin:0 0 8px;}.ai-card p{color:#e4dafa;}
        .row { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:11px 0; border-top:1px solid rgba(195,162,255,.16); color:#e9e0ff; }.row:first-of-type{border-top:0;}
        .tag { display:inline-block; border-radius:999px; padding:5px 10px; background:rgba(151,100,255,.15); color:#d6c1ff; font-size:.82rem; margin:4px 5px 0 0; }
        .roadmap-step { display:flex; gap:12px; align-items:flex-start; border-left:2px solid rgba(169,126,255,.36); padding:0 0 16px 15px; margin-left:8px; }.roadmap-step:last-child{padding-bottom:0;}.done-dot,.next-dot{margin-left:-23px;width:14px;height:14px;border-radius:50%;flex:0 0 14px;margin-top:4px;}.done-dot{background:var(--mint);box-shadow:0 0 0 4px rgba(112,225,186,.12);}.next-dot{background:#9a65ff;box-shadow:0 0 0 4px rgba(154,101,255,.16);}
        .login-panel { background:rgba(16,9,38,.75); border:1px solid var(--line); border-radius:30px; padding:44px; box-shadow:0 25px 70px rgba(0,0,0,.35); }.login-title { font-family:'Space Grotesk', sans-serif; font-size:2.7rem; line-height:1.05; margin:0 0 10px; color:#fff; letter-spacing:-1.6px; }.login-subtitle{color:#c5aaf8;font-size:1.1rem;margin-bottom:20px;}
        .career-visual { min-height:650px; position:relative; display:flex; align-items:center; justify-content:center; overflow:hidden; }.orb{position:absolute;width:510px;height:510px;border:1px dashed rgba(180,132,255,.32);border-radius:50%;}.career-quote{z-index:2;max-width:420px;text-align:center;font-family:'Space Grotesk',sans-serif;color:#fff;font-size:3rem;font-weight:700;line-height:1.04;letter-spacing:-2px;}.career-quote span{color:#f56880;}.float{position:absolute;z-index:3;display:grid;place-items:center;width:100px;height:100px;background:linear-gradient(145deg,rgba(116,69,205,.48),rgba(26,15,64,.42));border:1px solid rgba(221,187,255,.3);border-radius:28px;font-size:3.5rem;box-shadow:0 14px 36px rgba(3,0,14,.35);animation:drift 4s ease-in-out infinite;}.one{top:55px;left:15%;}.two{top:55px;right:15%;animation-delay:-1s}.three{top:245px;left:2%;animation-delay:-2s}.four{top:245px;right:1%;animation-delay:-.5s}.five{bottom:52px;left:17%;animation-delay:-2.5s}.six{bottom:52px;right:17%;animation-delay:-1.5s}@keyframes drift{50%{transform:translateY(-13px) rotate(3deg)}}
        div[data-baseweb='input']>div, div[data-baseweb='select']>div { background:rgba(16,10,39,.8)!important; border-color:rgba(188,148,255,.42)!important; color:#fff!important; }input{color:#fff!important;} .stButton>button,button[kind='primary'] { background:linear-gradient(90deg,#7c3cff,#ef5978); color:#fff; border:0; border-radius:11px; font-weight:700; min-height:43px; }.stButton>button:hover{border:0;filter:brightness(1.1);}.stProgress>div>div>div{background:linear-gradient(90deg,#7c3cff,#ef5978);}
        @media(max-width:900px){.block-container{padding:1rem;}.login-panel{padding:30px 22px;}.login-title{font-size:2.25rem;}.career-visual{min-height:420px;}.career-quote{font-size:2.25rem;}.float{width:72px;height:72px;font-size:2.4rem;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Career recommendation data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Career:
    icon: str
    interests: tuple[str, ...]
    hobbies: tuple[str, ...]
    subjects: tuple[str, ...]
    skills: tuple[str, ...]
    description: str
    courses: tuple[str, ...]


CAREERS: dict[str, Career] = {
    "AI Engineer": Career("🤖", ("Technology", "AI & Robotics", "Science", "Mathematics"), ("Coding", "Research", "Gaming"), ("Mathematics", "Physics", "Computer Science"), ("Problem Solving", "Logical Thinking", "Programming"), "Build intelligent systems that solve real-world problems.", ("B.Tech Artificial Intelligence", "B.Tech Computer Science")),
    "Software Engineer": Career("💻", ("Technology", "Mathematics", "AI & Robotics"), ("Coding", "Gaming", "Research"), ("Mathematics", "Computer Science", "Physics"), ("Problem Solving", "Programming", "Logical Thinking"), "Design and build the apps and systems people use every day.", ("B.Tech Computer Science", "BCA")),
    "Data Scientist": Career("📊", ("Technology", "Mathematics", "Science", "Business"), ("Coding", "Research", "Reading"), ("Mathematics", "Computer Science", "Economics"), ("Mathematics", "Problem Solving", "Research"), "Turn data into useful insights and better decisions.", ("B.Tech Data Science", "B.Sc Mathematics")),
    "Robotics Engineer": Career("🦾", ("Technology", "AI & Robotics", "Science"), ("Coding", "Gaming", "Research"), ("Physics", "Mathematics", "Computer Science"), ("Problem Solving", "Logical Thinking", "Creativity"), "Create machines that sense, move and assist people.", ("B.Tech Robotics", "B.Tech Mechatronics")),
    "UX Designer": Career("🎨", ("Design", "Technology"), ("Drawing", "Writing", "Gaming"), ("Computer Science", "English", "Art"), ("Creativity", "Communication", "Problem Solving"), "Make digital products intuitive, useful and enjoyable.", ("B.Des Interaction Design", "B.Des UX Design")),
    "Business Analyst": Career("📈", ("Business", "Technology", "Mathematics"), ("Reading", "Research", "Writing"), ("Mathematics", "Economics", "Business Studies"), ("Communication", "Problem Solving", "Logical Thinking"), "Use research and data to improve how organisations work.", ("BBA Business Analytics", "B.Com Business Analytics")),
    "Doctor": Career("🩺", ("Medicine", "Science"), ("Reading", "Research"), ("Biology", "Chemistry"), ("Communication", "Research", "Problem Solving"), "Diagnose, treat and support patients' health.", ("MBBS", "B.Sc Nursing")),
    "Environmental Scientist": Career("🌱", ("Environment", "Science"), ("Research", "Reading"), ("Biology", "Chemistry", "Geography"), ("Research", "Problem Solving", "Communication"), "Protect ecosystems through science and sustainable solutions.", ("B.Sc Environmental Science", "B.Tech Environmental Engineering")),
}

UNIVERSITIES = (
    ("IIT Bombay", "Engineering, design and technology", 94),
    ("NID Ahmedabad", "Design and creative disciplines", 91),
    ("Ashoka University", "Liberal arts and sciences", 88),
)

SCHOLARSHIPS = (
    ("Future Leaders Scholarship", "Up to ₹5,00,000", "Merit and leadership"),
    ("Women in Tech Scholarship", "Up to ₹3,00,000", "Women pursuing technology"),
    ("Merit Excellence Award", "Up to ₹2,50,000", "Strong academic performance"),
)


# ---------------------------------------------------------------------------
# Session and utility functions
# ---------------------------------------------------------------------------


def init_state() -> None:
    defaults: dict[str, Any] = {
        "authenticated": False,
        "login_name": "",
        "profile": None,
        "nav_page": "Dashboard",
        "mentor_answer": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def calculate_matches(profile: dict[str, Any]) -> dict[str, int]:
    """Score careers against the selected profile fields (demo recommender)."""
    weights = {"interests": 25, "hobbies": 15, "subjects": 20, "skills": 20}
    scores: dict[str, int] = {}
    for name, career in CAREERS.items():
        score = 0
        for field, weight in weights.items():
            selected = set(profile.get(field, []))
            matched = selected.intersection(getattr(career, field))
            score += len(matched) * weight
        scores[name] = min(score, 99)
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


def go_to(page: str) -> None:
    st.session_state.nav_page = page


def reset_app() -> None:
    for key in ("authenticated", "login_name", "profile", "nav_page", "mentor_answer"):
        st.session_state.pop(key, None)
    st.rerun()


def title(text: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero-title'>{escape(text)}</div><div class='hero-subtitle'>{escape(subtitle)}</div>", unsafe_allow_html=True)


def tags(items: list[str]) -> str:
    return "".join(f"<span class='tag'>{escape(item)}</span>" for item in items) or "<span class='muted'>Not added yet</span>"


# ---------------------------------------------------------------------------
# Entry screens
# ---------------------------------------------------------------------------


def render_login() -> None:
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        st.markdown("""
        <div class='login-panel'>
          <div class='brand'><div class='brand-mark'>🦋</div><div class='brand-name'>Career <span>AI</span></div></div>
          <h1 class='login-title'>Welcome back</h1>
          <div class='login-subtitle'>Your future is waiting.</div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username or email", placeholder="Enter your username or email")
            password = st.text_input("Password", placeholder="Enter your password", type="password")
            st.checkbox("Remember me", help="Demo-only setting; no credentials are stored.")
            submitted = st.form_submit_button("Sign in  →", use_container_width=True)
        st.markdown("<p class='muted' style='font-size:.82rem;margin-top:14px;'>Demo mode: use any non-empty username and password.</p><p style='text-align:center;margin-top:28px;' class='muted'>New to Career AI? <span class='accent'>Create an account</span></p></div>", unsafe_allow_html=True)
        if submitted:
            if username.strip() and password:
                st.session_state.authenticated = True
                st.session_state.login_name = username.split("@")[0].strip().title()
                st.rerun()
            st.warning("Please enter both a username and password.")
    with right:
        st.markdown("""
        <div class='career-visual'>
          <div class='orb'></div><div class='float one'>🩺</div><div class='float two'>💻</div>
          <div class='float three'>🏏</div><div class='float four'>🎓</div>
          <div class='float five'>🎨</div><div class='float six'>🔬</div>
          <div class='career-quote'>Every interest<br>can become a <span>future.</span></div>
        </div>
        """, unsafe_allow_html=True)


def render_assessment() -> None:
    title("Let’s get to know you", "Your answers help Career AI recommend paths that fit you.")
    st.markdown("<div class='card'><h3>🧭 Career assessment</h3><p class='muted'>Choose the subjects, interests and strengths that genuinely describe you. You can update them later.</p></div>", unsafe_allow_html=True)
    with st.form("assessment_form"):
        name = st.text_input("Your name", value=st.session_state.login_name, placeholder="Enter your name")
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("Current grade", ["11", "12", "Undergraduate", "Other"])
            subjects = st.multiselect("Subjects you enjoy", ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Economics", "Business Studies", "English", "Geography", "Art"])
            hobbies = st.multiselect("Hobbies and activities", ["Coding", "Reading", "Sports", "Drawing", "Gaming", "Writing", "Music", "Research"])
        with col2:
            interests = st.multiselect("Interests", ["Technology", "Science", "Mathematics", "Business", "Design", "Medicine", "Law", "Environment", "AI & Robotics"])
            skills = st.multiselect("Your strengths", ["Problem Solving", "Logical Thinking", "Creativity", "Communication", "Mathematics", "Programming", "Research", "Leadership"])
            report_card = st.file_uploader("Upload report card (optional)", type=["pdf", "png", "jpg", "jpeg"])
        work_style = st.radio("The work that sounds most interesting", ["Solving technical problems", "Creating and designing things", "Helping people", "Research and discovering new things", "Business and management"], horizontal=False)
        submitted = st.form_submit_button("Discover my career matches  →", use_container_width=True)
    if submitted:
        if not name.strip() or not subjects or not interests:
            st.warning("Add your name, at least one subject, and at least one interest to continue.")
            return
        st.session_state.profile = {
            "name": name.strip().title(), "grade": grade, "subjects": subjects, "interests": interests,
            "hobbies": hobbies, "skills": skills, "work_style": work_style,
            "report_card": report_card.name if report_card else None,
        }
        st.session_state.nav_page = "Dashboard"
        st.rerun()


# ---------------------------------------------------------------------------
# App navigation and pages
# ---------------------------------------------------------------------------


PAGES = ("Dashboard", "My Profile", "Explore Careers", "Courses", "Universities", "Scholarships", "Skill Roadmap", "AI Mentor")
PAGE_ICONS = {"Dashboard": "⌂", "My Profile": "♙", "Explore Careers": "⌕", "Courses": "▣", "Universities": "♜", "Scholarships": "✦", "Skill Roadmap": "↗", "AI Mentor": "✧"}


def render_sidebar(profile: dict[str, Any]) -> str:
    with st.sidebar:
        st.markdown("<div class='brand'><div class='brand-mark'>🦋</div><div class='brand-name'>Career <span>AI</span></div></div>", unsafe_allow_html=True)
        choices = [f"{PAGE_ICONS[p]}  {p}" for p in PAGES]
        selected_label = st.radio("Navigation", choices, index=PAGES.index(st.session_state.nav_page), label_visibility="collapsed")
        selected_page = selected_label[3:]
        st.session_state.nav_page = selected_page
        st.markdown("---")
        st.markdown(f"<p class='muted'>Signed in as</p><h3 style='margin-top:-8px'>{escape(profile['name'])}</h3>", unsafe_allow_html=True)
        if st.button("Log out", use_container_width=True):
            reset_app()
    return selected_page


def render_dashboard(profile: dict[str, Any], matches: dict[str, int]) -> None:
    top_name, top_score = next(iter(matches.items()))
    title(f"Good morning, {profile['name']}! 👋", "Let’s build your future, one step at a time.")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='card'><h3>🎯 Career suitability score</h3><div class='metric'>{top_score}%</div><p class='muted'>Top match: <span class='accent'>{escape(top_name)}</span></p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='card'><h3>📚 Academic stage</h3><div class='metric metric-small'>Class {escape(profile['grade'])}</div><p class='muted'>{len(profile['subjects'])} favourite subject(s) added</p></div>", unsafe_allow_html=True)
    with m3:
        progress = min(25 + len(profile['skills']) * 8 + len(profile['interests']) * 7, 90)
        st.markdown(f"<div class='card'><h3>↗ Career preparation</h3><div class='metric'>{progress}%</div><p class='muted'>Keep completing your roadmap.</p></div>", unsafe_allow_html=True)

    st.markdown("<h2>Top career matches</h2>", unsafe_allow_html=True)
    career_columns = st.columns(3)
    for column, (name, score) in zip(career_columns, list(matches.items())[:3]):
        career = CAREERS[name]
        with column:
            st.markdown(f"<div class='career-card'><span class='score-badge'>{score}% match</span><div class='career-icon'>{career.icon}</div><div class='career-name'>{escape(name)}</div><p class='muted'>{escape(career.description)}</p><p class='accent'>Explore career →</p></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown("""<div class='card'><h3>🎓 Top universities for you</h3>
        <div class='row'><span>IIT Bombay</span><span class='mint'>Match 94%</span></div>
        <div class='row'><span>NID Ahmedabad</span><span class='mint'>Match 91%</span></div>
        <div class='row'><span>Ashoka University</span><span class='mint'>Match 88%</span></div></div>""", unsafe_allow_html=True)
        st.button("Browse universities", key="browse_universities", use_container_width=True, on_click=go_to, args=("Universities",))
    with right:
        st.markdown(f"<div class='ai-card'><h3>✦ Ask your AI Mentor</h3><p>Hi {escape(profile['name'])}, your strong match with <b>{escape(top_name)}</b> comes from your selected interests and strengths. Ask what to learn next.</p></div>", unsafe_allow_html=True)
        st.button("Start a conversation", key="start_mentor", use_container_width=True, on_click=go_to, args=("AI Mentor",))


def render_profile(profile: dict[str, Any]) -> None:
    title("My profile", "This is the information currently guiding your recommendations.")
    st.markdown(f"<div class='card'><h3>👤 {escape(profile['name'])}</h3><p class='muted'>Grade: {escape(profile['grade'])} · Preferred style: {escape(profile['work_style'])}</p><p class='muted'>Report card: {escape(profile['report_card'] or 'Not uploaded')}</p></div>", unsafe_allow_html=True)
    columns = st.columns(2)
    groups = (("📚 Favourite subjects", profile["subjects"]), ("💡 Interests", profile["interests"]), ("🌟 Hobbies", profile["hobbies"]), ("🧠 Strengths", profile["skills"]))
    for index, (heading, items) in enumerate(groups):
        with columns[index % 2]:
            st.markdown(f"<div class='card'><h3>{heading}</h3>{tags(items)}</div>", unsafe_allow_html=True)
    if st.button("Retake assessment"):
        st.session_state.profile = None
        st.rerun()


def render_careers(matches: dict[str, int]) -> None:
    title("Explore careers", "Compare career paths that connect with your profile.")
    for name, score in matches.items():
        career = CAREERS[name]
        with st.expander(f"{career.icon}  {name}  ·  {score}% match"):
            st.write(career.description)
            st.markdown("**Recommended courses**")
            st.write(" · ".join(career.courses))
            st.markdown("**Skills to build**")
            st.write(" · ".join(career.skills))


def render_courses(matches: dict[str, int]) -> None:
    title("Recommended courses", "Course ideas based on your strongest current career matches.")
    shown: set[str] = set()
    for name in list(matches)[:4]:
        for course in CAREERS[name].courses:
            shown.add(course)
    for course in sorted(shown):
        st.markdown(f"<div class='card'><h3>📚 {escape(course)}</h3><p class='muted'>A relevant option for one or more of your recommended career paths.</p></div>", unsafe_allow_html=True)


def render_universities() -> None:
    title("Universities", "Explore institutions that could fit your career direction.")
    for name, focus, match in UNIVERSITIES:
        st.markdown(f"<div class='card'><span class='score-badge'>{match}% fit</span><h3>🎓 {escape(name)}</h3><p class='muted'>{escape(focus)}</p><p class='accent'>Explore programmes and admissions →</p></div>", unsafe_allow_html=True)


def render_scholarships() -> None:
    title("Scholarships and aid", "A starting list of opportunities to research carefully before applying.")
    for name, amount, eligibility in SCHOLARSHIPS:
        st.markdown(f"<div class='card'><h3>✦ {escape(name)}</h3><p class='mint'>{escape(amount)}</p><p class='muted'>{escape(eligibility)}</p></div>", unsafe_allow_html=True)


def render_roadmap(profile: dict[str, Any], matches: dict[str, int]) -> None:
    top_name = next(iter(matches))
    title("Your learning roadmap", f"A practical starting plan for exploring {top_name}.")
    steps = (("Self-discovery", "Completed — your profile is ready.", True), ("Career exploration", "Compare your top three career matches.", True), ("Skill building", "Choose one foundational course or project.", False), ("Real-world preparation", "Look for a club, competition or internship.", False), ("University planning", "Shortlist universities and scholarships.", False))
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for heading, description, complete in steps:
        dot = "done-dot" if complete else "next-dot"
        state = "Completed" if complete else "Next step"
        st.markdown(f"<div class='roadmap-step'><div class='{dot}'></div><div><b>{escape(heading)}</b><br><span class='muted'>{escape(description)} · {state}</span></div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_mentor(profile: dict[str, Any], matches: dict[str, int]) -> None:
    top_name, top_score = next(iter(matches.items()))
    title("AI Mentor", "Ask for a simple, personalised next step.")
    st.markdown("<div class='ai-card'><h3>✦ Your personal Career AI mentor</h3><p>I use your profile to provide demo recommendations. Connect this page to an LLM API when your backend is ready.</p></div>", unsafe_allow_html=True)
    with st.form("mentor_form", clear_on_submit=True):
        question = st.text_input("What would you like to know?", placeholder="For example: What should I learn for my top career match?")
        asked = st.form_submit_button("Ask mentor  →", use_container_width=True)
    if asked:
        if not question.strip():
            st.warning("Type a question first.")
        else:
            st.session_state.mentor_answer = (
                f"Based on your profile, {top_name} is your strongest current match ({top_score}%). "
                f"Start by strengthening {CAREERS[top_name].skills[0].lower()} and explore {CAREERS[top_name].courses[0]}. "
                "Compare a few paths before making a final choice."
            )
    if st.session_state.mentor_answer:
        st.markdown(f"<div class='card'><h3>Career AI says</h3><p>{escape(st.session_state.mentor_answer)}</p></div>", unsafe_allow_html=True)


def render_app() -> None:
    profile = st.session_state.profile
    if profile is None:
        render_assessment()
        return
    matches = calculate_matches(profile)
    page = render_sidebar(profile)
    renderers = {
        "Dashboard": lambda: render_dashboard(profile, matches),
        "My Profile": lambda: render_profile(profile),
        "Explore Careers": lambda: render_careers(matches),
        "Courses": lambda: render_courses(matches),
        "Universities": render_universities,
        "Scholarships": render_scholarships,
        "Skill Roadmap": lambda: render_roadmap(profile, matches),
        "AI Mentor": lambda: render_mentor(profile, matches),
    }
    renderers[page]()


def main() -> None:
    inject_styles()
    init_state()
    if not st.session_state.authenticated:
        render_login()
        return
    render_app()


if __name__ == "__main__":
    main()
