"""Career AI — Streamlit career discovery interface."""

import streamlit as st
from html import escape


LOGO_PATH = "assets/career-ai-logo-cropped.png"
st.set_page_config(
    page_title="Career AI",
    page_icon=LOGO_PATH,
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = (
    "Dashboard",
    "Explore Careers",
    "Skill Roadmap",
    "Scholarships",
    "Universities",
    "Profile",
    "AI Mentor",
)
PAGE_ICONS = {
    "Dashboard": "⌂",
    "Explore Careers": "⌕",
    "Skill Roadmap": "↗",
    "Scholarships": "✦",
    "Universities": "♜",
    "Profile": "♙",
    "AI Mentor": "✧",
}

THEMES = {
    "Dark": {
        "app_bg": "radial-gradient(circle at 70% 2%, #34206c 0, #170b31 38%, #0d0820 100%)",
        "text": "#fbfaff",
        "muted": "#bdb4d4",
        "card": "linear-gradient(145deg, rgba(37,24,76,.96), rgba(16,10,42,.96))",
        "card_soft": "rgba(35, 23, 71, .84)",
        "line": "rgba(190, 156, 255, .22)",
        "sidebar": "#0d0824",
        "input": "rgba(13, 8, 32, .78)",
        "shadow": "rgba(0, 0, 0, .27)",
        "score": "linear-gradient(135deg, #4d26c5, #1e4eaa)",
        "mentor": "linear-gradient(145deg, rgba(69, 29, 93, .86), rgba(18, 11, 45, .96))",
    },
    "Light": {
        "app_bg": "radial-gradient(circle at 72% 5%, #ffffff 0, #f0edff 43%, #e5e0ff 100%)",
        "text": "#28184d",
        "muted": "#71628d",
        "card": "linear-gradient(145deg, rgba(255,255,255,.98), rgba(248,246,255,.98))",
        "card_soft": "rgba(255,255,255,.9)",
        "line": "rgba(124, 58, 237, .20)",
        "sidebar": "#201153",
        "input": "#ffffff",
        "shadow": "rgba(67, 37, 128, .12)",
        "score": "linear-gradient(135deg, #7542df, #5e94ef)",
        "mentor": "linear-gradient(145deg, #ffffff, #f8f5ff)",
    },
}


def init_state() -> None:
    st.session_state.setdefault("app_stage", "login")
    if st.session_state.app_stage == "results":
        st.session_state.app_stage = "dashboard"
    st.session_state.setdefault("nav_page", "Dashboard")
    st.session_state.setdefault("light_mode", False)
    st.session_state.setdefault("student_name", "")
    st.session_state.setdefault("mentor_history", [])


def profile_name() -> str:
    return st.session_state.student_name or "Student"


def career_matches() -> tuple[str, ...]:
    return ("UX Designer", "Data Analyst", "Clinical Psychologist")


def dashboard_progress() -> int:
    """Static display value for the frontend-only dashboard."""
    return 60


def current_theme() -> str:
    return "Light" if st.session_state.light_mode else "Dark"


CAREER_KEYWORDS = (
    "career", "job", "profession", "future", "course", "degree", "college", "university",
    "scholarship", "financial aid", "skill", "certificate", "certification", "internship",
    "resume", "cv", "interview", "study", "subject", "stream", "engineering", "designer",
    "design", "data", "doctor", "psychology", "business", "salary", "placement", "12th",
    "school", "roadmap", "learn", "education",
)


def mentor_reply(question: str) -> str:
    """Return a concise, career-only reply without calling an external AI API."""
    question_lower = question.lower()
    if not any(keyword in question_lower for keyword in CAREER_KEYWORDS):
        return (
            "I’m here specifically to help with career and education guidance. "
            "Please ask me about careers, skills, courses, universities, scholarships, or internships."
        )
    if any(word in question_lower for word in ("university", "college", "admission")):
        return "Start by shortlisting universities based on your preferred course, entry requirements, location, fees, and scholarships. Compare at least three options before deciding."
    if any(word in question_lower for word in ("skill", "learn", "certificate", "certification")):
        return "Choose one skill connected to your target career, learn the basics through a structured course, then create a small project to show what you can do."
    if any(word in question_lower for word in ("scholarship", "financial aid", "fees")):
        return "Look for merit, need-based, and subject-specific scholarships. Keep your marks, activity record, documents, and application deadlines organised in one place."
    if any(word in question_lower for word in ("internship", "resume", "cv", "interview")):
        return "Build a simple one-page resume, add projects or activities that demonstrate your skills, and begin with internships, clubs, competitions, or volunteering related to your interests."
    if any(word in question_lower for word in ("course", "degree", "subject", "stream", "12th", "school")):
        return "Pick subjects and courses that keep more than one career option open. Check the entry requirements for careers you are interested in before you finalise a path."
    return "A good next step is to identify your interests, strengths, and preferred work style, then explore two or three careers that match them. I can also help you compare courses, skills, and universities."


def inject_styles(theme_name: str) -> None:
    theme = THEMES[theme_name]
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root {{
          --app-bg:{theme['app_bg']}; --text:{theme['text']}; --muted:{theme['muted']};
          --card:{theme['card']}; --card-soft:{theme['card_soft']}; --line:{theme['line']};
          --sidebar:{theme['sidebar']}; --input:{theme['input']}; --shadow:{theme['shadow']};
          --score:{theme['score']}; --mentor:{theme['mentor']}; --violet:#7c3aed; --pink:#ec5b7a; --mint:#15bfa2;
        }}
        * {{ font-family:'DM Sans',sans-serif; }}
        .stApp {{ background:var(--app-bg); color:var(--text); }}
        #MainMenu, footer {{ visibility:hidden; }}
        header {{ background:transparent !important; }}
        .block-container {{ max-width:1530px; padding-top:1.6rem; padding-bottom:2.6rem; }}
        [data-testid='stSidebar'] {{ background:var(--sidebar); border-right:1px solid rgba(211,193,255,.24); }}
        [data-testid='stSidebar'] * {{ color:#f8f5ff !important; }}
        [data-testid='stSidebar'] .stRadio label {{ padding:7px 5px; border-radius:10px; }}
        h1,h2,h3 {{ font-family:'Space Grotesk',sans-serif; color:var(--text); letter-spacing:-.55px; }}
        label,p {{ color:var(--text); }}
        .brand {{ display:flex; align-items:center; gap:10px; margin:5px 0 22px; }}
        .brand-mark {{ width:45px; height:45px; border-radius:15px; display:grid; place-items:center; font-size:27px; background:linear-gradient(135deg,#e83d60,#7247e9); box-shadow:0 9px 25px rgba(221,54,132,.35); }}
        .brand-name {{ color:#fff; font-size:1.35rem; font-family:'Space Grotesk',sans-serif; font-weight:700; }} .brand-name span {{ color:#ff6b81; }}
        .sidebar-brand {{ padding-top:3px; }} .sidebar-brand .brand-name {{ margin:0; white-space:nowrap; }} .sidebar-tagline {{ color:#cfc4eb; font-size:.73rem; margin-top:4px; white-space:nowrap; }}
        .top-title {{ font-family:'Space Grotesk',sans-serif; font-weight:700; color:var(--text); font-size:2.25rem; letter-spacing:-1.5px; margin:0 0 2px; }}
        .top-subtitle {{ color:var(--muted); font-size:1.03rem; margin-bottom:17px; }}
        .panel {{ background:var(--card); border:1px solid var(--line); border-radius:17px; padding:19px; box-shadow:0 15px 38px var(--shadow); box-sizing:border-box; height:100%; }}
        .panel-title {{ font-family:'Space Grotesk',sans-serif; font-weight:700; color:var(--text); font-size:1.07rem; margin:0 0 15px; }}
        .panel-link {{ color:#8b5cf6; font-weight:700; font-size:.84rem; float:right; }}
        .score-panel {{ background:var(--score); color:#fff; border-radius:17px; padding:24px; min-height:250px; box-shadow:0 16px 38px var(--shadow); }}
        .score-panel h3,.score-panel p {{ color:#fff; }} .score-panel p {{ color:rgba(255,255,255,.78); }}
        .big-score {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:3.15rem; color:#fff; margin:24px 0 12px; }}
        .score-ring {{ float:right; margin-top:-76px; width:100px; height:100px; border-radius:50%; border:12px solid rgba(255,255,255,.19); border-top-color:#fff; border-right-color:#fff; box-sizing:border-box; }}
        .match-card {{ background:var(--card-soft); border:1px solid var(--line); border-radius:12px; padding:13px; min-height:185px; box-sizing:border-box; }}
        .match-grid,.mini-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }} .roadmap-grid {{ display:grid; grid-template-columns:1.35fr .65fr; gap:16px; }}
        .icon-bubble {{ width:42px; height:42px; border-radius:14px; display:grid; place-items:center; position:relative; overflow:hidden; font-size:1.35rem; color:#6d3ce5; background:linear-gradient(145deg,rgba(255,255,255,.62),rgba(177,138,255,.28)); border:1px solid rgba(255,255,255,.72); box-shadow:inset 0 1px 1px rgba(255,255,255,.9), inset 0 -8px 14px rgba(100,57,211,.16), 0 9px 20px rgba(70,35,155,.22); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); }}
        .icon-bubble:after {{ content:''; position:absolute; inset:3px 4px auto; height:38%; border-radius:10px; background:linear-gradient(180deg,rgba(255,255,255,.58),rgba(255,255,255,0)); pointer-events:none; }}
        .match-name {{ color:var(--text); font-weight:700; margin:10px 0 4px; }} .match-copy {{ color:var(--muted); font-size:.8rem; line-height:1.45; min-height:58px; }}
        .match-pill {{ float:right; color:var(--mint); background:rgba(21,191,162,.13); padding:4px 7px; border-radius:7px; font-size:.72rem; font-weight:700; }}
        .tiny-link {{ color:#8b5cf6; font-size:.78rem; font-weight:700; }}
        .mentor-panel {{ background:var(--mentor); border:1px solid rgba(236,91,122,.44); border-radius:17px; padding:21px; min-height:100%; text-align:center; box-shadow:0 15px 38px var(--shadow); box-sizing:border-box; }}
        .mentor-panel h3 {{ text-align:left; margin:0; }} .mentor-orb {{ width:102px; height:102px; border-radius:50%; margin:33px auto 22px; display:grid; place-items:center; font-size:47px; background:radial-gradient(circle,#3d1959,#100a29); border:2px solid #9d5cff; box-shadow:0 0 0 13px rgba(140,78,245,.08); }}
        .ai-card {{ background:var(--mentor); border:1px solid rgba(236,91,122,.38); border-radius:17px; padding:20px; margin:0 0 18px; box-shadow:0 12px 30px var(--shadow); }} .ai-card h3 {{ margin:0 0 7px; }} .ai-card p {{ color:var(--muted); margin:0; }}
        .st-key-ai_mentor_card {{ background:var(--mentor); border:1px solid rgba(236,91,122,.44)!important; border-radius:17px; padding:12px 13px 16px; box-shadow:0 15px 38px var(--shadow); text-align:center; }}
        .st-key-ai_mentor_card img {{ filter:drop-shadow(0 0 9px rgba(167,99,255,.9)) drop-shadow(0 0 22px rgba(236,91,122,.42)); }}
        [data-testid='stImage'] img {{ filter:drop-shadow(0 0 7px rgba(163,99,255,.9)) drop-shadow(0 0 18px rgba(236,91,122,.42)); animation:logo-glow 2.8s ease-in-out infinite; }}
        @keyframes logo-glow {{ 50% {{ filter:drop-shadow(0 0 12px rgba(181,114,255,1)) drop-shadow(0 0 30px rgba(255,91,141,.7)); }} }}
        .roadmap {{ border-left:2px solid rgba(124,58,237,.35); margin:5px 0 0 8px; }} .roadmap-item {{ padding:0 0 13px 16px; position:relative; color:var(--text); font-size:.83rem; }} .roadmap-item:before {{ content:''; position:absolute; left:-8px; top:4px; width:13px; height:13px; border-radius:50%; background:#7352e7; box-shadow:0 0 0 3px rgba(124,58,237,.14); }} .roadmap-item.done:before {{ background:var(--mint); }} .roadmap-sub {{ color:var(--muted); font-size:.72rem; }}
        .progress-circle {{ width:94px; height:94px; min-width:94px; border:10px solid rgba(124,58,237,.18); border-top-color:#7c3aed; border-right-color:#7c3aed; border-radius:50%; display:grid; place-items:center; font-weight:700; font-size:1.2rem; line-height:1; white-space:nowrap; margin:12px auto; box-sizing:border-box; }}
        .insight {{ display:flex; gap:10px; padding:12px 0; border-top:1px solid var(--line); color:var(--muted); font-size:.8rem; line-height:1.42; }} .insight:first-of-type {{ border-top:0; }} .insight-icon {{ color:#8b5cf6; font-size:1.25rem; }}
        .course-card,.scholar-card {{ background:var(--card-soft); border:1px solid var(--line); border-radius:12px; padding:12px; min-height:102px; box-sizing:border-box; }}
        .course-card b,.scholar-card b {{ color:var(--text); font-size:.78rem; }} .course-meta {{ color:var(--muted); font-size:.72rem; margin-top:16px; }} .price {{ color:var(--mint); font-weight:700; font-size:.8rem; margin-top:13px; }}
        .university-row {{ display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--line); padding:12px 0; color:var(--text); font-weight:600; font-size:.86rem; }} .university-row:first-of-type {{ border-top:0; }}
        .tag {{ color:var(--mint); background:rgba(21,191,162,.13); border-radius:7px; padding:5px 8px; font-size:.71rem; font-weight:700; }}
        [data-testid='stSidebar'] .stRadio label {{ background:linear-gradient(145deg,rgba(255,255,255,.10),rgba(145,98,255,.08)); border:1px solid rgba(255,255,255,.10); box-shadow:inset 0 1px rgba(255,255,255,.10), 0 5px 12px rgba(4,0,25,.16); backdrop-filter:blur(12px); }}
        [data-testid='stSidebar'] .stRadio label:hover {{ background:linear-gradient(145deg,rgba(255,255,255,.17),rgba(156,98,255,.20)); border-color:rgba(201,172,255,.42); }}
        .login-panel {{ background:var(--card); border:1px solid var(--line); border-radius:28px; padding:43px; box-shadow:0 22px 64px var(--shadow); }} .login-title {{ font-family:'Space Grotesk',sans-serif; color:var(--text); font-size:2.65rem; line-height:1.05; letter-spacing:-1.5px; margin:0 0 10px; }} .login-subtitle {{ color:var(--muted); margin-bottom:22px; }}
        .career-visual {{ position:relative; min-height:610px; display:flex; align-items:center; justify-content:center; overflow:hidden; }} .orb {{ position:absolute; width:480px; height:480px; border:1px dashed rgba(124,58,237,.35); border-radius:50%; }} .career-quote {{ position:relative; z-index:2; max-width:370px; text-align:center; font-family:'Space Grotesk',sans-serif; color:var(--text); font-size:2.9rem; line-height:1.04; font-weight:700; letter-spacing:-1.9px; }} .career-quote span {{ color:var(--pink); }} .float {{ position:absolute; z-index:3; display:grid; place-items:center; width:93px; height:93px; border:1px solid var(--line); background:var(--card-soft); border-radius:26px; font-size:3.15rem; box-shadow:0 13px 32px var(--shadow); animation:drift 4s ease-in-out infinite; }} .one{{top:45px;left:15%}}.two{{top:48px;right:15%;animation-delay:-1s}}.three{{top:233px;left:2%;animation-delay:-2s}}.four{{top:233px;right:2%;animation-delay:-.5s}}.five{{bottom:44px;left:17%;animation-delay:-2.5s}}.six{{bottom:44px;right:17%;animation-delay:-1.5s}} @keyframes drift{{50%{{transform:translateY(-12px) rotate(3deg)}}}}
        div[data-baseweb='input']>div {{ background:var(--input)!important; border-color:var(--line)!important; color:var(--text)!important; }} input {{ color:var(--text)!important; }}
        .stButton>button,button[kind='primary'] {{ background:linear-gradient(90deg,#7c3aed,#ef5e7d); color:#fff; border:1px solid rgba(255,255,255,.16); border-radius:12px; font-weight:700; min-height:42px; box-shadow:0 8px 18px rgba(95,45,199,.24); transition:transform .24s ease, background .24s ease, border-color .24s ease, box-shadow .24s ease, backdrop-filter .24s ease; }}
        .stButton>button:hover,button[kind='primary']:hover {{ transform:translateY(-2px) scale(1.01); color:var(--text); background:linear-gradient(135deg,rgba(255,255,255,.35),rgba(181,143,255,.22)); border-color:rgba(255,255,255,.68); box-shadow:inset 0 1px 1px rgba(255,255,255,.82), inset 0 -8px 16px rgba(106,58,224,.14), 0 12px 28px rgba(110,55,220,.32); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); }}
        .stButton>button:active,button[kind='primary']:active {{ transform:translateY(0) scale(.98); box-shadow:inset 0 2px 8px rgba(52,23,112,.28); }}
        @media(max-width:900px){{.block-container{{padding:1rem}}.login-panel{{padding:30px 22px}}.career-visual{{min-height:400px}}.career-quote{{font-size:2.1rem}}.float{{width:67px;height:67px;font-size:2.2rem}}.top-title{{font-size:1.9rem}}.match-grid,.mini-grid{{grid-template-columns:1fr}}.roadmap-grid{{grid-template-columns:1fr}}}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def go_to(page: str) -> None:
    st.session_state.nav_page = page


def render_login() -> None:
    top_left, top_right = st.columns([5, 1])
    with top_right:
        st.toggle("☀️ Light mode", key="light_mode")

    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        st.image(LOGO_PATH, width=86)
        st.markdown("""
        <div class='login-panel'>
          <div class='brand'><div class='brand-name'>Career <span>AI</span></div></div>
          <h1 class='login-title'>Welcome back</h1>
          <div class='login-subtitle'>Your future is waiting.</div>
        """, unsafe_allow_html=True)
        username = st.text_input("Username or email", placeholder="Enter your username or email", key="username_input")
        st.text_input("Password", placeholder="Enter your password", type="password")
        st.checkbox("Remember me")
        if st.button("Sign in  →", use_container_width=True):
            st.session_state.student_name = username.split("@")[0].strip().title() or "Student"
            st.session_state.app_stage = "quiz"
            st.rerun()
        st.markdown("<p style='text-align:center;color:var(--muted);margin:28px 0 0'>New to Career AI? <span style='color:#8b5cf6;font-weight:700'>Create an account</span></p></div>", unsafe_allow_html=True)
    with right:
        st.markdown("""
        <div class='career-visual'>
          <div class='orb'></div><div class='float one'>🩺</div><div class='float two'>💻</div>
          <div class='float three'>🏏</div><div class='float four'>🎓</div>
          <div class='float five'>🎨</div><div class='float six'>🔬</div>
          <div class='career-quote'>Every interest<br>can become a <span>future.</span></div>
        </div>
        """, unsafe_allow_html=True)


def render_sidebar() -> str:
    with st.sidebar:
        logo_col, name_col = st.columns([.3, .7], gap="small")
        with logo_col:
            st.image(LOGO_PATH, width=62)
        with name_col:
            st.markdown("<div class='sidebar-brand'><div class='brand-name'>Career <span>AI</span></div><div class='sidebar-tagline'>Your AI Career Mentor</div></div>", unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio(
            "Navigation",
            PAGES,
            format_func=lambda item: f"{PAGE_ICONS[item]}  {item}",
            key="nav_page",
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("Log out", use_container_width=True):
            st.session_state.app_stage = "login"
            st.session_state.nav_page = "Dashboard"
            st.rerun()
    return page


def render_heading() -> None:
    st.markdown(f"<div class='top-title'>Good morning, {profile_name()} 👋</div><div class='top-subtitle'>Let’s build your future, one step at a time.</div>", unsafe_allow_html=True)


def render_dashboard() -> None:
    render_heading()
    progress = dashboard_progress()
    matches = career_matches()
    score_col, matches_col, mentor_col = st.columns([1.05, 1.43, .67], gap="medium")
    with score_col:
        st.markdown(f"""
        <div class='score-panel'><h3>Career Discovery Progress</h3><div class='big-score'>{progress}%</div><div class='score-ring'></div>
        <b>You’re building a clear picture!</b><p>Your personalised insights will appear here.</p></div>
        """, unsafe_allow_html=True)
    with matches_col:
        descriptions = (
            "Explore a path that fits the interests you shared.",
            "Use your strongest themes to guide your next steps.",
            "Compare courses, skills, and real-world opportunities.",
        )
        cards = tuple(("✦", name, f"{max(70, 94 - index * 4)}%", descriptions[index]) for index, name in enumerate(matches[:3]))
        cards_html = "".join(
            f"<div class='match-card'><span class='match-pill'>{score}</span><div class='icon-bubble'>{icon}</div><div class='match-name'>{name}</div><div class='match-copy'>{copy}</div><span class='tiny-link'>Explore career →</span></div>"
            for icon, name, score, copy in cards
        )
        st.markdown(f"<div class='panel'><span class='panel-link'>View all →</span><div class='panel-title'>Top Career Matches</div><div class='match-grid'>{cards_html}</div></div>", unsafe_allow_html=True)
    with mentor_col:
        with st.container(border=True, key="ai_mentor_card"):
            st.markdown("### AI Mentor")
            _, logo_col, _ = st.columns([1, 1.4, 1])
            with logo_col:
                st.image(LOGO_PATH, use_container_width=True)
            st.markdown("**Ask your AI Mentor**")
            st.caption("Get personalised guidance, clarity, and career advice whenever you need it.")
            st.button("Start a conversation", use_container_width=True, on_click=go_to, args=("AI Mentor",))

    roadmap_col, insight_col = st.columns([1.02, .98], gap="medium")
    with roadmap_col:
        st.markdown(f"""<div class='panel'><span class='panel-link'>View full roadmap</span><div class='panel-title'>Your Learning Roadmap</div><div class='roadmap-grid'><div class='roadmap'>
              <div class='roadmap-item done'><b>1. Self Discovery</b><br><span class='roadmap-sub'>Explore your interests</span></div>
              <div class='roadmap-item'><b>2. Career Exploration</b><br><span class='roadmap-sub'>Review your recommended paths</span></div>
              <div class='roadmap-item'><b>3. Skill Building</b><br><span class='roadmap-sub'>In progress</span></div>
              <div class='roadmap-item'><b>4. Real World Preparation</b><br><span class='roadmap-sub'>Upcoming</span></div>
              <div class='roadmap-item'><b>5. Career Launch</b><br><span class='roadmap-sub'>Upcoming</span></div>
            </div><div><div class='progress-circle'>{progress}%</div><p style='text-align:center;margin:0'><b>Overall Progress</b><br><span style='color:var(--muted);font-size:.78rem'>You’re making great progress!</span></p></div></div></div>""", unsafe_allow_html=True)
    with insight_col:
        st.markdown("""<div class='panel'><span class='panel-link'>View all insights</span><div class='panel-title'>✧ AI Insights</div>
        <div class='insight'><span class='insight-icon'>◎</span><span>You have strong analytical and problem-solving skills, ideal for roles in data and research.</span></div>
        <div class='insight'><span class='insight-icon'>↗</span><span>Gaining expertise in tools like Figma and SQL can boost your career prospects.</span></div>
        <div class='insight'><span class='insight-icon'>♙</span><span>Consider internships in the next 6 months to gain hands-on experience.</span></div></div>""", unsafe_allow_html=True)

    courses_col, universities_col, scholarship_col = st.columns([1.02, .78, 1.2], gap="medium")
    with courses_col:
        courses_html = "".join(f"<div class='course-card'><b>{name}</b><div class='course-meta'>Course provider<br><span class='mint'>4.8 ★</span></div></div>" for name in ("UI/UX Design Fundamentals", "SQL for Data Analysis", "Data Visualization"))
        st.markdown(f"<div class='panel'><span class='panel-link'>View all</span><div class='panel-title'>Recommended Courses</div><div class='mini-grid'>{courses_html}</div></div>", unsafe_allow_html=True)
    with universities_col:
        st.markdown("""<div class='panel'><span class='panel-link'>Browse</span><div class='panel-title'>Top Universities for You</div>
          <div class='university-row'><span>IIT Bombay</span><span class='tag'>Match 94%</span></div>
          <div class='university-row'><span>NID Ahmedabad</span><span class='tag'>Match 91%</span></div>
          <div class='university-row'><span>Ashoka University</span><span class='tag'>Match 88%</span></div></div>""", unsafe_allow_html=True)
    with scholarship_col:
        scholarships_html = "".join(f"<div class='scholar-card'><b>{name}</b><div class='price'>{price}</div><div class='course-meta'>Deadline: Aug 2026</div></div>" for name, price in zip(("Future Leaders Scholarship", "Women in Tech Scholarship", "Merit Excellence Award"), ("Up to $5,000", "Up to $3,000", "Up to $2,500")))
        st.markdown(f"<div class='panel'><span class='panel-link'>View all</span><div class='panel-title'>Scholarship Recommendations</div><div class='mini-grid'>{scholarships_html}</div></div>", unsafe_allow_html=True)


def render_simple_page(page: str) -> None:
    subtitles = {
        "Explore Careers": "Browse career paths in a clean visual layout.",
        "Skill Roadmap": "Plan the skills you want to develop.",
        "Scholarships": "Save scholarship opportunities in one place.",
        "Universities": "Explore colleges and universities for your future.",
        "Profile": "Your student profile and settings will live here.",
        "AI Mentor": "This is the visual space for your AI mentor chat.",
    }
    st.markdown(f"<div class='top-title'>{page}</div><div class='top-subtitle'>{subtitles[page]}</div>", unsafe_allow_html=True)
    if page == "Explore Careers":
        for career in career_matches():
            st.markdown(f"<div class='panel'><div class='icon-bubble'>✦</div><h3>{career}</h3><p style='color:var(--muted);font-size:.9rem'>A static career card for the frontend design. Connect recommendation data here later.</p></div>", unsafe_allow_html=True)
        return
    for row in range(2):
        cols = st.columns(3)
        for number, col in enumerate(cols, start=1 + row * 3):
            with col:
                st.markdown(f"<div class='panel'><div class='icon-bubble'>✦</div><h3>{page} card {number}</h3><p style='color:var(--muted);font-size:.85rem'>Static UI space — connect your backend data here later.</p></div>", unsafe_allow_html=True)


def render_ai_mentor() -> None:
    st.markdown("<div class='top-title'>AI Mentor</div><div class='top-subtitle'>Ask about careers, courses, skills, universities, scholarships, or internships.</div>", unsafe_allow_html=True)
    st.markdown("<div class='ai-card'><h3>Career-focused guidance only</h3><p>I can help you think through education and career decisions. For anything unrelated, I’ll politely guide you back to a career question.</p></div>", unsafe_allow_html=True)

    with st.form("mentor_question_form", clear_on_submit=True):
        question = st.text_input("Ask your question", placeholder="Example: Which skills should I develop for UX design?")
        submitted = st.form_submit_button("Ask AI Mentor  →", use_container_width=True)

    if submitted:
        if question.strip():
            st.session_state.mentor_history.append((question.strip(), mentor_reply(question.strip())))
        else:
            st.warning("Please type a career-related question first.")

    for asked, response in reversed(st.session_state.mentor_history[-5:]):
        st.markdown(f"<div class='panel'><p style='margin:0 0 10px'><b>You:</b> {escape(asked)}</p><p style='color:var(--muted);margin:0'><b>Career AI:</b> {escape(response)}</p></div>", unsafe_allow_html=True)


def render_app() -> None:
    _, theme_col = st.columns([5, 1])
    with theme_col:
        st.toggle("☀️ Light mode", key="light_mode")
    page = render_sidebar()
    if page == "Dashboard":
        render_dashboard()
    elif page == "AI Mentor":
        render_ai_mentor()
    else:
        render_simple_page(page)


def render_quiz() -> None:
    """Empty frontend screen reserved for the career-discovery quiz."""
    _, theme_col = st.columns([5, 1])
    with theme_col:
        st.toggle("☀️ Light mode", key="light_mode")

    st.markdown("<div class='top-title'>Career Discovery Quiz</div><div class='top-subtitle'>Tell us about your interests, strengths, subjects and goals.</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='panel' style='max-width:820px;margin:36px auto;padding:48px;text-align:center'>
      <div style='font-size:3rem;margin-bottom:12px'>✦</div>
      <h2 style='margin-bottom:10px'>Your quiz will appear here</h2>
      <p style='color:var(--muted);max-width:510px;margin:0 auto'>This page is ready for your career-interest questions. Add the questions whenever you have them.</p>
    </div>
    """, unsafe_allow_html=True)
    _, action_col, _ = st.columns([1, 1.15, 1])
    with action_col:
        if st.button("Finish quiz and view summary  →", use_container_width=True):
            st.session_state.app_stage = "dashboard"
            st.rerun()


def main() -> None:
    init_state()
    inject_styles(current_theme())
    if st.session_state.app_stage == "quiz":
        render_quiz()
    elif st.session_state.app_stage == "dashboard":
        render_app()
    else:
        render_login()


if __name__ == "__main__":
    main()
