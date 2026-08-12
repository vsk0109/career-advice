"""Career AI — interactive Streamlit career mentor.

Career-intake and personality questions are based on the supplied Career
Mentor Question Bank. Answers stay only in this Streamlit browser session.
"""

from __future__ import annotations

from html import escape
import random

import streamlit as st


LOGO_PATH = "assets/career-ai-logo-cropped.png"
st.set_page_config(page_title="Career AI", page_icon=LOGO_PATH, layout="wide", initial_sidebar_state="expanded")

PAGES = ("Dashboard", "Explore Careers", "Skill Roadmap", "Scholarships", "Universities", "Profile", "AI Mentor")
PAGE_ICONS = {"Dashboard": "⌂", "Explore Careers": "⌕", "Skill Roadmap": "↗", "Scholarships": "✦", "Universities": "♜", "Profile": "♙", "AI Mentor": "✧"}
QUOTES = (
    "The future depends on what you do today.",
    "Choose a path that lets your strengths grow.",
    "A career is explored one thoughtful step at a time.",
    "Your interests are clues, not limits.",
)

# The full intake bank, grouped as in the supplied document. All prompts are
# intentionally open text so students can answer in their own words.
INTAKE_SECTIONS = (
    ("Basic profile & background", (
        "Tell us your full name, age, and current grade or year of study.",
        "What is your school or institution, board/curriculum, and stream?",
        "Where do you currently live (city, state, and country)?",
        "Are you the first person in your immediate family to pursue higher education?",
        "Which languages are you most comfortable studying and communicating in?",
        "Is there any community, category, or group information you would like us to consider for targeted scholarships? (optional)",
        "Are there physical, learning, or health-related considerations we should account for in recommendations? (optional)",
        "Who most influences your academic and career decisions?",
    )),
    ("Academic performance", (
        "What is your most recent overall percentage, GPA, or CGPA?",
        "Describe your marks or grades in individual subjects over the last two to three academic years.",
        "Which subjects do you consistently score highest in?",
        "Which subjects do you find most difficult or score lowest in?",
        "Which entrance or aptitude tests have you taken or plan to take, and what are your scores or targets?",
        "What academic honours, olympiads, competitions, or subject awards have you received?",
        "Have you repeated a grade, taken a gap year, or faced a disruption in your academic timeline? (optional)",
        "How would you rate your academic performance relative to your effort: underperforming, on par, or overperforming?",
    )),
    ("Interests & passions", (
        "If you had a completely free afternoon, what would you choose to do?",
        "Which school subjects genuinely interest you, even if they are not your highest-scoring ones?",
        "Name up to five topics, fields, or industries you enjoy reading, watching, or talking about.",
        "Is there a career, role, or public figure whose day-to-day work you admire? What appeals to you about it?",
        "Rank your preference for working with people, data/information, physical objects/tools, and abstract ideas.",
        "Would you rather create something new, analyse a problem, help a person, lead a group, or organise a system? Why?",
        "What subjects or industries are you curious about but have not had a chance to explore?",
        "How have your interests changed in the last two or three years?",
        "On a scale of 1–5, how strongly do your interests align with what you think you should pursue for a stable career? Explain briefly.",
    )),
    ("Skills & strengths", (
        "What do teachers, family, or friends say you are naturally good at?",
        "List any technical skills you have, such as coding, design tools, lab work, writing, public speaking, music, or sport.",
        "List soft skills you consider strengths, such as leadership, communication, teamwork, problem-solving, or creativity.",
        "List any certifications, formal training, or online courses you have completed.",
        "Describe a project, assignment, or task you are proud of. What made it successful?",
        "Which skills are you actively trying to build right now?",
        "Rate your confidence (1–5) in analytical reasoning, communication, creativity, maths, interpersonal skills, and digital literacy.",
        "Do you see yourself as more of a generalist or specialist? Why?",
    )),
    ("Hobbies & activities", (
        "What are your current hobbies, and how many hours per week do you spend on each?",
        "Are you part of clubs, teams, student councils, or societies?",
        "Describe any competitions, hackathons, debates, sports tournaments, exhibitions, or performances you have joined.",
        "Do you do volunteering, community service, or social-impact work?",
        "Have you had internships, part-time jobs, shadowing, or freelance experience?",
        "Do you contribute to personal projects outside school, such as a blog, app, channel, small business, or team?",
        "Which activity would you continue even if it never helped your resume or application?",
        "How do your hobbies overlap with your interests?",
    )),
    ("Drive, motivation & work values", (
        "Rank your top three motivators: solving problems, recognition, income, creative freedom, helping others, or status.",
        "Do you prefer a fast-paced, high-pressure environment or a steady, predictable one? Why?",
        "Would you rather work independently, in a small close-knit team, or in a large organisation?",
        "On a scale of 1–5, how important is work-life balance compared with career advancement?",
        "How comfortable are you with uncertainty, entrepreneurship, or unconventional paths compared with stability?",
        "Describe a time you kept working on something difficult. What kept you going?",
        "Would you rather become an expert in one field or work across different areas?",
        "How important is visible positive impact on people or society in your future work?",
        "Where do you see yourself in ten years? Describe it freely.",
    )),
    ("Career awareness & aspirations", (
        "Do you already have a career or field in mind? How did you arrive at it?",
        "If you are undecided, which two or three broad fields are you considering?",
        "Have you spoken with, shadowed, or interviewed anyone in a field you are considering?",
        "What concerns or fears do you have about choosing the wrong career path?",
        "Are there careers you feel pushed toward that do not excite you?",
        "Are there careers you are excited about but hesitant to pursue due to family, financial, or social pressure?",
        "How much importance should recommendations give to salary and job-market demand versus personal interest?",
        "Would you be open to an emerging or unconventional career if it matched your profile well?",
    )),
    ("University & location preferences", (
        "Which countries would you prefer for higher education?",
        "Which states, regions, or cities would you prefer within your home country?",
        "Would you prefer to study close to home or are you open to relocating or studying abroad?",
        "Which campus environment suits you: large research university, small liberal-arts college, specialised institute, or any?",
        "Do you prefer an urban, suburban, or rural/residential campus?",
        "Do you prefer public/government or private institutions, or are you open to both?",
        "On a scale of 1–5, how important is prestige compared with programme fit, cost, and location?",
        "Do you prefer a large student body or a smaller close-knit community?",
        "Are you interested in accreditations, exchanges, or study-abroad opportunities?",
        "What climate, culture, language, safety, or lifestyle preferences matter to you?",
    )),
    ("Financial considerations", (
        "What is your approximate annual budget for tuition and living expenses? A range is fine.",
        "Will you rely on family funding, loans, scholarships, work, or a combination?",
        "Are you open to an education loan, and what is a comfortable maximum amount?",
        "Which merit, need-based, community, sports, or arts scholarships may you qualify for?",
        "Would you consider part-time work, a co-op, or work-study during your studies?",
        "Is cost a hard constraint or a softer preference?",
        "Would you consider a lower-cost institution with a transfer plan later?",
    )),
    ("Learning style", (
        "Do you learn best through hands-on work, visuals, reading/writing, or listening/discussion?",
        "Do you prefer structured coursework or open-ended, self-directed projects?",
        "Do you perform better with continuous assessment or high-stakes exams?",
        "Do you prefer small interactive classes or large lecture-based courses?",
        "Do you prefer interdisciplinary programs or a single focused major?",
        "How comfortable are you with online, hybrid, or remote learning compared with in-person learning?",
        "Would you prefer a standard-length program or flexible programs that let you change direction?",
    )),
    ("Support & constraints", (
        "Do family responsibilities affect your location, course length, or work-study choices?",
        "Do you have mentors or counsellors, and would you like to share recommendations with them?",
        "Are there timeline constraints for starting or finishing your studies?",
        "Do visa, immigration, or citizenship considerations affect where you can study or work?",
        "Is there anything else you want Career AI to know before it creates recommendations?",
    )),
)

