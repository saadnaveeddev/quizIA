"""
db.py — Database connection and query module.

Handles all SQLite operations: initialization, user management,
quiz result storage, and history retrieval.
"""

import sqlite3
import os
from datetime import datetime

# ── Path to the SQLite database file ──
DB_PATH = os.path.join(os.path.dirname(__file__), "quizia.db")


# ═══════════════════════════════════════════════════════
#  Connection helper
# ═══════════════════════════════════════════════════════

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row‑factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA foreign_keys = ON") # enforce FK constraints
    return conn


# ═══════════════════════════════════════════════════════
#  Schema initialisation
# ═══════════════════════════════════════════════════════

def init_db() -> None:
    """Create tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── users table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            email           TEXT    NOT NULL UNIQUE,
            password        TEXT    NOT NULL
        );
    """)

    # ── quiz_results table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id              INTEGER   PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER   NOT NULL,
            topic           TEXT      NOT NULL,
            difficulty      TEXT      NOT NULL,
            question_type   TEXT      NOT NULL DEFAULT 'mcq',
            score           INTEGER   NOT NULL,
            total_questions INTEGER   NOT NULL,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # ── answers table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id       INTEGER NOT NULL,
            question        TEXT    NOT NULL,
            user_answer     TEXT,
            correct_answer  TEXT    NOT NULL,
            is_correct      INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (result_id) REFERENCES quiz_results(id)
        );
    """)

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════
#  User operations
# ═══════════════════════════════════════════════════════

def user_exists(email: str) -> bool:
    """Check whether a user with the given email already exists."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(name: str, email: str, hashed_password: str) -> int:
    """Insert a new user and return the new user ID."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, hashed_password),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str) -> dict | None:
    """Fetch a user row by email. Returns dict or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════
#  Quiz‑result operations
# ═══════════════════════════════════════════════════════

def save_quiz_result(
    user_id: int,
    topic: str,
    difficulty: str,
    question_type: str,
    score: int,
    total_questions: int,
    answers_data: list[dict],
) -> int:
    """
    Persist a completed quiz attempt.

    Parameters
    ----------
    answers_data : list[dict]
        Each dict has keys: question, user_answer, correct_answer, is_correct
    
    Returns
    -------
    int  The ID of the newly created quiz_results row.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO quiz_results
           (user_id, topic, difficulty, question_type, score, total_questions)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, topic, difficulty, question_type, score, total_questions),
    )
    result_id = cursor.lastrowid

    for a in answers_data:
        cursor.execute(
            """INSERT INTO answers
               (result_id, question, user_answer, correct_answer, is_correct)
               VALUES (?, ?, ?, ?, ?)""",
            (
                result_id,
                a["question"],
                a.get("user_answer", ""),
                a["correct_answer"],
                int(a.get("is_correct", False)),
            ),
        )

    conn.commit()
    conn.close()
    return result_id


# ═══════════════════════════════════════════════════════
#  History / Dashboard queries
# ═══════════════════════════════════════════════════════

def get_quiz_history(user_id: int, limit: int = 50) -> list[dict]:
    """Return quiz results for a user, most recent first."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM quiz_results
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_answers_for_result(result_id: int) -> list[dict]:
    """Return all saved answers for a specific quiz attempt."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM answers WHERE result_id = ?", (result_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats(user_id: int) -> dict:
    """
    Aggregate dashboard statistics for a user.

    Returns
    -------
    dict with keys: total_quizzes, average_score, average_percentage,
                    last_5_attempts, performance_label
    """
    conn = get_connection()

    # Total quizzes
    total = conn.execute(
        "SELECT COUNT(*) AS cnt FROM quiz_results WHERE user_id = ?",
        (user_id,),
    ).fetchone()["cnt"]

    # Average percentage
    avg_row = conn.execute(
        """SELECT AVG(CAST(score AS REAL) / total_questions * 100) AS avg_pct
           FROM quiz_results WHERE user_id = ?""",
        (user_id,),
    ).fetchone()
    avg_pct = round(avg_row["avg_pct"], 1) if avg_row["avg_pct"] else 0.0

    # Last 5 attempts
    last_5 = conn.execute(
        """SELECT * FROM quiz_results
           WHERE user_id = ?
           ORDER BY created_at DESC LIMIT 5""",
        (user_id,),
    ).fetchall()

    conn.close()

    # Performance label
    if avg_pct >= 80:
        label = "Strong"
    elif avg_pct >= 50:
        label = "Moderate"
    else:
        label = "Needs Improvement"

    return {
        "total_quizzes": total,
        "average_percentage": avg_pct,
        "last_5_attempts": [dict(r) for r in last_5],
        "performance_label": label,
    }
