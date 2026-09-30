"""Core lookup engine and terminal formatting routines."""

from __future__ import annotations
import json
import time
from typing import List, Dict, Any, Optional, Tuple

from src.database import DatabaseRepository, SQLiteRepository
from src.normalization import normalize_phone
from src.validation import validate_lookup_input
from src.schema import UserRecord


class LookupEngine:
    """High-speed query engine for phone numbers."""

    def __init__(self, repository: DatabaseRepository):
        self.repo = repository

    def lookup(self, user_query: str) -> Dict[str, Any]:
        """Perform a validated, indexed lookup for a phone number.

        Returns:
            Dict with query info, records, timing, and status.
        """
        start_total = time.perf_counter()

        is_valid, normalized, err_msg = validate_lookup_input(user_query)
        if not is_valid or not normalized:
            total_time_ms = (time.perf_counter() - start_total) * 1000.0
            return {
                "success": False,
                "error": err_msg,
                "query": user_query,
                "normalized": None,
                "records": [],
                "count": 0,
                "db_time_ms": 0.0,
                "total_time_ms": total_time_ms,
            }

        records, db_time_ms = self.repo.find_by_phone(normalized)
        total_time_ms = (time.perf_counter() - start_total) * 1000.0

        return {
            "success": True,
            "error": None,
            "query": user_query,
            "normalized": normalized,
            "records": records,
            "count": len(records),
            "db_time_ms": db_time_ms,
            "total_time_ms": total_time_ms,
        }

    @staticmethod
    def format_record(rec: UserRecord, index: Optional[int] = None) -> str:
        """Format a single UserRecord cleanly for terminal display."""
        lines = []
        if index is not None:
            lines.append(f"Result {index}")
            lines.append("-" * 35)

        fields = [
            ("Name", rec.name),
            ("Phone (Normalized)", rec.phone_normalized),
            ("Phone (Original)", rec.phone_raw if rec.phone_raw != rec.phone_normalized else None),
            ("Email", rec.email),
            ("City", rec.city),
            ("State", rec.state),
            ("Address", rec.address),
            ("Gender", rec.gender),
            ("DOB", rec.dob),
            ("Bank", rec.bank),
            ("Account Type", rec.account_type),
            ("Income", rec.income),
            ("PAN", rec.pan),
            ("Profession", rec.profession_1),
            ("Profession 2", rec.profession_2),
            ("Mobile Alerts", rec.mobile_alerts),
            ("Source", rec.source_file),
        ]

        for label, val in fields:
            if val is not None and str(val).strip() != "":
                lines.append(f"{label:<20}: {val}")

        # Show extra metadata if present
        if rec.extra_data:
            try:
                extra = json.loads(rec.extra_data)
                for k, v in extra.items():
                    if v and str(v).strip():
                        lines.append(f"{k:<20}: {v}")
            except Exception:
                pass

        return "\n".join(lines)
