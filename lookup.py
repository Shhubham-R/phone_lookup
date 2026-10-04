"""Interactive High-Speed Phone Number Lookup Terminal UI."""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SQLiteRepository
from src.lookup import LookupEngine

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "users.db"


def print_banner(stats: dict):
    print("=" * 60)
    print("        PHONE NUMBER LOOKUP SYSTEM")
    print("=" * 60)
    print(f"Database     : {stats['db_path']}")
    print(f"Records      : {stats['total_records']:,}")
    print(f"Indexed Field: phone_normalized (B-Tree index)")
    print(f"Status       : READY")
    print("-" * 60)
    print("Type a phone number to search, or 'help', 'stats', 'exit'.")
    print("-" * 60)


def print_help():
    print("\nAvailable Commands:")
    print("  <number>    : Look up an Indian/International phone number")
    print("                Examples: 9876543210, +91 98765 43210, 09876543210")
    print("  stats       : Display database statistics and integrity status")
    print("  help        : Show this help message")
    print("  exit / quit : Exit the application\n")


def print_stats(stats: dict):
    print("\n" + "=" * 50)
    print(" DATABASE STATISTICS")
    print("=" * 50)
    print(f"Location             : {stats['db_path']}")
    print(f"Database Size        : {stats['size_mb']:.2f} MB ({stats['size_bytes']:,} bytes)")
    print(f"Total Records        : {stats['total_records']:,}")
    print(f"Unique Phone Numbers : {stats['unique_phones']:,}")
    print(f"Duplicate Phone Keys : {stats['duplicate_phone_keys']:,}")
    print(f"Total Columns        : {stats['column_count']}")
    print(f"Available Columns    : {', '.join(stats['columns'])}")
    print(f"Active Indexes       : {', '.join(stats['indexes'])}")
    print(f"Integrity Status     : {stats['integrity']}")
    print("=" * 50 + "\n")


def run_interactive(engine: LookupEngine, repo: SQLiteRepository):
    stats = repo.get_stats()
    print_banner(stats)

    while True:
        try:
            user_input = input("Enter phone number:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Exiting. Goodbye!")
            break
        elif cmd in ("help", "?"):
            print_help()
            continue
        elif cmd == "stats":
            print_stats(repo.get_stats())
            continue

        # Perform lookup
        result = engine.lookup(user_input)

        print("\n---------------------------------------------")
        if not result["success"]:
            print(f"[INVALID INPUT] {result['error']}")
            print("---------------------------------------------\n")
            continue

        records = result["records"]
        count = result["count"]

        if count == 0:
            print("NOT FOUND")
            print(f"Normalized search key: {result['normalized']}")
            print(f"Lookup time: {result['db_time_ms']:.2f} ms")
            print("---------------------------------------------\n")
            continue

        print(f"FOUND ({count} {'record' if count == 1 else 'records'})")
        print(f"Normalized Key : {result['normalized']}")
        print("---------------------------------------------")

        if count == 1:
            print(LookupEngine.format_record(records[0]))
        else:
            for i, rec in enumerate(records, start=1):
                print(LookupEngine.format_record(rec, index=i))
                if i < count:
                    print("-" * 35)

        print("-" * 45)
        print(
            f"Lookup time   : {result['total_time_ms']:.2f} ms "
            f"(DB query: {result['db_time_ms']:.2f} ms)"
        )
        print(f"Records found : {count}")
        print("---------------------------------------------\n")


def main():
    db_path = DEFAULT_DB_PATH
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and not sys.argv[1].isdigit():
        # User might pass custom db path
        if sys.argv[1].endswith(".db") or sys.argv[1].endswith(".sqlite"):
            db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"\n[ERROR] Database not found at: {db_path}")
        print("Please build the database first by running:")
        print("    python build_database.py\n")
        sys.exit(1)

    repo = SQLiteRepository(db_path)
    engine = LookupEngine(repo)

    # Check for direct command-line lookup (e.g., python lookup.py 9876543210)
    args = [a for a in sys.argv[1:] if not a.endswith(".db") and not a.endswith(".sqlite")]
    if args:
        query = " ".join(args)
        result = engine.lookup(query)
        if not result["success"]:
            print(f"[ERROR] {result['error']}")
            sys.exit(1)
        if result["count"] == 0:
            print(f"Not found: {result['normalized']} (time: {result['db_time_ms']:.2f} ms)")
            sys.exit(0)
        for i, rec in enumerate(result["records"], start=1):
            if result["count"] > 1:
                print(f"\n--- Result {i} ---")
            print(LookupEngine.format_record(rec))
        print(f"\nLookup time: {result['total_time_ms']:.2f} ms (DB: {result['db_time_ms']:.2f} ms)")
        sys.exit(0)

    try:
        run_interactive(engine, repo)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
