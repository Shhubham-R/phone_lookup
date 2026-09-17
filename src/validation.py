"""Input validation and sanitization for queries and records."""

from __future__ import annotations
import re
from typing import Tuple, Optional
from src.normalization import normalize_phone, is_valid_phone


def validate_lookup_input(user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate user input from terminal or API.

    Returns:
        (is_valid, normalized_phone, error_message)
    """
    if not user_input or not user_input.strip():
        return False, None, "Input cannot be empty. Please enter a phone number."

    raw = user_input.strip()

    # Reject obvious invalid non-phone queries
    if len(raw) < 4:
        return False, None, "Phone number is too short. Please enter a valid number."

    if len(raw) > 30:
        return False, None, "Phone number is too long. Please enter a valid number."

    normalized = normalize_phone(raw)

    if not normalized or not is_valid_phone(normalized):
        return False, None, f"Could not recognize '{raw}' as a valid phone number format."

    return True, normalized, None


def sanitize_string(val: Any) -> Optional[str]:
    """Clean string values, handling nulls, NaN, and whitespace."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "nil"):
        return None
    return s
