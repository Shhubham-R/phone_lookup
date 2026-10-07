"""Data quality audit and reporting tool."""

from __future__ import annotations
import csv
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.normalization import normalize_phone, is_valid_phone

DEFAULT_DATA_DIR = Path(r"C:\Users\sp\Music\Paytm_Users_Database\Paytm_Users_Database")
DEFAULT_CSV_PATH = DEFAULT_DATA_DIR / "New folder" / "Merged_Master_Data.csv"


def run_data_quality_audit(file_path: Path, max_rows: int = 500000):
    print("=" * 60)
    print("              DATA QUALITY AUDIT REPORT")
    print("=" * 60)
    print(f"Auditing File: {file_path}")
    print(f"Max Sample   : {'ALL' if max_rows <= 0 else f'{max_rows:,} rows'}")
    print("-" * 60)

    if not file_path.exists():
        print(f"[ERROR] Target file not found: {file_path}")
        sys.exit(1)

    start_time = time.time()

    total_rows = 0
    empty_phones = 0
    valid_phones = 0
    invalid_phones = 0
    scientific_notation = 0
    plus_91_prefix = 0
    prefix_91_twelve = 0
    prefix_0_eleven = 0
    pure_10_digits = 0
    suspiciously_short = 0
    suspiciously_long = 0
    has_spaces_hyphens = 0
    multiple_numbers_in_cell = 0

    phone_counts = Counter()
    length_distribution = Counter()

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            print("[ERROR] Empty CSV file.")
            return

        phone_idx = 0
        for i, col in enumerate(header):
            if "phone" in col.lower() or "mobile" in col.lower():
                phone_idx = i
                break

        print(f"Identified Phone Column: '{header[phone_idx]}' (Index {phone_idx})")
        print("Scanning rows...")

        for row in reader:
            total_rows += 1
            if not row or len(row) <= phone_idx:
                empty_phones += 1
                continue

            raw = row[phone_idx].strip()
            if not raw or raw.lower() in ("nan", "none", "null", "n/a"):
                empty_phones += 1
                continue

            length_distribution[len(raw)] += 1

            if "e+" in raw.lower() or "e-" in raw.lower():
                scientific_notation += 1

            if " " in raw or "-" in raw or "(" in raw or ")" in raw:
                has_spaces_hyphens += 1

            if any(sep in raw for sep in (",", ";", "/")) or (len(raw.split()) > 1 and len(raw) > 15):
                multiple_numbers_in_cell += 1

            norm = normalize_phone(raw)
            if not norm or not is_valid_phone(norm):
                invalid_phones += 1
            else:
                valid_phones += 1
                phone_counts[norm] += 1

                if raw.startswith("+91"):
                    plus_91_prefix += 1
                elif raw.startswith("91") and len(raw) == 12:
                    prefix_91_twelve += 1
                elif raw.startswith("0") and len(raw) == 11:
                    prefix_0_eleven += 1
                elif len(raw) == 10 and raw.isdigit():
                    pure_10_digits += 1

                if len(norm.lstrip("+")) < 10:
                    suspiciously_short += 1
                elif len(norm.lstrip("+")) > 12:
                    suspiciously_long += 1

            if 0 < max_rows <= total_rows:
                break

    elapsed = time.time() - start_time
    dup_phones = sum(1 for c in phone_counts.values() if c > 1)
    unique_phones = len(phone_counts)

    print("\n" + "=" * 60)
    print("                 AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total Rows Examined         : {total_rows:,}")
    print(f"Valid Phone Numbers         : {valid_phones:,} ({valid_phones / total_rows * 100:.2f}%)")
    print(f"Empty / Missing Phones      : {empty_phones:,} ({empty_phones / total_rows * 100:.2f}%)")
    print(f"Malformed / Invalid Phones  : {invalid_phones:,} ({invalid_phones / total_rows * 100:.2f}%)")
    print(f"Unique Normalized Phones    : {unique_phones:,}")
    print(f"Duplicate Phone Numbers     : {dup_phones:,}")
    print("-" * 60)
    print("FORMATTING ANOMALIES DETECTED:")
    print(f"  Pure Clean 10-Digit (Indian): {pure_10_digits:,}")
    print(f"  Prefixed with +91           : {plus_91_prefix:,}")
    print(f"  Prefixed with 91 (12 digits): {prefix_91_twelve:,}")
    print(f"  Prefixed with 0 (11 digits) : {prefix_0_eleven:,}")
    print(f"  Excel Scientific Notation   : {scientific_notation:,}")
    print(f"  With Spaces / Hyphens       : {has_spaces_hyphens:,}")
    print(f"  Multiple Numbers in One Cell: {multiple_numbers_in_cell:,}")
    print(f"  Suspiciously Short (<10 dig): {suspiciously_short:,}")
    print(f"  Suspiciously Long (>12 dig) : {suspiciously_long:,}")
    print("-" * 60)
    print("TOP RAW STRING LENGTHS:")
    for l, cnt in sorted(length_distribution.items(), key=lambda x: -x[1])[:8]:
        print(f"  Length {l:2d} chars: {cnt:,} rows ({cnt / total_rows * 100:.2f}%)")
    print("-" * 60)
    print(f"Audit completed in {elapsed:.2f} seconds ({total_rows / elapsed:,.0f} rows/sec)")
    print("=" * 60 + "\n")


def main():
    path = DEFAULT_CSV_PATH
    max_rows = 500000
    if len(sys.argv) > 1 and not sys.argv[1].isdigit():
        path = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        max_rows = int(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        max_rows = int(sys.argv[1])

    run_data_quality_audit(path, max_rows)


if __name__ == "__main__":
    main()
