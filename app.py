"""
app.py — Main Streamlit entry‑point for QuizIA.

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

# ═══════════════════════════════════════════════════════
#  Page config & DB init
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="QuizIA — Math Competency Evaluator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()  # idempotent — safe to call every reload


# ═══════════════════════════════════════════════════════
#  Custom CSS for a polished look
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Global tweaks ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Metric cards ── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
div[data-testid="stMetric"] label { color: #a0a0c0 !important; font-size: 0.85rem; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
}
section[data-testid="stSidebar"] .stRadio label { font-weight: 500; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.35);
}

/* ── Quiz card style ── */
.quiz-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* ── Result banner ── */
.result-banner {
    text-align: center;
    padding: 32px;
    border-radius: 16px;
    margin-bottom: 24px;
}
.result-banner.strong  { background: linear-gradient(135deg, #064e3b, #065f46); }
.result-banner.moderate { background: linear-gradient(135deg, #78350f, #92400e); }
.result-banner.weak    { background: linear-gradient(135deg, #7f1d1d, #991b1b); }

/* ── History table ── */
.history-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Session‑state defaults
# ═══════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════
#  Sidebar navigation
# ═══════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🧮 QuizIA")
    st.caption("AI‑Powered Math Competency Evaluator")
    st.divider()

    if st.session_state.logged_in:
        st.success(f"👋  Hi, **{st.session_state.user['name']}**!")
        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "📝 Start Quiz", "📊 History"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in DEFAULTS:
                st.session_state[k] = DEFAULTS[k]
            st.rerun()
    else:
        page = "Login / Signup"
        st.info("Please log in or create an account.")


# ═══════════════════════════════════════════════════════
#  PAGE: Login / Signup
# ═══════════════════════════════════════════════════════

def render_auth_page():
    st.markdown("# 🧮 Welcome to QuizIA")
    st.markdown("##### Test your mathematics skills with AI‑generated quizzes")
    st.write("")

    tab_login, tab_signup = st.tabs(["🔑 Login", "📋 Sign Up"])

    # ── Login tab ──
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            ok, msg, user = auth.login(email, password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.toast("✅ " + msg, icon="🎉")
                st.rerun()
            else:
                st.error(msg)

    # ── Signup tab ──
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="Jane Doe")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, msg = auth.signup(name, email, password)
                if ok:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)


# ═══════════════════════════════════════════════════════
#  PAGE: Dashboard
# ═══════════════════════════════════════════════════════

def render_dashboard():
    st.markdown("# 🏠 Dashboard")
    stats = db.get_dashboard_stats(st.session_state.user["id"])

    # ── Top metrics ──
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Quizzes", stats["total_quizzes"])
    c2.metric("Avg. Score", f"{stats['average_percentage']}%")
    c3.metric("Performance", stats["performance_label"])

    st.divider()

    # ── Last 5 attempts ──
    st.markdown("### 📋 Recent Attempts")
    attempts = stats["last_5_attempts"]
    if not attempts:
        st.info("You haven't taken any quizzes yet. Head over to **Start Quiz** to begin!")
        return

    for a in attempts:
        pct = percentage(a["score"], a["total_questions"])
        label = performance_label(pct)
        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1.5])
        col1.markdown(f"**{a['topic']}**")
        col2.caption(f"🎯 {a['difficulty']} · {a.get('question_type', 'mcq').upper()}")
        col3.markdown(f"`{a['score']}/{a['total_questions']}`")
        col4.markdown(f"**{pct}%**")
        col5.caption(f"🕑 {a['created_at']}")
        st.divider()


# ═══════════════════════════════════════════════════════
#  PAGE: Start Quiz — config → attempt → results
# ═══════════════════════════════════════════════════════

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
Q_TYPES = {"MCQs": "mcq", "Short Answer": "short_answer"}


def render_quiz_page():
    # ── If results exist, show them ──
    if st.session_state.quiz_submitted and st.session_state.quiz_result:
        render_results()
        return

    # ── If questions already generated, show the attempt form ──
    if st.session_state.questions is not None:
        render_quiz_attempt()
        return

    # ── Otherwise show configuration form ──
    st.markdown("# 📝 Configure Your Quiz")
    st.markdown("Choose your settings and let the AI craft a unique quiz for you.")
    st.write("")

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        topic = st.selectbox("📚 Topic", TOPICS)
        difficulty = st.select_slider(
            "🎚️ Difficulty",
            options=DIFFICULTIES,
            value="Medium",
        )

    with col_right:
        q_type_label = st.radio("❓ Question Type", list(Q_TYPES.keys()), horizontal=True)
        num_q = st.slider("🔢 Number of Questions", min_value=3, max_value=20, value=5)

    st.write("")
    generate_btn = st.button("🚀 Generate Quiz", use_container_width=True, type="primary")

    if generate_btn:
        q_type = Q_TYPES[q_type_label]
        with st.spinner("🤖 AI is crafting your quiz — hang tight…"):
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
                st.error(f"⚠️ Failed to generate quiz: {e}")


def render_quiz_attempt():
    """Render the quiz questions and collect user answers."""
    config = st.session_state.quiz_config
    questions = st.session_state.questions
    q_type = config["question_type"]

    st.markdown(f"# 📝 {config['topic']}  —  {config['difficulty']}")
    st.caption(f"{'Multiple Choice' if q_type == 'mcq' else 'Short Answer'}  ·  {len(questions)} questions")
    st.divider()

    # Store answers in a form so the user can submit all at once
    with st.form("quiz_attempt_form"):
        user_answers = []

        for i, q in enumerate(questions, start=1):
            st.markdown(f"### Q{i}. {q['question']}")

            if q_type == "mcq":
                options = q.get("options", [])
                answer = st.radio(
                    f"Select your answer for Q{i}",
                    options,
                    key=f"q_{i}",
                    label_visibility="collapsed",
                )
                user_answers.append(answer if answer else "")
            else:
                answer = st.text_input(
                    f"Your answer for Q{i}",
                    key=f"q_{i}",
                    placeholder="Type your answer here…",
                    label_visibility="collapsed",
                )
                user_answers.append(answer)

            st.divider()

        col_submit, col_cancel = st.columns(2)
        submitted = col_submit.form_submit_button(
            "✅ Submit Answers", use_container_width=True, type="primary"
        )
        cancelled = col_cancel.form_submit_button(
            "❌ Cancel Quiz", use_container_width=True
        )

    if submitted:
        with st.spinner("📊 Grading your answers…"):
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

    # ── Banner ──
    if pct >= 80:
        banner_cls = "strong"
        emoji = "🏆"
        headline = "Excellent Work!"
    elif pct >= 50:
        banner_cls = "moderate"
        emoji = "👍"
        headline = "Good Effort!"
    else:
        banner_cls = "weak"
        emoji = "💪"
        headline = "Keep Practicing!"

    st.markdown(
        f"""
        <div class="result-banner {banner_cls}">
            <h1 style="margin:0;font-size:2.5rem;">{emoji} {headline}</h1>
            <p style="font-size:1.3rem;margin-top:8px;opacity:0.9;">
                You scored <strong>{result['score']}/{result['total']}</strong>
                — <strong>{pct}%</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Per‑question breakdown ──
    st.markdown("### 📋 Detailed Breakdown")
    for i, a in enumerate(result["answers"], start=1):
        icon = "✅" if a["is_correct"] else "❌"
        with st.expander(f"{icon}  Q{i}: {a['question']}", expanded=not a['is_correct']):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Your Answer:** {a['user_answer'] or '*(no answer)*'}")
            c2.markdown(f"**Correct Answer:** {a['correct_answer']}")

    st.write("")

    # ── Action buttons ──
    col_a, col_b = st.columns(2)
    if col_a.button("🔄 Take Another Quiz", use_container_width=True, type="primary"):
        st.session_state.questions = None
        st.session_state.quiz_config = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_result = None
        st.rerun()
    if col_b.button("🏠 Go to Dashboard", use_container_width=True):
        st.session_state.questions = None
        st.session_state.quiz_config = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_result = None
        st.rerun()


