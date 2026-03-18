"""
quiz.py — Quiz generation, grading, and persistence logic.

Orchestrates the AI provider, parses the returned JSON,
grades user answers, and saves everything to the database.
"""

from api_client import get_ai_provider, AIProvider
from utils import extract_json_from_text, percentage
import db


# ═══════════════════════════════════════════════════════
#  Singleton‑ish provider (cached per session)
# ═══════════════════════════════════════════════════════

_provider_cache: AIProvider | None = None


def _get_provider() -> AIProvider:
    """Return a cached AI provider instance."""
    global _provider_cache
    if _provider_cache is None:
        _provider_cache = get_ai_provider()
    return _provider_cache


# ═══════════════════════════════════════════════════════
#  Question generation
# ═══════════════════════════════════════════════════════

def generate_quiz(
    topic: str,
    difficulty: str,
    num_questions: int,
    question_type: str,
) -> list[dict]:
    """
    Call the AI provider and return a list of question dicts.

    For MCQs each dict has:
        question, options, correct_answer

    For short‑answer each dict has:
        question, correct_answer

    Raises ValueError if the AI response cannot be parsed.
    """
    provider = _get_provider()
    raw = provider.generate_questions(topic, difficulty, num_questions, question_type)

    parsed = extract_json_from_text(raw)
    if parsed is None:
        raise ValueError(
            "The AI returned an unparsable response. Please try again."
        )

    # The JSON may be {"questions": [...]} or just [...]
    if isinstance(parsed, dict) and "questions" in parsed:
        questions = parsed["questions"]
    elif isinstance(parsed, list):
        questions = parsed
    else:
        raise ValueError("Unexpected JSON structure from AI.")

    if not questions:
        raise ValueError("AI returned an empty question list.")

    return questions


# ═══════════════════════════════════════════════════════
#  Grading
# ═══════════════════════════════════════════════════════

def grade_mcq(questions: list[dict], user_answers: list[str]) -> list[dict]:
    """
    Grade MCQ answers by exact letter match.

    Returns a list of answer dicts ready for database storage:
        [{ question, user_answer, correct_answer, is_correct }, ...]
    """
    results = []
    for q, ua in zip(questions, user_answers):
        correct = q["correct_answer"].strip().upper()
        # Extract just the letter from "A) ..." style user answer
        user_letter = ua.strip()[0].upper() if ua.strip() else ""
        results.append({
            "question": q["question"],
            "user_answer": ua,
            "correct_answer": correct,
            "is_correct": user_letter == correct,
        })
    return results


def grade_short_answers(
    questions: list[dict],
    user_answers: list[str],
) -> list[dict]:
    """
    Grade short‑answer questions using the AI evaluation endpoint.

    Falls back to case‑insensitive keyword matching when AI is unavailable.
    """
    provider = _get_provider()
    results = []

    for q, ua in zip(questions, user_answers):
        try:
            evaluation = provider.evaluate_short_answer(
                question=q["question"],
                correct_answer=q["correct_answer"],
                user_answer=ua,
            )
            is_correct = bool(evaluation.get("is_correct", False))
        except Exception:
            # Fallback: simple keyword match
            is_correct = ua.strip().lower() == q["correct_answer"].strip().lower()

        results.append({
            "question": q["question"],
            "user_answer": ua,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
        })

    return results


# ═══════════════════════════════════════════════════════
#  Convenience wrapper: grade → save → return summary
# ═══════════════════════════════════════════════════════

def evaluate_and_save(
    user_id: int,
    topic: str,
    difficulty: str,
    question_type: str,
    questions: list[dict],
    user_answers: list[str],
) -> dict:
    """
    Grade all answers, persist to DB, and return a summary dict.

    Returns
    -------
    {
        "score": int,
        "total": int,
        "percentage": float,
        "answers": list[dict],   # per‑question breakdown
        "result_id": int,
    }
    """
    if question_type == "mcq":
        graded = grade_mcq(questions, user_answers)
    else:
        graded = grade_short_answers(questions, user_answers)

    score = sum(1 for a in graded if a["is_correct"])
    total = len(graded)

    result_id = db.save_quiz_result(
        user_id=user_id,
        topic=topic,
        difficulty=difficulty,
        question_type=question_type,
        score=score,
        total_questions=total,
        answers_data=graded,
    )

    return {
        "score": score,
        "total": total,
        "percentage": percentage(score, total),
        "answers": graded,
        "result_id": result_id,
    }