SHORT_INTAKE = tuple((title, questions[0]) for title, questions in INTAKE_SECTIONS)
LONG_INTAKE = tuple((title, question) for title, questions in INTAKE_SECTIONS for question in questions)

RIASEC = {
    "R": ("Realistic", "🔧", ("I enjoy fixing or building things with my hands.", "I would rather work outdoors than sit in an office all day.", "I like understanding how machines, engines, or systems work.", "I prefer clear, practical tasks over abstract theory.", "I enjoy working with tools, equipment, or technology in a hands-on way.", "I like sports, physical activity, or working with my body.", "I would enjoy a job that involves building, repairing, or operating something.", "I prefer concrete results I can see and touch over abstract ideas.", "I am comfortable working in labs, workshops, or field settings.", "I like solving practical, real-world problems rather than theoretical ones.")),
    "I": ("Investigative", "🔬", ("I enjoy analyzing data, patterns, or complex problems.", "I like asking why and digging deep to understand root causes.", "I enjoy science subjects more than most.", "I would rather figure something out myself than be told the answer.", "I like reading research, studies, or in-depth articles on topics that interest me.", "I enjoy puzzles, logic problems, or strategy games.", "I am comfortable working with numbers, formulas, or statistics.", "I like designing experiments or testing hypotheses.", "I prefer careful, evidence-based reasoning over gut instinct.", "I would enjoy a career centered on research or discovery.")),
    "A": ("Artistic", "🎨", ("I enjoy expressing myself through writing, art, music, or design.", "I get bored with rigid rules and prefer creative freedom.", "I often come up with original or unconventional ideas.", "I enjoy imagining new possibilities more than following a set process.", "I like activities such as drawing, photography, film, theatre, or music.", "I value beauty, style, and aesthetics in things I create or use.", "I would enjoy a career that lets me express my own point of view.", "I prefer open-ended projects over highly structured ones.", "I enjoy storytelling through words, images, or performance.", "I like environments where non-traditional thinking is encouraged.")),
    "S": ("Social", "🤝", ("I enjoy helping people solve personal or academic problems.", "I find it rewarding to teach or explain something to someone else.", "I am good at listening to and understanding other people's feelings.", "I enjoy working in teams and collaborating with others.", "I would enjoy a career focused on healthcare, counselling, or education.", "People often come to me for advice or support.", "I care more about my work's impact on people than prestige or pay.", "I enjoy volunteering or community-oriented activities.", "I am comfortable resolving conflicts or mediating between people.", "I would rather work closely with people than alone with data or objects.")),
    "E": ("Enterprising", "🚀", ("I enjoy convincing or persuading others toward an idea or goal.", "I like taking charge and leading a group or project.", "I am comfortable with competition and enjoy trying to win.", "I would enjoy starting my own business or venture someday.", "I like setting ambitious goals and pushing to achieve them.", "I am comfortable with public speaking or presenting to a group.", "I enjoy negotiating deals or managing a team's decisions.", "I am motivated by status, achievement, or financial success.", "I like taking initiative rather than waiting to be told what to do.", "I would enjoy a career in business, law, politics, or sales or marketing.")),
    "C": ("Conventional", "📋", ("I enjoy organizing information, files, or schedules.", "I like following clear rules, processes, and procedures.", "I am detail-oriented and rarely miss small errors.", "I feel satisfied when things are neat, accurate, and well-structured.", "I am comfortable working with spreadsheets, records, or databases.", "I prefer predictable, well-defined tasks over ambiguous ones.", "I am reliable about deadlines, checklists, and routines.", "I would enjoy a career in accounting, administration, or operations.", "I like double-checking my work to make sure it is accurate.", "I am comfortable with repetitive tasks if they lead to a well-organized outcome.")),
}

