"""
auth.py — Authentication helpers.

Provides signup / login logic with bcrypt password hashing.
"""

import bcrypt
import db


# ═══════════════════════════════════════════════════════
#  Password utilities
# ═══════════════════════════════════════════════════════

def hash_password(plain: str) -> str:
    """Return a bcrypt‑hashed version of the plain‑text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain‑text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ═══════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════

def signup(name: str, email: str, password: str) -> tuple[bool, str]:
    """
    Register a new user.

    Returns
    -------
    (success: bool, message: str)
    """
    # ── input validation ──
    if not name.strip():
        return False, "Name is required."
    if not email.strip() or "@" not in email:
        return False, "A valid email address is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    # ── duplicate check ──
    if db.user_exists(email.strip().lower()):
        return False, "An account with this email already exists."

    # ── create ──
    hashed = hash_password(password)
    db.create_user(name.strip(), email.strip().lower(), hashed)
    return True, "Account created successfully! You can now log in."


def login(email: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Authenticate a user.

    Returns
    -------
    (success: bool, message: str, user: dict | None)
    """
    if not email.strip() or not password:
        return False, "Email and password are required.", None

    user = db.get_user_by_email(email.strip().lower())
    if user is None:
        return False, "No account found with this email.", None

    if not verify_password(password, user["password"]):
        return False, "Incorrect password.", None

    return True, "Login successful!", user
