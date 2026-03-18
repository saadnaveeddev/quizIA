"""
api_client.py — AI provider abstraction layer.

Currently supports Google Gemini.
Designed so OpenAI (or any other provider) can be added
by implementing the same `AIProvider` interface.

Switch providers by setting the AI_PROVIDER env variable
("gemini" or "openai").
"""

import os
import json
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════
#  Abstract base class — every provider implements this
# ═══════════════════════════════════════════════════════

class AIProvider(ABC):
    """Interface that every AI backend must implement."""

    @abstractmethod
    def generate_questions(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        question_type: str,   # "mcq" or "short_answer"
    ) -> str:
        """Return raw text containing a JSON array of questions."""
        ...

    @abstractmethod
    def evaluate_short_answer(
        self,
        question: str,
        correct_answer: str,
        user_answer: str,
    ) -> dict:
        """
        Evaluate a free‑text answer.

        Returns
        -------
        dict  {"is_correct": bool, "explanation": str}
        """
        ...


# ═══════════════════════════════════════════════════════
#  Prompt templates (shared across providers)
# ═══════════════════════════════════════════════════════

MCQ_PROMPT_TEMPLATE = """
You are a mathematics professor creating a quiz for computer science students.

Generate exactly {num_questions} **multiple-choice** questions on the topic "{topic}"
at **{difficulty}** difficulty level.

Rules:
- Each question must be unique and well-formed.
- Provide exactly 4 options labelled A, B, C, D.
- Indicate the single correct option letter.
- Respond ONLY with valid JSON — no additional commentary.

Use this exact JSON schema:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "A"
    }}
  ]
}}
"""

SHORT_ANSWER_PROMPT_TEMPLATE = """
You are a mathematics professor creating a quiz for computer science students.

Generate exactly {num_questions} **short-answer** questions on the topic "{topic}"
at **{difficulty}** difficulty level.

Rules:
- Each question must be unique and well-formed.
- Provide a concise correct answer for each question.
- Respond ONLY with valid JSON — no additional commentary.

Use this exact JSON schema:
{{
  "questions": [
    {{
      "question": "...",
      "correct_answer": "..."
    }}
  ]
}}
"""

EVALUATION_PROMPT_TEMPLATE = """
You are a mathematics professor evaluating a student's answer.

Question : {question}
Correct answer : {correct_answer}
Student's answer: {user_answer}

Determine whether the student's answer is essentially correct.
Minor differences in wording, formatting, or notation are acceptable
as long as the mathematical meaning is the same.

Respond ONLY with valid JSON:
{{
  "is_correct": true or false,
  "explanation": "Brief explanation of your judgement"
}}
"""


# ═══════════════════════════════════════════════════════
#  Google Gemini provider
# ═══════════════════════════════════════════════════════

class GeminiProvider(AIProvider):
    """Google Gemini (generativeai SDK) implementation."""

    def __init__(self):
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set.  "
                "Add it to your .env file or export it as an environment variable."
            )
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")

    # ── question generation ──────────────────────────
    def generate_questions(
        self, topic: str, difficulty: str, num_questions: int, question_type: str
    ) -> str:
        if question_type == "mcq":
            prompt = MCQ_PROMPT_TEMPLATE.format(
                topic=topic, difficulty=difficulty, num_questions=num_questions
            )
        else:
            prompt = SHORT_ANSWER_PROMPT_TEMPLATE.format(
                topic=topic, difficulty=difficulty, num_questions=num_questions
            )

        response = self._model.generate_content(prompt)
        return response.text

    # ── short‑answer evaluation ──────────────────────
    def evaluate_short_answer(
        self, question: str, correct_answer: str, user_answer: str
    ) -> dict:
        prompt = EVALUATION_PROMPT_TEMPLATE.format(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
        )
        response = self._model.generate_content(prompt)
        from utils import extract_json_from_text

        result = extract_json_from_text(response.text)
        if result and isinstance(result, dict):
            return result
        # Fallback: keyword comparison
        return {
            "is_correct": user_answer.strip().lower() == correct_answer.strip().lower(),
            "explanation": "Evaluated by keyword match (AI response was unparsable).",
        }


# ═══════════════════════════════════════════════════════
#  OpenAI provider  (stub — ready for future use)
# ═══════════════════════════════════════════════════════

class OpenAIProvider(AIProvider):
    """
    OpenAI ChatCompletion implementation.

    To activate:
      1.  pip install openai
      2.  Set OPENAI_API_KEY in your .env
      3.  Set AI_PROVIDER=openai
    """

    def __init__(self):
        try:
            import openai
        except ImportError:
            raise ImportError("Install the openai package:  pip install openai")

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        self._client = openai.OpenAI(api_key=api_key)
        self._model_name = "gpt-4o-mini"

    def _chat(self, prompt: str) -> str:
        """Send a single‑turn chat completion request."""
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    def generate_questions(
        self, topic: str, difficulty: str, num_questions: int, question_type: str
    ) -> str:
        if question_type == "mcq":
            prompt = MCQ_PROMPT_TEMPLATE.format(
                topic=topic, difficulty=difficulty, num_questions=num_questions
            )
        else:
            prompt = SHORT_ANSWER_PROMPT_TEMPLATE.format(
                topic=topic, difficulty=difficulty, num_questions=num_questions
            )
        return self._chat(prompt)

    def evaluate_short_answer(
        self, question: str, correct_answer: str, user_answer: str
    ) -> dict:
        prompt = EVALUATION_PROMPT_TEMPLATE.format(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
        )
        from utils import extract_json_from_text

        result = extract_json_from_text(self._chat(prompt))
        if result and isinstance(result, dict):
            return result
        return {
            "is_correct": user_answer.strip().lower() == correct_answer.strip().lower(),
            "explanation": "Evaluated by keyword match (AI response was unparsable).",
        }


# ═══════════════════════════════════════════════════════
#  Factory — returns the correct provider instance
# ═══════════════════════════════════════════════════════

_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


def get_ai_provider() -> AIProvider:
    """
    Instantiate and return the AI provider specified by
    the AI_PROVIDER environment variable (default: 'gemini').
    """
    name = os.getenv("AI_PROVIDER", "gemini").lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown AI_PROVIDER '{name}'. Choose from: {list(_PROVIDERS.keys())}"
        )
    return cls()