# ═══════════════════════════════════════════════════════
#  PAGE: History
# ═══════════════════════════════════════════════════════

def render_history():
    st.markdown("# 📊 Quiz History")

    history = db.get_quiz_history(st.session_state.user["id"])
    if not history:
        st.info("No quiz history yet. Go take a quiz!")
        return

    for entry in history:
        pct = percentage(entry["score"], entry["total_questions"])
        label = performance_label(pct)

        with st.expander(
            f"**{entry['topic']}**  |  {entry['difficulty']}  |  "
            f"{entry['score']}/{entry['total_questions']}  ({pct}%)  {label}  —  "
            f"{entry['created_at']}"
        ):
            answers = db.get_answers_for_result(entry["id"])
            if not answers:
                st.caption("No answer details saved.")
                continue
            for j, a in enumerate(answers, 1):
                icon = "✅" if a["is_correct"] else "❌"
                st.markdown(f"**{icon} Q{j}.** {a['question']}")
                c1, c2 = st.columns(2)
                c1.caption(f"Your answer: {a['user_answer'] or '—'}")
                c2.caption(f"Correct: {a['correct_answer']}")
            st.divider()


# ═══════════════════════════════════════════════════════
#  Router
# ═══════════════════════════════════════════════════════

if not st.session_state.logged_in:
    render_auth_page()
elif page == "🏠 Dashboard":
    render_dashboard()
elif page == "📝 Start Quiz":
    render_quiz_page()
elif page == "📊 History":
    render_history()
