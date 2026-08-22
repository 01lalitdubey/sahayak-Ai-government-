"""
Password Utilities — Sahayak AI
=================================
bcrypt hashing using the bcrypt library directly (avoids passlib backend
version detection issues with bcrypt >= 4.x).

Plain-text passwords NEVER leave this module.

Rules enforced at registration:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
"""

import re
import bcrypt

from app.core.exceptions import ValidationException

_UPPERCASE = re.compile(r"[A-Z]")
_LOWERCASE = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")

_BCRYPT_ROUNDS = 12   # OWASP recommended minimum


def hash_password(plain: str) -> str:
    """Return bcrypt hash string of the plain-text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> str:
    """
    Enforce password complexity rules.
    Raises ValidationException with a descriptive message on failure.
    Returns the password unchanged on success.
    """
    errors: list[str] = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not _UPPERCASE.search(password):
        errors.append("at least one uppercase letter")
    if not _LOWERCASE.search(password):
        errors.append("at least one lowercase letter")
    if not _DIGIT.search(password):
        errors.append("at least one digit")
    if not _SPECIAL.search(password):
        errors.append("at least one special character (!@#$%^&* etc.)")

    if errors:
        raise ValidationException(
            f"Password must contain: {', '.join(errors)}."
        )
    return password
