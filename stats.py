"""Database statistics and integrity verification CLI."""

from __future__ import annotations
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SQLiteRepository

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "users.db"


def main():
    db_path = DEFAULT_DB_PATH
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"[ERROR] Database not found at: {db_path}")
        print("Please run 'python build_database.py' first.")
        sys.exit(1)

    repo = SQLiteRepository(db_path)
    try:
        stats = repo.get_stats()
        print("=" * 55)
        print("            DATABASE STATISTICS")
        print("=" * 55)
        print(f"Database File        : {stats['db_path']}")
        print(f"Database Size        : {stats['size_mb']:.2f} MB ({stats['size_bytes']:,} bytes)")
        print(f"Total Records        : {stats['total_records']:,}")
        print(f"Unique Phone Numbers : {stats['unique_phones']:,}")
        print(f"Duplicate Phone Keys : {stats['duplicate_phone_keys']:,}")
        print(f"Number of Columns    : {stats['column_count']}")
        print(f"Columns              : {', '.join(stats['columns'])}")
        print(f"Indexed Columns      : {', '.join(stats['indexes'])}")
        integrity_status = "PASS" if stats['integrity'].lower() == "ok" else f"FAIL ({stats['integrity']})"
        print(f"Database Integrity   : {integrity_status}")
        print("=" * 55)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