RIASEC_QUESTIONS = tuple((code, statement) for code, (_, _, statements) in RIASEC.items() for statement in statements)
# Quick RIASEC: two representative statements from each of the six themes.
SHORT_RIASEC_QUESTIONS = tuple(
    (code, statement)
    for code, (_, _, statements) in RIASEC.items()
    for statement in statements[:2]
)

CAREER_MAP = {
    "R": ("Mechanical Engineer", "Architect", "Environmental Scientist"), "I": ("Data Scientist", "Software Engineer", "Physician"),
    "A": ("UX Designer", "Writer", "Animator"), "S": ("Psychologist", "Teacher", "Healthcare Professional"),
    "E": ("Entrepreneur", "Product Manager", "Lawyer"), "C": ("Data Analyst", "Accountant", "Operations Manager"),
    "RI": ("Robotics Engineer", "Cybersecurity Analyst", "Environmental Scientist"), "IA": ("UX Researcher", "Product Designer", "Science Journalist"),
    "AS": ("Art Therapist", "Communications Specialist", "Teacher"), "SE": ("HR Manager", "Corporate Trainer", "Nonprofit Director"),
    "EC": ("Financial Manager", "Supply Chain Manager", "Business Analyst"), "CI": ("Actuarial Analyst", "Statistician", "Risk Analyst"),
}

THEMES = {
    "Dark": {"bg":"radial-gradient(circle at 70% 2%,#34206c 0,#170b31 38%,#0d0820 100%)", "text":"#fbfaff", "muted":"#bdb4d4", "card":"linear-gradient(145deg,rgba(37,24,76,.96),rgba(16,10,42,.96))", "soft":"rgba(35,23,71,.84)", "line":"rgba(190,156,255,.22)", "sidebar":"#0d0824", "input":"rgba(13,8,32,.78)", "shadow":"rgba(0,0,0,.27)", "score":"linear-gradient(135deg,#4d26c5,#1e4eaa)", "mentor":"linear-gradient(145deg,rgba(69,29,93,.86),rgba(18,11,45,.96))"},
    "Light": {"bg":"radial-gradient(circle at 72% 5%,#fff 0,#f0edff 43%,#e5e0ff 100%)", "text":"#28184d", "muted":"#71628d", "card":"linear-gradient(145deg,rgba(255,255,255,.98),rgba(248,246,255,.98))", "soft":"rgba(255,255,255,.9)", "line":"rgba(124,58,237,.20)", "sidebar":"#201153", "input":"#fff", "shadow":"rgba(67,37,128,.12)", "score":"linear-gradient(135deg,#7542df,#5e94ef)", "mentor":"linear-gradient(145deg,#fff,#f8f5ff)"},
}


def init_state() -> None:
    defaults = {"app_stage":"login", "light_mode":False, "nav_page":"Dashboard", "student_name":"", "quiz_name":"", "intake_mode":None, "intake_index":0, "intake_answers":{}, "personality_mode":None, "personality_index":0, "personality_answers":{}, "personality_complete":False, "mentor_history":[]}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def theme_name() -> str:
    return "Light" if st.session_state.light_mode else "Dark"


