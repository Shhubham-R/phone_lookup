"""Phone number normalization and validation module.

This module provides robust phone number normalization routines for Indian mobile
and landline numbers, as well as international formats.
"""

from __future__ import annotations
import re
from typing import List, Optional


def normalize_phone(raw: str | int | float | None) -> Optional[str]:
    """Normalize a raw phone number input into a standard search key.

    Handles:
    - 10-digit Indian mobile numbers (e.g. '9876543210')
    - Indian numbers with country code '+91' or '91' (e.g. '+919876543210', '91 9876543210')
    - Indian numbers with leading zero (e.g. '09876543210')
    - Formatting characters (spaces, hyphens, dots, parentheses)
    - Excel float and scientific notation strings (e.g. '9.876543210E+09', '9876543210.0')
    - Multiple phone numbers in a single string (extracts primary/first valid number)
    - International numbers with '+' prefix (e.g. '+971 50 5651438' -> '+971505651438')

    Returns:
        Normalized phone string, or None if invalid/empty.
    """
    if raw is None:
        return None

    s = str(raw).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "nil", "0", "-"):
        return None

    # Handle scientific notation like '9.87654e+09' or '9.87654321E+09'
    if re.match(r"^[0-9]+(\.[0-9]+)?[eE][+-]?[0-9]+$", s):
        try:
            val = float(s)
            s = str(int(round(val)))
        except (ValueError, OverflowError):
            pass

    # Remove decimal .0 from float conversion (e.g. '9876543210.0')
    if s.endswith(".0"):
        s = s[:-2].strip()

    # If comma, semicolon, or slash separated, take the first chunk
    if any(sep in s for sep in (",", ";", "/")):
        s = re.split(r"[,;/]", s)[0].strip()
    elif len(s.split()) > 1:
        # If multiple space-separated tokens look like multiple 10-digit numbers: '9819969920 9833020247'
        parts = s.split()
        if len(parts) >= 2 and all(len(p) == 10 and p.isdigit() for p in parts):
            s = parts[0]

    has_plus = s.startswith("+")

    # Strip all non-digit characters
    digits = re.sub(r"\D", "", s)

    if not digits:
        return None

    # 1. 12 digits starting with '91' and Indian mobile prefix (5, 6, 7, 8, 9)
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "56789":
        return digits[2:]

    # 2. 11 digits starting with '0' and Indian mobile prefix (5, 6, 7, 8, 9)
    if len(digits) == 11 and digits.startswith("0") and digits[1] in "56789":
        return digits[1:]

    # 3. Standard 10-digit number
    if len(digits) == 10:
        return digits

    # 4. Explicit international number with '+' prefix
    if has_plus:
        if digits.startswith("91") and len(digits) == 12 and digits[2] in "56789":
            return digits[2:]
        return "+" + digits

    # 5. Landline numbers (e.g., 02225542869, 07923236989) or other digit lengths
    if len(digits) in (10, 11, 12, 13, 14, 15):
        return digits

    # Fallback for short/other numbers if they have at least 6 digits
    if len(digits) >= 6:
        return digits

    return None


def extract_all_phone_numbers(raw: str | int | float | None) -> List[str]:
    """Extract all valid normalized phone numbers from a field that may contain multiple numbers."""
    if raw is None:
        return []

    s = str(raw).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "nil"):
        return []

    # Split by comma, slash, semicolon, or newline
    chunks = re.split(r"[,;/\n]+", s)
    results: List[str] = []
    seen = set()

    for chunk in chunks:
        norm = normalize_phone(chunk)
        if norm and norm not in seen:
            seen.add(norm)
            results.append(norm)

    return results


def is_valid_phone(phone: Optional[str]) -> bool:
    """Check whether a normalized phone number is structurally valid."""
    if not phone:
        return False
    clean = phone.lstrip("+")
    if not clean.isdigit():
        return False
    # Valid mobile/landline typically has length between 7 and 15 digits
    return 7 <= len(clean) <= 15
