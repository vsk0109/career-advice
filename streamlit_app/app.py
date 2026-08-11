"""
Career Compass AI — main Streamlit app.

Flow:
    Login (streamlit-authenticator) -> Complete Profile -> Dashboard / other pages

Run:
    pip install -r requirements.txt
    streamlit run app.py

Before running: generate real password hashes with generate_hashes.py and
paste them into auth_config.yaml -- the placeholders there won't work as-is.
"""

import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import plotly.graph_objects as go

import api_client

st.set_page_config(page_title="Career Compass AI", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# STEP 1 -- Load auth config and build the Authenticate object
# ---------------------------------------------------------------------------

with open("auth_config.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# ---------------------------------------------------------------------------
# STEP 2 -- Render the login form. Writes st.session_state["authentication_status"],
# ["name"], and ["username"] behind the scenes.
# ---------------------------------------------------------------------------

authenticator.login()

if st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password.")
    st.info(
        "Demo login for the expo: create a 'guest' account with a known password "
        "using generate_hashes.py, and post it near your booth so visitors can log in."
    )
    st.stop()

# ---------------------------------------------------------------------------
# STEP 3 -- Authenticated. Everything below only runs for logged-in users.
# ---------------------------------------------------------------------------

RIASEC_QUESTIONS = [
    {"text": "I enjoy fixing, building, or working with tools and machines.", "dimension": "R"},
    {"text": "I like working outdoors or with my hands.", "dimension": "R"},
    {"text": "I enjoy solving puzzles, analyzing data, or doing research.", "dimension": "I"},
    {"text": "I like understanding how and why things work.", "dimension": "I"},
    {"text": "I enjoy creative writing, art, music, or design.", "dimension": "A"},
    {"text": "I like expressing myself in original or unconventional ways.", "dimension": "A"},
    {"text": "I enjoy helping, teaching, or counseling other people.", "dimension": "S"},
    {"text": "I like working in teams and communicating with others.", "dimension": "S"},
    {"text": "I enjoy leading projects, persuading people, or starting new ventures.", "dimension": "E"},
    {"text": "I like taking initiative and being in charge.", "dimension": "E"},
    {"text": "I enjoy organizing information, following procedures, and being detail-oriented.", "dimension": "C"},
    {"text": "I like structured tasks with clear rules and steps.", "dimension": "C"},
]

DEFAULTS = {
    "student_id": None,
    "page": "Complete Profile",
    "chat_history": [],
    "profile_data": None,
    "roadmap_checked": {},
    "visited_pages": set(),
    "top_matches_cache": None,
    "insights_cache": None,
}
for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
<style>
    .stApp { background-color: #f8f7fc; }
    .card { background: white; border-radius: 16px; padding: 20px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 16px; }
    .card-title { font-size: 15px; font-weight: 600; color: #1f2937; margin-bottom: 14px; }
    .gradient-card { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
                      border-radius: 16px; padding: 22px; color: white; margin-bottom: 16px; }
    .match-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
    .match-name { font-size: 13px; font-weight: 500; color: #1f2937; width: 160px; flex-shrink: 0; }
    .match-bar-bg { flex-grow: 1; background: #ede9fe; border-radius: 6px; height: 6px; overflow: hidden; }
    .match-bar-fill { background: #8b5cf6; height: 6px; border-radius: 6px; }
    .match-pct { font-size: 13px; font-weight: 600; color: #1f2937; width: 36px; text-align: right; }
    .skill-bar-bg { background: #f1f5f9; border-radius: 6px; height: 8px; overflow: hidden; width: 100%; }
    .skill-bar-fill-you { background: #8b5cf6; height: 8px; }
    .skill-bar-fill-req { background: #fbcfe8; height: 8px; }
    .course-card { background: white; border: 1px solid #eee; border-radius: 14px; padding: 16px; height: 100%; }
    .match-badge { display: inline-block; background: #dcfce7; color: #16a34a;
                    font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; margin-top: 4px; }
    section[data-testid="stSidebar"] button {
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 8px !important;
        margin-bottom: 3px !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #c4b5fd !important;
        color: #3730a3 !important;
        border: none !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #b3a2f7 !important;
        color: #3730a3 !important;
    }
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #f5f3ff !important;
        color: #4c1d95 !important;
        border: 1px solid #ede9fe !important;
    }
        section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #ede9fe !important;
        color: #4c1d95 !important;
        border: 1px solid #ddd6fe !important;
    }

    @keyframes floatUpDown {
        0%   { transform: translateY(0px); }
        50%  { transform: translateY(-22px); }
        100% { transform: translateY(0px); }
    }
    .floating-emoji {
        position: fixed;
        font-size: 42px;
        opacity: 0.55;
        z-index: 0;
        pointer-events: none;
        animation: floatUpDown 4.5s ease-in-out infinite;
    }
    .floating-emoji.book {
        top: 18%;
        right: 40px;
        animation-delay: 0s;
    }
    .floating-emoji.flask {
        top: 55%;
        right: 90px;
        font-size: 36px;
        animation-delay: 1.6s;
    }
</style>
<div class="floating-emoji book">📚</div>
<div class="floating-emoji flask">⚗️</div>
""", unsafe_allow_html=True)


def require_profile():
    """Call at the top of any page that needs a completed profile."""
    if not st.session_state.student_id:
        st.warning("Complete your profile first to unlock this page.")
        st.stop()


def get_top_matches():
    """
    Cached in session_state so navigating between pages doesn't re-hit the
    backend (and the LLM) on every click — only refetches when the cache
    has been explicitly cleared (profile resubmitted, or manual refresh).
    """
    if st.session_state.top_matches_cache is None:
        st.session_state.top_matches_cache = api_client.get_score(st.session_state.student_id)
    return st.session_state.top_matches_cache


def get_insights(top_matches):
    """Same caching approach as get_top_matches — the LLM call is the slow part."""
    if st.session_state.insights_cache is None:
        st.session_state.insights_cache = api_client.get_insights(st.session_state.student_id, top_matches)
    return st.session_state.insights_cache


def clear_recommendation_cache():
    """Call this whenever the underlying profile changes, so stale scores/insights don't stick around."""
    st.session_state.top_matches_cache = None
    st.session_state.insights_cache = None


# ---------------------------------------------------------------------------
# Sidebar -- nav + logout
# ---------------------------------------------------------------------------

NAV_OPTIONS = [
    "Complete Profile", "Dashboard", "My Profile", "Career Explorer",
    "Courses", "Universities", "Scholarships", "Skill Gap",
    "Roadmap", "AI Mentor", "Progress", "Settings",
]

with st.sidebar:
    st.markdown("### Career Compass AI")
    st.caption(f"Welcome, {st.session_state.get('name', 'Student')}!")
    st.markdown("---")
    st.caption("NAVIGATION")
    for item in NAV_OPTIONS:
        is_active = st.session_state.page == item
        if st.button(
            item, key=f"nav_{item}", use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.page = item
            st.rerun()
    st.markdown("---")
    st.markdown("""
    <div class="gradient-card" style="text-align:center; padding:16px;">
        <div style="font-weight:600; margin-bottom:4px;">🤖 AI Mentor</div>
        <div style="font-size:12px; opacity:0.9;">Your personal career guide is here to help!</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Chat Now →", use_container_width=True):
        st.session_state.page = "AI Mentor"
        st.rerun()
    st.markdown("---")
    authenticator.logout("Logout", "sidebar")

st.session_state.visited_pages.add(st.session_state.page)
page = st.session_state.page

# ---------------------------------------------------------------------------
# PAGE: Complete Profile (intake form)
# ---------------------------------------------------------------------------

if page == "Complete Profile":
    st.markdown("## Tell us about yourself")
    st.caption("This takes about 2 minutes and powers all your recommendations.")

    with st.form("intake_form"):
        st.markdown("#### Interests")
        interests = st.multiselect(
            "What are you interested in?",
            ["technology", "design", "business", "healthcare", "environment",
             "psychology", "coding", "research", "leadership", "creativity"],
        )

        st.markdown("#### Hobbies")
        hobbies = st.multiselect(
            "What do you enjoy doing outside class?",
            ["coding", "reading", "sketching", "sports", "music",
             "volunteering", "gaming", "writing", "debating"],
        )

        st.markdown("#### Personality Quiz")
        st.caption("Rate how much each statement sounds like you (1 = not at all, 5 = very much).")
        riasec_answers = [st.slider(q["text"], 1, 5, 3, key=q["text"]) for q in RIASEC_QUESTIONS]

        st.markdown("#### Academics")
        col1, col2 = st.columns(2)
        with col1:
            math_marks = st.number_input("Math", 0, 100, 75)
            physics_marks = st.number_input("Physics", 0, 100, 75)
            cs_marks = st.number_input("Computer Science", 0, 100, 75)
        with col2:
            english_marks = st.number_input("English", 0, 100, 75)
            biology_marks = st.number_input("Biology", 0, 100, 70)
            economics_marks = st.number_input("Economics", 0, 100, 70)

        st.markdown("#### Self-Rated Skills")
        col3, col4 = st.columns(2)
        with col3:
            coding_skill = st.slider("Coding", 1, 5, 3)
            communication_skill = st.slider("Communication", 1, 5, 3)
        with col4:
            statistics_skill = st.slider("Statistics", 1, 5, 3)
            leadership_skill = st.slider("Leadership", 1, 5, 3)

        submitted = st.form_submit_button("Get My Recommendations →")

    if submitted:
        profile_data = {
            "name": st.session_state.get("name", "Student"),
            "interests": interests,
            "hobbies": hobbies,
            "riasec_answers": riasec_answers,
            "academics": {
                "Math": math_marks, "Physics": physics_marks, "Computer Science": cs_marks,
                "English": english_marks, "Biology": biology_marks, "Economics": economics_marks,
            },
            "self_rated_skills": {
                "Coding": coding_skill, "Communication": communication_skill,
                "Statistics": statistics_skill, "Leadership": leadership_skill,
            },
        }
        result = api_client.create_profile(profile_data)
        if result:
            st.session_state.student_id = result["student_id"]
            st.session_state.profile_data = result
            clear_recommendation_cache()
            st.success("Profile saved! Head to your Dashboard.")
            st.session_state.page = "Dashboard"
            st.rerun()
        else:
            st.error("Couldn't reach the backend. Make sure `uvicorn app.main:app --reload` is running.")

# ---------------------------------------------------------------------------
# PAGE: Dashboard
# ---------------------------------------------------------------------------

elif page == "Dashboard":
    require_profile()
    top_matches = get_top_matches()
    insights = get_insights(top_matches)

    header_col, refresh_col = st.columns([5, 1])
    with header_col:
        st.markdown(f"## Good to see you, {st.session_state.get('name', 'Student')}! 👋")
    with refresh_col:
        if st.button("↻ Refresh"):
            clear_recommendation_cache()
            st.rerun()

    col1, col2 = st.columns([1.4, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Top Career Matches</div>', unsafe_allow_html=True)
        for m in top_matches:
            st.markdown(f"""
            <div class="match-row">
                <div class="match-name">{m['career']}</div>
                <div class="match-bar-bg"><div class="match-bar-fill" style="width:{m['score']}%;"></div></div>
                <div class="match-pct">{m['score']}%</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if top_matches:
            top_score = top_matches[0]["score"]
            fig = go.Figure(go.Pie(
                values=[top_score, 100 - top_score], hole=0.78,
                marker=dict(colors=["#8b5cf6", "#ede9fe"]), textinfo="none", sort=False,
            ))
            fig.update_layout(
                showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=180,
                annotations=[dict(
                    text=f"<b>{top_score}%</b><br><span style='font-size:11px;color:#6b7280'>Top Match</span>",
                    x=0.5, y=0.5, showarrow=False, font=dict(size=24, color="#1f2937"),
                )],
            )
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Career Suitability</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="gradient-card">
            <div style="font-weight:600; margin-bottom:8px;">✨ AI Insight</div>
            <div style="font-size:13px; line-height:1.5; opacity:0.95;">{insights.get('emerging_trend', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Learning Roadmap</div>', unsafe_allow_html=True)
        for step in insights.get("roadmap", []):
            st.markdown(f"- {step}")
        st.caption("See the Roadmap page to track your progress on these steps.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Why These Fit You</div>', unsafe_allow_html=True)
    for career, explanation in insights.get("explanations", {}).items():
        st.markdown(f"**{career}**")
        st.write(explanation)
        st.write("")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: My Profile
# ---------------------------------------------------------------------------

elif page == "My Profile":
    require_profile()
    profile = api_client.get_profile(st.session_state.student_id) or st.session_state.profile_data

    st.markdown("## My Profile")

    if not profile:
        st.info("Profile details aren't available right now (backend unreachable). Try again once it's running.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Basic Info</div>', unsafe_allow_html=True)
            st.write(f"**Name:** {profile.get('name', '-')}")
            st.write(f"**Interests:** {', '.join(profile.get('interests', [])) or '-'}")
            st.write(f"**Hobbies:** {', '.join(profile.get('hobbies', [])) or '-'}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Academics</div>', unsafe_allow_html=True)
            for subject, mark in profile.get("academics", {}).items():
                st.write(f"{subject}: **{mark}**")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Personality (RIASEC)</div>', unsafe_allow_html=True)
            riasec = profile.get("riasec_scores", {})
            if riasec:
                fig = go.Figure(go.Scatterpolar(
                    r=list(riasec.values()) + [list(riasec.values())[0]],
                    theta=list(riasec.keys()) + [list(riasec.keys())[0]],
                    fill="toself", line_color="#8b5cf6",
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                    showlegend=False, margin=dict(l=30, r=30, t=20, b=20), height=280,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Self-Rated Skills</div>', unsafe_allow_html=True)
            for skill, rating in profile.get("self_rated_skills", {}).items():
                st.write(f"{skill}: {'⭐' * rating}")
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Retake Profile Quiz"):
        st.session_state.page = "Complete Profile"
        st.rerun()

# ---------------------------------------------------------------------------
# PAGE: Career Explorer
# ---------------------------------------------------------------------------

elif page == "Career Explorer":
    st.markdown("## Career Explorer")
    st.caption("Browse every career in our dataset, not just your top matches.")

    careers = api_client.get_all_careers()
    search = st.text_input("Search careers", "")
    filtered = [c for c in careers if search.lower() in c["name"].lower()] if search else careers

    for c in filtered:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        badge = " 🌱 Emerging" if c.get("emerging") else ""
        st.markdown(f"#### {c['name']}{badge}")
        st.write(c.get("description", ""))
        with st.expander("Details"):
            st.write("**Relevant subjects:**", ", ".join(c.get("relevant_subjects", [])))
            st.write("**Required skills:**", ", ".join(c.get("required_skills", [])))
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: Courses
# ---------------------------------------------------------------------------

elif page == "Courses":
    require_profile()
    top_matches = get_top_matches()
    careers = {c["name"]: c for c in api_client.get_all_careers()}

    st.markdown("## Recommended Courses")
    cols = st.columns(3)
    i = 0
    for m in top_matches:
        career = careers.get(m["career"])
        if not career:
            continue
        for course in career.get("courses", []):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="course-card">
                    <div style="font-weight:600; font-size:14px;">{course['name']}</div>
                    <div class="match-badge">{m['score']}% Match</div>
                    <div style="font-size:12px; color:#6b7280; margin-top:10px;">
                        {course.get('level', '')} &nbsp; via {career['name']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            i += 1
    if i == 0:
        st.info("No course data available yet — check back once your top matches have course info.")

# ---------------------------------------------------------------------------
# PAGE: Universities
# ---------------------------------------------------------------------------

elif page == "Universities":
    require_profile()
    top_matches = get_top_matches()
    careers = {c["name"]: c for c in api_client.get_all_careers()}

    st.markdown("## Recommended Universities & Colleges")
    for m in top_matches:
        career = careers.get(m["career"])
        if not career or not career.get("colleges"):
            continue
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">For {career["name"]}</div>', unsafe_allow_html=True)
        for college in career["colleges"]:
            st.write(f"🏛️ **{college['name']}** — {college.get('location', '')}")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: Scholarships
# ---------------------------------------------------------------------------

elif page == "Scholarships":
    require_profile()
    top_matches = get_top_matches()
    careers = {c["name"]: c for c in api_client.get_all_careers()}

    st.markdown("## Scholarships & Financial Aid")
    for m in top_matches:
        career = careers.get(m["career"])
        if not career or not career.get("scholarships"):
            continue
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">For {career["name"]}</div>', unsafe_allow_html=True)
        for s in career["scholarships"]:
            st.write(f"🏆 **{s['name']}**")
            st.caption(s.get("eligibility", ""))
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: Skill Gap
# ---------------------------------------------------------------------------

elif page == "Skill Gap":
    require_profile()
    top_matches = get_top_matches()
    profile = st.session_state.profile_data or {}
    self_rated = profile.get("self_rated_skills", {})

    st.markdown("## Skill Gap Analysis")
    if not top_matches:
        st.info("No matches yet.")
    else:
        top = top_matches[0]
        st.caption(f"Based on your top match: **{top['career']}**")

        gaps = top.get("skill_gaps", [])
        if not gaps:
            st.success("No major skill gaps detected for your top match!")
        for skill in gaps:
            your_level = self_rated.get(skill, 2) * 20  # 1-5 scale -> rough 0-100
            required = 90
            gap = required - your_level
            c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
            c1.markdown(f"**{skill}**")
            c2.markdown(f"""<div class="skill-bar-bg"><div class="skill-bar-fill-you" style="width:{your_level}%;"></div></div>
                <span style="font-size:11px;color:#6b7280;">{your_level}%</span>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="skill-bar-bg"><div class="skill-bar-fill-req" style="width:{required}%;"></div></div>
                <span style="font-size:11px;color:#6b7280;">{required}%</span>""", unsafe_allow_html=True)
            c4.markdown(f"<span style='color:#ef4444;font-weight:600;'>{gap}%</span>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: Roadmap
# ---------------------------------------------------------------------------

elif page == "Roadmap":
    require_profile()
    top_matches = get_top_matches()
    insights = get_insights(top_matches)
    roadmap = insights.get("roadmap", [])

    st.markdown("## Your Learning Roadmap")
    st.caption("Check off steps as you complete them.")

    for i, step in enumerate(roadmap):
        key = f"roadmap_{i}"
        checked = st.session_state.roadmap_checked.get(key, False)
        new_val = st.checkbox(step, value=checked, key=key)
        st.session_state.roadmap_checked[key] = new_val

    if roadmap:
        done = sum(1 for i in range(len(roadmap)) if st.session_state.roadmap_checked.get(f"roadmap_{i}"))
        st.progress(done / len(roadmap))
        st.caption(f"{done} of {len(roadmap)} steps complete")

# ---------------------------------------------------------------------------
# PAGE: AI Mentor (chat)
# ---------------------------------------------------------------------------

elif page == "AI Mentor":
    require_profile()
    st.markdown("## 🤖 AI Mentor")
    st.caption("Ask anything about your career matches, courses, or next steps.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_msg = st.chat_input("Ask your mentor something...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)

        reply = api_client.send_chat_message(st.session_state.student_id, user_msg)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

# ---------------------------------------------------------------------------
# PAGE: Progress
# ---------------------------------------------------------------------------

elif page == "Progress":
    require_profile()
    top_matches = get_top_matches()
    profile = st.session_state.profile_data or {}

    profile_fields = ["interests", "hobbies", "academics", "self_rated_skills"]
    filled = sum(1 for f in profile_fields if profile.get(f))
    profile_completion = round((filled / len(profile_fields)) * 100)

    skills_analysis = round(top_matches[0]["skill_score"]) if top_matches else 0
    career_research = 100 if "Career Explorer" in st.session_state.visited_pages else 40

    roadmap_keys = [k for k in st.session_state.roadmap_checked if k.startswith("roadmap_")]
    if roadmap_keys:
        roadmap_progress = round(
            sum(st.session_state.roadmap_checked.values()) / len(roadmap_keys) * 100
        )
    else:
        roadmap_progress = 0

    overall = round((profile_completion + skills_analysis + career_research + roadmap_progress) / 4)

    st.markdown("## Progress Tracker")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">Overall Progress — {overall}%</div>', unsafe_allow_html=True)
    st.progress(overall / 100)
    st.write("")
    for label, value, icon in [
        ("Profile Completion", profile_completion, "👤"),
        ("Skills Analysis", skills_analysis, "📈"),
        ("Career Research", career_research, "🔍"),
        ("Roadmap Progress", roadmap_progress, "🗺️"),
    ]:
        st.markdown(f"{icon} **{label}**: {value}%")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: Settings
# ---------------------------------------------------------------------------

elif page == "Settings":
    st.markdown("## Settings")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Account</div>', unsafe_allow_html=True)
    st.write(f"**Name:** {st.session_state.get('name', '-')}")
    st.write(f"**Username:** {st.session_state.get('username', '-')}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Reset</div>', unsafe_allow_html=True)
    if st.button("Clear my profile and start over"):
        st.session_state.student_id = None
        st.session_state.profile_data = None
        st.session_state.chat_history = []
        st.session_state.roadmap_checked = {}
        clear_recommendation_cache()
        st.session_state.page = "Complete Profile"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
