"""
utils.py — Shared helper utilities.

Contains small, reusable functions used across the application.
"""

import re
import json


# ═══════════════════════════════════════════════════════
#  JSON helpers
# ═══════════════════════════════════════════════════════

def extract_json_from_text(text: str) -> dict | list | None:
    """
    Extract a JSON object or array from a string that may contain
    markdown fences or other surrounding text.

    Returns the parsed Python object, or None on failure.
    """
    # Try to find JSON inside ```json ... ``` fences first
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Fallback: find the first { ... } or [ ... ] block
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return None


# ═══════════════════════════════════════════════════════
#  Display helpers
# ═══════════════════════════════════════════════════════

def percentage(score: int, total: int) -> float:
    """Return the percentage score, rounded to 1 decimal."""
    if total == 0:
        return 0.0
    return round((score / total) * 100, 1)


def performance_label(pct: float) -> str:
    """Return a human-readable performance label for a percentage."""
    if pct >= 80:
        return "Strong"
    elif pct >= 50:
        return "Moderate"
    else:
        return "Needs Improvement"


def ordinal(n: int) -> str:
    """Return English ordinal string for an integer (1 → '1st')."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
