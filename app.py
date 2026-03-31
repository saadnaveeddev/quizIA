"""
app.py — Main Streamlit entry-point for QuizIA.

Handles page routing, sidebar navigation, session state,
and renders each screen (auth, quiz, results, dashboard).

Run with:
    streamlit run app.py
"""

import streamlit as st
import db
import auth
import quiz as quiz_module
from utils import percentage, performance_label

# ===================================================================
#  Page config & DB init
# ===================================================================

st.set_page_config(
    page_title="QuizIA  |  Math Competency Evaluator",
    page_icon="Q",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()


# ===================================================================
#  Design System  (Custom CSS)
# ===================================================================

st.markdown("""
<style>
/* ----------------------------------------------------------------
   0.  IMPORTS & RESET
   ---------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ----------------------------------------------------------------
   1.  COLOR TOKENS  (CSS custom properties)
   ---------------------------------------------------------------- */
:root {
    --bg-primary:     #0b0f19;
    --bg-secondary:   #111827;
    --bg-card:        #151c2c;
    --bg-card-hover:  #1a2236;
    --border-subtle:  rgba(148, 163, 184, 0.08);
    --border-medium:  rgba(148, 163, 184, 0.14);
    --text-primary:   #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted:     #64748b;
    --accent:         #6366f1;
    --accent-light:   #818cf8;
    --accent-glow:    rgba(99, 102, 241, 0.25);
    --success:        #22c55e;
    --success-bg:     rgba(34, 197, 94, 0.08);
    --warning:        #f59e0b;
    --warning-bg:     rgba(245, 158, 11, 0.08);
    --danger:         #ef4444;
    --danger-bg:      rgba(239, 68, 68, 0.08);
    --radius-sm:      8px;
    --radius-md:      12px;
    --radius-lg:      16px;
}

/* ----------------------------------------------------------------
   2.  SIDEBAR
   ---------------------------------------------------------------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
    border-right: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] .stRadio > label {
    font-weight: 500;
    letter-spacing: 0.01em;
}

/* ----------------------------------------------------------------
   3.  METRIC CARDS
   ---------------------------------------------------------------- */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: var(--border-medium);
    box-shadow: 0 2px 6px rgba(0,0,0,0.16), 0 8px 24px rgba(0,0,0,0.12);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

/* ----------------------------------------------------------------
   4.  BUTTONS
   ---------------------------------------------------------------- */
.stButton > button {
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border-subtle) !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px var(--accent-glow);
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stFormSubmitButton"] {
    background: linear-gradient(135deg, var(--accent) 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
}

/* ----------------------------------------------------------------
   5.  FORM INPUTS
   ---------------------------------------------------------------- */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea textarea {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-medium) !important;
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
div[data-testid="InputInstructions"] {
    display: none !important;
}

/* ----------------------------------------------------------------
   6.  TABS
   ---------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--bg-card);
    border-radius: var(--radius-md);
    padding: 4px;
    border: 1px solid var(--border-subtle);
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm);
    font-weight: 500;
    color: var(--text-secondary);
    padding: 10px 24px;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ----------------------------------------------------------------
   7.  EXPANDER
   ---------------------------------------------------------------- */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border-radius: var(--radius-md) !important;
}
details[data-testid="stExpander"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-card) !important;
    margin-bottom: 8px;
}

/* ----------------------------------------------------------------
   8.  CUSTOM COMPONENT CLASSES
   ---------------------------------------------------------------- */

/* -- Page header -- */
.page-header {
    margin-bottom: 8px;
}
.page-header h1 {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    letter-spacing: -0.02em;
}
.page-header p {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 4px;
}

/* -- Stat card (HTML-based) -- */
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 22px 24px;
    transition: all 0.25s ease;
}
.stat-card:hover {
    border-color: var(--border-medium);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.stat-card .stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 6px;
}
.stat-card .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}
.stat-card .stat-sub {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 4px;
}
.stat-card.accent  { border-left: 3px solid var(--accent); }
.stat-card.success { border-left: 3px solid var(--success); }
.stat-card.warning { border-left: 3px solid var(--warning); }

/* -- Result banner -- */
.result-banner {
    text-align: center;
    padding: 36px 24px;
    border-radius: var(--radius-lg);
    margin-bottom: 28px;
    border: 1px solid var(--border-subtle);
}
.result-banner h2 {
    margin: 0 0 6px 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
}
.result-banner p {
    margin: 0;
    font-size: 1.05rem;
    color: var(--text-secondary);
}
.result-banner.excellent {
    background: linear-gradient(135deg, rgba(34,197,94,0.12) 0%, rgba(16,185,129,0.06) 100%);
    border-color: rgba(34,197,94,0.2);
}
.result-banner.good {
    background: linear-gradient(135deg, rgba(245,158,11,0.12) 0%, rgba(217,119,6,0.06) 100%);
    border-color: rgba(245,158,11,0.2);
}
.result-banner.weak {
    background: linear-gradient(135deg, rgba(239,68,68,0.10) 0%, rgba(220,38,38,0.05) 100%);
    border-color: rgba(239,68,68,0.2);
}

/* -- Quiz question card -- */
.question-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 16px;
}
.question-card .q-number {
    display: inline-block;
    background: var(--accent);
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 10px;
}

/* -- History row card -- */
.history-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 20px;
    border-radius: var(--radius-md);
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    margin-bottom: 8px;
    transition: border-color 0.2s ease;
}
.history-card:hover { border-color: var(--border-medium); }

/* -- Auth container -- */
.auth-container {
    max-width: 460px;
    margin: 0 auto;
    padding-top: 32px;
}
.auth-header {
    text-align: center;
    margin-bottom: 32px;
}
.auth-header h1 {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0 0 4px 0;
    letter-spacing: -0.03em;
}
.auth-header .brand-accent {
    color: var(--accent-light);
}
.auth-header p {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin: 0;
}

/* -- Badge/pill -- */
.badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 3px 10px;
    border-radius: 20px;
}
.badge-success { background: var(--success-bg); color: var(--success); }
.badge-warning { background: var(--warning-bg); color: var(--warning); }
.badge-danger  { background: var(--danger-bg);  color: var(--danger); }
.badge-accent  { background: var(--accent-glow); color: var(--accent-light); }

/* -- Answer breakdown -- */
.answer-correct {
    border-left: 3px solid var(--success);
    background: var(--success-bg);
    padding: 12px 16px;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin-bottom: 6px;
}
.answer-wrong {
    border-left: 3px solid var(--danger);
    background: var(--danger-bg);
    padding: 12px 16px;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin-bottom: 6px;
}

/* -- Divider override -- */
hr {
    border-color: var(--border-subtle) !important;
    margin: 20px 0 !important;
}

/* -- Logo text -- */
.logo-text {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text-primary);
}
.logo-text span {
    color: var(--accent-light);
}

/* -- Sidebar user card -- */
.sidebar-user {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 14px 16px;
    margin-bottom: 12px;
}
.sidebar-user .user-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
}
.sidebar-user .user-email {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* -- Empty state -- */
.empty-state {
    text-align: center;
    padding: 48px 24px;
    color: var(--text-secondary);
}
.empty-state h3 {
    color: var(--text-primary);
    font-weight: 600;
    margin-bottom: 8px;
}
.empty-state p {
    color: var(--text-muted);
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)


# ===================================================================
#  Session-state defaults
# ===================================================================

DEFAULTS = {
    "logged_in": False,
    "user": None,
    "page": "Login / Signup",
    "questions": None,
    "quiz_config": None,
    "quiz_submitted": False,
    "quiz_result": None,
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ===================================================================
#  Sidebar navigation
# ===================================================================

with st.sidebar:
    st.markdown('<div class="logo-text">Quiz<span>IA</span></div>', unsafe_allow_html=True)
    st.caption("Math Competency Evaluator")
    st.divider()

    if st.session_state.logged_in:
        user = st.session_state.user
        st.markdown(
            f"""<div class="sidebar-user">
                <div class="user-name">{user['name']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigate",
            ["Dashboard", "Start Quiz", "History"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Logout", use_container_width=True):
            for k in DEFAULTS:
                st.session_state[k] = DEFAULTS[k]
            st.rerun()
    else:
        page = "Login / Signup"
        st.info("Sign in to access your quizzes.")


# ===================================================================
#  PAGE: Login / Signup
# ===================================================================

def render_auth_page():
    st.markdown(
        """<div class="auth-header">
            <h1>Quiz<span class="brand-accent">IA</span></h1>
            <p>Evaluate your mathematics competency with AI-generated quizzes</p>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # -- Login tab --
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            st.write("")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            ok, msg, user = auth.login(email, password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.toast(msg)
                st.rerun()
            else:
                st.error(msg)

    # -- Signup tab --
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full name", placeholder="Jane Doe")
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            st.write("")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, msg = auth.signup(name, email, password)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


# ===================================================================
#  PAGE: Dashboard
# ===================================================================

def _performance_badge(label: str) -> str:
    """Return an HTML badge string for a performance label."""
    if label == "Strong":
        return '<span class="badge badge-success">Strong</span>'
    elif label == "Moderate":
        return '<span class="badge badge-warning">Moderate</span>'
    else:
        return '<span class="badge badge-danger">Needs Improvement</span>'


def render_dashboard():
    st.markdown(
        '<div class="page-header"><h1>Dashboard</h1>'
        "<p>Your quiz performance at a glance</p></div>",
        unsafe_allow_html=True,
    )

    stats = db.get_dashboard_stats(st.session_state.user["id"])

    # -- Stat cards (HTML) --
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="stat-card accent">
                <div class="stat-label">Total Quizzes</div>
                <div class="stat-value">{stats['total_quizzes']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="stat-card success">
                <div class="stat-label">Average Score</div>
                <div class="stat-value">{stats['average_percentage']}%</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        badge = _performance_badge(stats["performance_label"])
        st.markdown(
            f"""<div class="stat-card warning">
                <div class="stat-label">Performance</div>
                <div class="stat-value" style="font-size:1.1rem;margin-top:6px;">{badge}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    # -- Recent attempts --
    st.markdown("#### Recent Attempts")
    attempts = stats["last_5_attempts"]
    if not attempts:
        st.markdown(
            """<div class="empty-state">
                <h3>No quizzes yet</h3>
                <p>Head over to Start Quiz to take your first assessment.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    for a in attempts:
        pct = percentage(a["score"], a["total_questions"])
        label = performance_label(pct)
        badge = _performance_badge(label)
        q_type = a.get("question_type", "mcq").upper()

        col1, col2, col3, col4, col5 = st.columns([2.2, 1.5, 0.8, 0.8, 1.5])
        col1.markdown(f"**{a['topic']}**")
        col2.caption(f"{a['difficulty']}  |  {q_type}")
        col3.markdown(f"`{a['score']}/{a['total_questions']}`")
        col4.markdown(f"**{pct}%**")
        col5.caption(f"{a['created_at']}")
        st.divider()


# ===================================================================
#  PAGE: Start Quiz  (config -> attempt -> results)
# ===================================================================

TOPICS = [
    "Linear Algebra",
    "Probability & Statistics",
    "Calculus",
    "Discrete Mathematics",
    "Number Theory",
    "Set Theory",
    "Graph Theory",
    "Boolean Algebra",
    "Combinatorics",
    "Differential Equations",
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]
Q_TYPES = {"Multiple Choice": "mcq", "Short Answer": "short_answer"}


def render_quiz_page():
    # -- If results exist, show them --
    if st.session_state.quiz_submitted and st.session_state.quiz_result:
        render_results()
        return

    # -- If questions already generated, show the attempt form --
    if st.session_state.questions is not None:
        render_quiz_attempt()
        return

    # -- Otherwise show configuration form --
    st.markdown(
        '<div class="page-header"><h1>Configure Your Quiz</h1>'
        "<p>Select your preferences and let AI generate a tailored assessment</p></div>",
        unsafe_allow_html=True,
    )
    st.write("")

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        topic = st.selectbox("Topic", TOPICS)
        difficulty = st.select_slider(
            "Difficulty",
            options=DIFFICULTIES,
            value="Medium",
        )

    with col_right:
        q_type_label = st.radio("Question Type", list(Q_TYPES.keys()), horizontal=True)
        num_q = st.slider("Number of Questions", min_value=3, max_value=20, value=5)

    st.write("")
    generate_btn = st.button("Generate Quiz", use_container_width=True, type="primary")

    if generate_btn:
        q_type = Q_TYPES[q_type_label]
        with st.spinner("Generating your quiz..."):
            try:
                questions = quiz_module.generate_quiz(topic, difficulty, num_q, q_type)
                st.session_state.questions = questions
                st.session_state.quiz_config = {
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_type": q_type,
                }
                st.session_state.quiz_submitted = False
                st.session_state.quiz_result = None
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate quiz: {e}")


def render_quiz_attempt():
    """Render the quiz questions and collect user answers."""
    config = st.session_state.quiz_config
    questions = st.session_state.questions
    q_type = config["question_type"]

    type_label = "Multiple Choice" if q_type == "mcq" else "Short Answer"

    st.markdown(
        f'<div class="page-header"><h1>{config["topic"]}</h1>'
        f'<p>{config["difficulty"]}  |  {type_label}  |  {len(questions)} questions</p></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    with st.form("quiz_attempt_form"):
        user_answers = []

        for i, q in enumerate(questions, start=1):
            st.markdown(f"**Question {i}**")
            st.markdown(q["question"])

            if q_type == "mcq":
                options = q.get("options", [])
                answer = st.radio(
                    f"Select answer for Question {i}",
                    options,
                    key=f"q_{i}",
                    label_visibility="collapsed",
                )
                user_answers.append(answer if answer else "")
            else:
                answer = st.text_input(
                    f"Your answer for Question {i}",
                    key=f"q_{i}",
                    placeholder="Type your answer here...",
                    label_visibility="collapsed",
                )
                user_answers.append(answer)

            st.divider()

        col_submit, col_cancel = st.columns(2)
        submitted = col_submit.form_submit_button(
            "Submit Answers", use_container_width=True, type="primary"
        )
        cancelled = col_cancel.form_submit_button(
            "Cancel Quiz", use_container_width=True
        )

    if submitted:
        with st.spinner("Grading your answers..."):
            result = quiz_module.evaluate_and_save(
                user_id=st.session_state.user["id"],
                topic=config["topic"],
                difficulty=config["difficulty"],
                question_type=config["question_type"],
                questions=questions,
                user_answers=user_answers,
            )
        st.session_state.quiz_submitted = True
        st.session_state.quiz_result = result
        st.rerun()

    if cancelled:
        st.session_state.questions = None
        st.session_state.quiz_config = None
        st.rerun()


def render_results():
    """Display grading results after a quiz submission."""
    result = st.session_state.quiz_result
    config = st.session_state.quiz_config
    pct = result["percentage"]

    # -- Banner --
    if pct >= 80:
        banner_cls = "excellent"
        headline = "Excellent Work"
    elif pct >= 50:
        banner_cls = "good"
        headline = "Good Effort"
    else:
        banner_cls = "weak"
        headline = "Keep Practicing"

    st.markdown(
        f"""<div class="result-banner {banner_cls}">
            <h2>{headline}</h2>
            <p>You scored <strong>{result['score']}/{result['total']}</strong>
            &mdash; <strong>{pct}%</strong></p>
        </div>""",
        unsafe_allow_html=True,
    )

    # -- Per-question breakdown --
    st.markdown("#### Detailed Breakdown")
    for i, a in enumerate(result["answers"], start=1):
        is_correct = a["is_correct"]
        status = "Correct" if is_correct else "Incorrect"
        css_class = "answer-correct" if is_correct else "answer-wrong"

        with st.expander(f"Question {i}: {status} — {a['question']}", expanded=not is_correct):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Your answer:** {a['user_answer'] or '*(no answer)*'}")
            c2.markdown(f"**Correct answer:** {a['correct_answer']}")

    st.write("")

    # -- Action buttons --
    col_a, col_b = st.columns(2)
    if col_a.button("Take Another Quiz", use_container_width=True, type="primary"):
        st.session_state.questions = None
        st.session_state.quiz_config = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_result = None
        st.rerun()
    if col_b.button("Go to Dashboard", use_container_width=True):
        st.session_state.questions = None
        st.session_state.quiz_config = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_result = None
        st.rerun()


# ===================================================================
#  PAGE: History
# ===================================================================

def render_history():
    st.markdown(
        '<div class="page-header"><h1>Quiz History</h1>'
        "<p>Review all your past quiz attempts</p></div>",
        unsafe_allow_html=True,
    )

    history = db.get_quiz_history(st.session_state.user["id"])
    if not history:
        st.markdown(
            """<div class="empty-state">
                <h3>No history yet</h3>
                <p>Complete a quiz to see your results here.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    for entry in history:
        pct = percentage(entry["score"], entry["total_questions"])
        label = performance_label(pct)
        badge = _performance_badge(label)

        with st.expander(
            f"{entry['topic']}  |  {entry['difficulty']}  |  "
            f"{entry['score']}/{entry['total_questions']}  ({pct}%)  "
            f"{label}  |  {entry['created_at']}"
        ):
            answers = db.get_answers_for_result(entry["id"])
            if not answers:
                st.caption("No answer details saved.")
                continue
            for j, a in enumerate(answers, 1):
                status_class = "answer-correct" if a["is_correct"] else "answer-wrong"
                status_text = "Correct" if a["is_correct"] else "Incorrect"
                st.markdown(
                    f'<div class="{status_class}">'
                    f"<strong>Q{j}.</strong> {a['question']}<br>"
                    f'<span style="font-size:0.85rem;color:var(--text-secondary);">'
                    f"Your answer: {a['user_answer'] or '—'}  |  "
                    f"Correct: {a['correct_answer']}</span></div>",
                    unsafe_allow_html=True,
                )


# ===================================================================
#  Router
# ===================================================================

if not st.session_state.logged_in:
    render_auth_page()
elif page == "Dashboard":
    render_dashboard()
elif page == "Start Quiz":
    render_quiz_page()
elif page == "History":
    render_history()