def inject_styles() -> None:
    t = THEMES[theme_name()]
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root{{--bg:{t['bg']};--text:{t['text']};--muted:{t['muted']};--card:{t['card']};--soft:{t['soft']};--line:{t['line']};--sidebar:{t['sidebar']};--input:{t['input']};--shadow:{t['shadow']};--score:{t['score']};--mentor:{t['mentor']};--violet:#7c3aed;--pink:#ef5e7d;--mint:#15bfa2}} *{{font-family:'DM Sans',sans-serif}} .stApp{{background:var(--bg);color:var(--text)}} #MainMenu,footer{{visibility:hidden}} header{{background:transparent!important}} .block-container{{max-width:1500px;padding-top:1.5rem;padding-bottom:2.5rem}} [data-testid='stSidebar']{{background:var(--sidebar);border-right:1px solid rgba(211,193,255,.24)}} [data-testid='stSidebar'] *{{color:#f8f5ff!important}} h1,h2,h3{{font-family:'Space Grotesk',sans-serif;color:var(--text)}}
    .brand{{display:flex;align-items:center;gap:10px;margin:3px 0 20px}}.brand-name{{color:#fff;font:700 1.35rem 'Space Grotesk',sans-serif;white-space:nowrap}}.brand-name span{{color:#ff6b81}}.sidebar-tagline{{color:#cfc4eb;font-size:.73rem;white-space:nowrap}}.top-title{{font:700 2.25rem 'Space Grotesk',sans-serif;color:var(--text);letter-spacing:-1.4px;margin:0 0 3px}}.top-subtitle{{color:var(--muted);margin-bottom:18px}}.panel{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 15px 38px var(--shadow);box-sizing:border-box}}.panel h3{{margin:0 0 8px}}.muted{{color:var(--muted)!important}}.accent{{color:#8b5cf6;font-weight:700}}.mint{{color:var(--mint);font-weight:700}}
    .choice-card{{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:27px;min-height:250px;text-align:center;box-shadow:0 15px 38px var(--shadow)}}.choice-icon{{font-size:2.6rem;margin-bottom:9px}}.quiz-step{{color:#8b5cf6;font-size:.85rem;font-weight:700;margin-bottom:10px}}.question-card{{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:29px;box-shadow:0 15px 38px var(--shadow)}}.question-number{{color:#8b5cf6;font-weight:700}}.question-text{{font:600 1.6rem 'Space Grotesk',sans-serif;color:var(--text);line-height:1.35;margin:13px 0 21px}}.progress-shell{{height:8px;background:rgba(124,58,237,.16);border-radius:999px;overflow:hidden;margin:11px 0 25px}}.progress-fill{{height:100%;background:linear-gradient(90deg,#7c3aed,#ef5e7d);border-radius:999px}}.result-code{{font:700 3.2rem 'Space Grotesk',sans-serif;color:#8b5cf6;letter-spacing:4px}}.result-number{{font:700 2.7rem 'Space Grotesk',sans-serif;color:var(--text)}}.match-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}}.match-card{{background:var(--soft);border:1px solid var(--line);border-radius:13px;padding:15px;min-height:160px}}.match-pill{{float:right;color:var(--mint);background:rgba(21,191,162,.13);padding:4px 8px;border-radius:8px;font-size:.74rem;font-weight:700}}.icon-bubble{{width:43px;height:43px;display:grid;place-items:center;border-radius:14px;background:linear-gradient(145deg,rgba(255,255,255,.62),rgba(177,138,255,.28));border:1px solid rgba(255,255,255,.7);box-shadow:inset 0 1px rgba(255,255,255,.9),0 8px 17px rgba(70,35,155,.2);font-size:1.35rem}}.score-panel{{background:var(--score);border-radius:18px;padding:23px;color:#fff;min-height:228px}}.score-panel *{{color:#fff}}.big-score{{font:700 3.2rem 'Space Grotesk',sans-serif;margin:22px 0 8px}}.ai-card{{background:var(--mentor);border:1px solid rgba(236,91,122,.38);border-radius:18px;padding:20px;margin-bottom:17px}}.ai-card p{{color:var(--muted)}}
    .login-visual{{position:relative;min-height:610px;display:flex;align-items:center;justify-content:center;overflow:hidden}}.login-orbit{{position:absolute;width:470px;height:470px;border:1px dashed rgba(154,105,255,.34);border-radius:50%}}.login-message{{position:relative;z-index:2;max-width:500px;text-align:center;font:700 3.1rem/1.05 'Space Grotesk',sans-serif;color:var(--text);letter-spacing:-2px}}.login-message span{{color:#ef5e7d}}.float-career{{position:absolute;z-index:3;display:grid;place-items:center;width:93px;height:93px;border-radius:27px;border:1px solid var(--line);background:var(--soft);box-shadow:0 13px 32px var(--shadow);font-size:3rem;animation:career-drift 4s ease-in-out infinite}}.career-1{{top:48px;left:15%}}.career-2{{top:48px;right:15%;animation-delay:-1s}}.career-3{{top:235px;left:2%;animation-delay:-2s}}.career-4{{top:235px;right:2%;animation-delay:-.5s}}.career-5{{bottom:46px;left:17%;animation-delay:-2.5s}}.career-6{{bottom:46px;right:17%;animation-delay:-1.5s}}@keyframes career-drift{{50%{{transform:translateY(-12px) rotate(3deg)}}}}
    .st-key-ai_mentor_card{{background:var(--mentor);border:1px solid rgba(236,91,122,.44)!important;border-radius:17px;padding:12px 13px 16px;box-shadow:0 15px 38px var(--shadow);text-align:center}}[data-testid='stImage'] img{{filter:drop-shadow(0 0 7px rgba(163,99,255,.9)) drop-shadow(0 0 18px rgba(236,91,122,.42));animation:logo-glow 2.8s ease-in-out infinite}}@keyframes logo-glow{{50%{{filter:drop-shadow(0 0 12px rgba(181,114,255,1)) drop-shadow(0 0 30px rgba(255,91,141,.7))}}}}
    div[data-baseweb='input']>div,div[data-baseweb='textarea']>div{{background:var(--input)!important;border-color:var(--line)!important;color:var(--text)!important}}input,textarea{{color:var(--text)!important}}.stButton>button,button[kind='primary']{{background:linear-gradient(90deg,#7c3aed,#ef5e7d);color:#fff;border:1px solid rgba(255,255,255,.16);border-radius:12px;font-weight:700;min-height:43px;box-shadow:0 8px 18px rgba(95,45,199,.24);transition:.24s}}.stButton>button:hover,button[kind='primary']:hover{{transform:translateY(-2px);color:var(--text);background:linear-gradient(135deg,rgba(255,255,255,.35),rgba(181,143,255,.22));border-color:rgba(255,255,255,.68);box-shadow:inset 0 1px rgba(255,255,255,.82),0 12px 28px rgba(110,55,220,.32);backdrop-filter:blur(16px)}}[data-testid='stSidebar'] .stRadio label{{padding:7px 5px;border-radius:10px;background:linear-gradient(145deg,rgba(255,255,255,.1),rgba(145,98,255,.08));border:1px solid rgba(255,255,255,.1)}}
    @media(max-width:900px){{.block-container{{padding:1rem}}.match-grid{{grid-template-columns:1fr}}.top-title{{font-size:1.9rem}}.question-text{{font-size:1.3rem}}}}
    </style>""", unsafe_allow_html=True)


def reset_quiz(mode: str) -> None:
    st.session_state.intake_mode = mode
    st.session_state.intake_index = 0
    st.session_state.intake_answers = {}
    st.session_state.app_stage = "intake"


def start_personality(mode: str) -> None:
    st.session_state.personality_mode = mode
    st.session_state.personality_index = 0
    st.session_state.personality_answers = {}
    # Clear old widget values so a new quiz always starts fresh.
    for key in list(st.session_state):
        if key.startswith("radio_p_") or key.startswith("slider_p_"):
            del st.session_state[key]
    st.session_state.app_stage = "personality"


def intake_questions() -> tuple[tuple[str, str], ...]:
    return SHORT_INTAKE if st.session_state.intake_mode == "short" else LONG_INTAKE


def personality_questions() -> tuple[tuple[str, str], ...]:
    return SHORT_RIASEC_QUESTIONS if st.session_state.personality_mode == "riasec_short" else RIASEC_QUESTIONS


def riasec_scores() -> dict[str, int]:
    scores = {code: 0 for code in RIASEC}
    for index, (code, _) in enumerate(personality_questions()):
        scores[code] += int(st.session_state.personality_answers.get(f"p_{index}", 3))
    return scores


def career_suggestions() -> tuple[str, ...]:
    if not st.session_state.personality_complete:
        return ("UX Designer", "Data Analyst", "Clinical Psychologist")
    ranked = sorted(riasec_scores(), key=riasec_scores().get, reverse=True)
    code = "".join(ranked[:2])
    return CAREER_MAP.get(code) or CAREER_MAP.get(code[::-1]) or CAREER_MAP[ranked[0]]


def profile_name() -> str:
    return st.session_state.student_name or "Student"


def render_theme_toggle() -> None:
    _, col = st.columns([5, 1])
    with col:
        st.toggle("☀️ Light mode", key="light_mode")


def render_login() -> None:
    render_theme_toggle()
    left, right = st.columns([.92, 1.08], gap="large")
    with left:
        st.image(LOGO_PATH, width=86)
        st.markdown("<div class='panel'><div class='brand'><div class='brand-name'>Career <span>AI</span></div></div><h1 class='top-title'>Welcome back</h1><p class='top-subtitle'>Your future is waiting.</p>", unsafe_allow_html=True)
        username = st.text_input("Username or email", placeholder="Enter your username or email", key="username_input")
        st.text_input("Password", placeholder="Enter your password", type="password")
        st.checkbox("Remember me")
        if st.button("Sign in  →", use_container_width=True):
            st.session_state.student_name = username.split("@")[0].strip().title() or "Student"
            st.session_state.app_stage = "welcome"
            st.rerun()
        st.markdown("<p class='muted' style='text-align:center'>New to Career AI? <span class='accent'>Create an account</span></p></div>", unsafe_allow_html=True)
    with right:
        st.markdown("""
        <div class='login-visual'>
          <div class='login-orbit'></div>
          <div class='float-career career-1'>🩺</div>
          <div class='float-career career-2'>💻</div>
          <div class='float-career career-3'>🏏</div>
          <div class='float-career career-4'>🎓</div>
          <div class='float-career career-5'>🎨</div>
          <div class='float-career career-6'>🔬</div>
          <div class='login-message'>Every interest<br>can become a <span>future.</span></div>
        </div>
        """, unsafe_allow_html=True)


def render_welcome() -> None:
    render_theme_toggle()
    st.markdown(f"<div class='top-title'>Hello, {escape(profile_name())}! 👋</div><div class='top-subtitle'>Let’s start by learning what matters to you.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel' style='text-align:center;max-width:900px;margin:0 auto 23px'><div style='font-size:2.3rem'>✦</div><h2>“{random.choice(QUOTES)}”</h2><p class='muted'>Choose a quiz length. You can pause and return during this browser session.</p></div>", unsafe_allow_html=True)
    short, long = st.columns(2, gap="large")
    with short:
        st.markdown("<div class='choice-card'><div class='choice-icon'>⚡</div><h2>Quick Career Quiz</h2><p class='muted'>11 thoughtful questions — one from each important area. Great for a fast first recommendation.</p><p class='accent'>About 8–10 minutes</p></div>", unsafe_allow_html=True)
        st.button("Start quick quiz  →", use_container_width=True, on_click=reset_quiz, args=("short",))
    with long:
        st.markdown("<div class='choice-card'><div class='choice-icon'>🧭</div><h2>Complete Career Quiz</h2><p class='muted'>The full question bank covering academics, interests, skills, preferences, finances, and support needs.</p><p class='accent'>About 30–40 minutes</p></div>", unsafe_allow_html=True)
        st.button("Start complete quiz  →", use_container_width=True, on_click=reset_quiz, args=("long",))


def render_intake() -> None:
    render_theme_toggle()
    questions = intake_questions()
    index = st.session_state.intake_index
    section, prompt = questions[index]
    percent = round((index + 1) * 100 / len(questions))
    st.markdown(f"<div class='top-title'>Career Discovery Quiz</div><div class='top-subtitle'>{'Quick' if st.session_state.intake_mode == 'short' else 'Complete'} version · Answer honestly — there are no right answers.</div><div class='quiz-step'>{section}</div><div class='progress-shell'><div class='progress-fill' style='width:{percent}%'></div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='question-card'><div class='question-number'>QUESTION {index + 1} OF {len(questions)}</div><div class='question-text'>{escape(prompt)}</div>", unsafe_allow_html=True)
    quiz_name = st.session_state.student_name
    if index == 0:
        quiz_name = st.text_input(
            "What should we call you?",
            value=st.session_state.student_name,
            placeholder="Enter your name",
            key="quiz_display_name",
        )
    key = f"intake_{index}"
    answer = st.text_area("Your answer", value=st.session_state.intake_answers.get(key, ""), placeholder="Write your answer here…", height=175, key=f"widget_{key}")
    st.markdown("</div>", unsafe_allow_html=True)
    previous, spacer, next_col = st.columns([1, 2, 1])
    with previous:
        if index and st.button("← Previous", use_container_width=True):
            st.session_state.intake_answers[key] = answer
            st.session_state.intake_index -= 1
            st.rerun()
    with next_col:
        next_label = "Finish quiz  →" if index == len(questions) - 1 else "Next question  →"
        if st.button(next_label, use_container_width=True):
            if index == 0 and quiz_name.strip():
                st.session_state.student_name = quiz_name.strip().title()
            st.session_state.intake_answers[key] = answer.strip()
            if index == len(questions) - 1:
                st.session_state.app_stage = "intake_results"
            else:
                st.session_state.intake_index += 1
            st.rerun()


def render_intake_results() -> None:
    render_theme_toggle()
    answered = sum(bool(value.strip()) for value in st.session_state.intake_answers.values())
    total = len(intake_questions())
    st.markdown("<div class='top-title'>Your Career Profile is Ready</div><div class='top-subtitle'>Here is your first overall summary. Complete a personality quiz next for a deeper career-fit view.</div>", unsafe_allow_html=True)
    stat1, stat2, stat3 = st.columns(3)
    for col, icon, number, label in ((stat1, "✦", f"{answered}/{total}", "Questions answered"), (stat2, "🧭", "Career profile", "Saved in this session"), (stat3, "🧠", "Next: personality", "Refine your matches")):
        with col: st.markdown(f"<div class='panel' style='text-align:center'><div class='icon-bubble' style='margin:auto'>{icon}</div><div class='result-number'>{number}</div><p class='muted'>{label}</p></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:28px'>Refine your results with a RIASEC personality quiz</h2><p class='muted'>Choose one version. Both provide a Holland Code and career-family suggestions.</p>", unsafe_allow_html=True)
    short, long = st.columns(2, gap="large")
    with short:
        st.markdown("<div class='choice-card'><div class='choice-icon'>⚡</div><h2>Quick RIASEC Quiz</h2><p class='muted'>12 short statements — two for each career-interest theme. Get a fast career-direction summary.</p><p class='accent'>About 3–5 minutes</p></div>", unsafe_allow_html=True)
        st.button("Start quick RIASEC quiz  →", use_container_width=True, on_click=start_personality, args=("riasec_short",))
    with long:
        st.markdown("<div class='choice-card'><div class='choice-icon'>🧠</div><h2>Full RIASEC Quiz</h2><p class='muted'>60 statements measuring Realistic, Investigative, Artistic, Social, Enterprising, and Conventional themes.</p><p class='accent'>About 15–20 minutes</p></div>", unsafe_allow_html=True)
        st.button("Start full personality quiz  →", use_container_width=True, on_click=start_personality, args=("riasec_long",))
    if st.button("Skip for now and open dashboard", use_container_width=True):
        st.session_state.app_stage = "dashboard"
        st.rerun()


def render_personality() -> None:
    render_theme_toggle()
    questions = personality_questions()
    index = st.session_state.personality_index
    code, statement = questions[index]
    name, icon, _ = RIASEC[code]
    value_key = f"p_{index}"
    quiz_title = "Quick RIASEC Personality Quiz" if st.session_state.personality_mode == "riasec_short" else "Full RIASEC Personality Quiz"
    st.markdown(f"<div class='top-title'>{quiz_title}</div><div class='top-subtitle'>Rate each statement based on how you actually feel. 1 = strongly disagree · 5 = strongly agree.</div><div class='progress-shell'><div class='progress-fill' style='width:{round((index+1)*100/len(questions))}%'></div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='question-card'><div class='question-number'>{icon} {name.upper()} · QUESTION {index+1} OF {len(questions)}</div><div class='question-text'>{escape(statement)}</div>", unsafe_allow_html=True)
    value = st.radio("Your rating", (1, 2, 3, 4, 5), index=int(st.session_state.personality_answers.get(value_key, 3)) - 1, horizontal=True, format_func=lambda number: {1:"1 · Strongly disagree",2:"2 · Disagree",3:"3 · Neutral",4:"4 · Agree",5:"5 · Strongly agree"}[number], key=f"radio_{value_key}")
    st.markdown("</div>", unsafe_allow_html=True)
    previous, _, next_col = st.columns([1, 2, 1])
    with previous:
        if index and st.button("← Previous", use_container_width=True, key="personality_previous"):
            st.session_state.personality_answers[value_key] = value
            st.session_state.personality_index -= 1
            st.rerun()
    with next_col:
        final = index == len(questions) - 1
        if st.button("See results  →" if final else "Next question  →", use_container_width=True, key="personality_next"):
            st.session_state.personality_answers[value_key] = value
            if final:
                st.session_state.personality_complete = True
                st.session_state.app_stage = "personality_results"
            else:
                st.session_state.personality_index += 1
            st.rerun()


def render_personality_results() -> None:
    render_theme_toggle()
    scores = riasec_scores()
    ranked = sorted(scores, key=scores.get, reverse=True)
    code = "".join(ranked[:2])
    suggestions = career_suggestions()
    max_score = 10 if st.session_state.personality_mode == "riasec_short" else 50
    summary_title = "Your Quick RIASEC Career Profile" if st.session_state.personality_mode == "riasec_short" else "Your RIASEC Career Profile"
    st.markdown(f"<div class='top-title'>{summary_title}</div><div class='top-subtitle'>Your strongest themes point to work environments and career families that may feel naturally engaging.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel' style='text-align:center;max-width:780px;margin:0 auto 22px'><div class='result-code'>{code}</div><h2>{RIASEC[ranked[0]][1]} {RIASEC[ranked[0]][0]} + {RIASEC[ranked[1]][1]} {RIASEC[ranked[1]][0]}</h2><p class='muted'>Your Holland Code is a starting point for exploration, not a final decision.</p></div>", unsafe_allow_html=True)
    score_cols = st.columns(3)
    for col, type_code in zip(score_cols, ranked[:3]):
        with col:
            name, icon, _ = RIASEC[type_code]
            st.markdown(f"<div class='panel' style='text-align:center'><div class='icon-bubble' style='margin:auto'>{icon}</div><h3>{name}</h3><div class='result-number'>{scores[type_code]}/{max_score}</div></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:28px'>Career families to explore</h2>", unsafe_allow_html=True)
    st.markdown("<div class='match-grid'>" + "".join(f"<div class='match-card'><div class='icon-bubble'>✦</div><h3>{escape(career)}</h3><p class='muted'>Explore courses, skills, and university paths related to this direction.</p></div>" for career in suggestions) + "</div>", unsafe_allow_html=True)
    if st.button("Open my dashboard  →", use_container_width=True):
        st.session_state.app_stage = "dashboard"
        st.rerun()


def render_sidebar() -> str:
    with st.sidebar:
        logo_col, name_col = st.columns([.3, .7], gap="small")
        with logo_col: st.image(LOGO_PATH, width=62)
        with name_col: st.markdown("<div style='padding-top:3px'><div class='brand-name'>Career <span>AI</span></div><div class='sidebar-tagline'>Your AI Career Mentor</div></div>", unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("Navigation", PAGES, format_func=lambda p: f"{PAGE_ICONS[p]}  {p}", key="nav_page", label_visibility="collapsed")
        st.markdown("---")
        if st.button("Log out", use_container_width=True):
            st.session_state.app_stage = "login"
            st.session_state.nav_page = "Dashboard"
            st.rerun()
    return page


def render_dashboard() -> None:
    st.markdown(f"<div class='top-title'>Hello, {escape(profile_name())} 👋</div><div class='top-subtitle'>Here is your growing career profile.</div>", unsafe_allow_html=True)
    suggested = career_suggestions()
    score, matches, mentor = st.columns([1, 1.45, .7], gap="medium")
    with score: st.markdown("<div class='score-panel'><h3>Career Suitability Score</h3><div class='big-score'>88%</div><b>You’re on the right path!</b><p>Keep exploring to discover more opportunities.</p></div>", unsafe_allow_html=True)
    with matches:
        st.markdown("<div class='panel'><span class='accent' style='float:right'>View all →</span><h3>Top Career Matches</h3><div class='match-grid'>" + "".join(f"<div class='match-card'><span class='match-pill'>{92-index*3}%</span><div class='icon-bubble'>✦</div><h3>{escape(career)}</h3><p class='muted'>A promising direction based on your current profile.</p></div>" for index, career in enumerate(suggested)) + "</div></div>", unsafe_allow_html=True)
    with mentor:
        with st.container(border=True, key="ai_mentor_card"):
            st.markdown("### AI Mentor")
            _, logo, _ = st.columns([1, 1.4, 1])
            with logo: st.image(LOGO_PATH, use_container_width=True)
            st.markdown("**Ask your AI Mentor**")
            st.caption("Career and education guidance whenever you need it.")
            if st.button("Start a conversation", use_container_width=True): st.session_state.nav_page = "AI Mentor"; st.rerun()
    left, right = st.columns(2, gap="medium")
    with left: st.markdown("<div class='panel'><h3>🎓 Top Universities for You</h3><p class='muted'>IIT Bombay <span class='mint'>· Match 94%</span></p><p class='muted'>NID Ahmedabad <span class='mint'>· Match 91%</span></p><p class='muted'>Ashoka University <span class='mint'>· Match 88%</span></p></div>", unsafe_allow_html=True)
    with right: st.markdown("<div class='panel'><h3>✧ Your Learning Roadmap</h3><p class='mint'>● Self discovery</p><p class='muted'>○ Career exploration</p><p class='muted'>○ Skill building</p><p class='muted'>○ Real-world preparation</p></div>", unsafe_allow_html=True)


def mentor_reply(question: str) -> str:
    career_words = ("career","job","course","college","university","skill","scholarship","internship","study","degree","subject","resume","interview","education","salary","profession")
    if not any(word in question.lower() for word in career_words):
        return "I’m here specifically for career and education guidance. Please ask about careers, courses, skills, universities, scholarships, or internships."
    return "A useful next step is to compare your interests, strengths, entry requirements, and opportunities. I can help you explore relevant skills, courses, colleges, or career paths."


def render_ai_mentor() -> None:
    st.markdown("<div class='top-title'>AI Mentor</div><div class='top-subtitle'>Career and education guidance only.</div><div class='ai-card'><h3>Ask a career-focused question</h3><p>I can help with careers, skills, courses, universities, scholarships, and internships. For unrelated topics, I’ll politely guide you back.</p></div>", unsafe_allow_html=True)
    with st.form("mentor_form", clear_on_submit=True):
        question = st.text_input("Ask your question", placeholder="Which skills should I build for UX design?")
        asked = st.form_submit_button("Ask AI Mentor  →", use_container_width=True)
    if asked and question.strip(): st.session_state.mentor_history.append((question.strip(), mentor_reply(question.strip())))
    for question, answer in reversed(st.session_state.mentor_history[-5:]): st.markdown(f"<div class='panel'><b>You:</b> {escape(question)}<p class='muted'><b>Career AI:</b> {escape(answer)}</p></div>", unsafe_allow_html=True)


def render_simple_page(page: str) -> None:
    st.markdown(f"<div class='top-title'>{page}</div><div class='top-subtitle'>This section is ready for the next stage of your app.</div>", unsafe_allow_html=True)
    for row in range(2):
        cols = st.columns(3)
        for number, col in enumerate(cols, 1 + row * 3):
            with col: st.markdown(f"<div class='panel'><div class='icon-bubble'>✦</div><h3>{page} card {number}</h3><p class='muted'>Connect live recommendation data here later.</p></div>", unsafe_allow_html=True)


def render_app() -> None:
    render_theme_toggle()
    page = render_sidebar()
    if page == "Dashboard": render_dashboard()
    elif page == "AI Mentor": render_ai_mentor()
    else: render_simple_page(page)


def main() -> None:
    init_state()
    inject_styles()
    stage = st.session_state.app_stage
    if stage == "login": render_login()
    elif stage == "welcome": render_welcome()
    elif stage == "intake": render_intake()
    elif stage == "intake_results": render_intake_results()
    elif stage == "personality": render_personality()
    elif stage == "personality_results": render_personality_results()
    else: render_app()


if __name__ == "__main__":
    main()
