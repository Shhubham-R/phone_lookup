"""Database builder and bulk data ingestion CLI."""

from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SQLiteRepository
from src.importer import DataImporter

DEFAULT_DATA_DIR = Path(r"C:\Users\sp\Music\Paytm_Users_Database\Paytm_Users_Database")
DEFAULT_CSV_PATH = DEFAULT_DATA_DIR / "New folder" / "Merged_Master_Data.csv"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "users.db"


def render_progress(
    processed: int,
    valid: int,
    invalid: int,
    duplicates: int,
    elapsed: float,
    total_expected: int = 3494058,
):
    percent = min(100.0, (processed / total_expected) * 100) if total_expected > 0 else 0.0
    bar_len = 25
    filled = int(bar_len * (percent / 100))
    bar = "=" * filled + "-" * (bar_len - filled)
    rate = processed / elapsed if elapsed > 0 else 0

    status = (
        f"\rProcessing: [{bar}] {percent:5.1f}% | "
        f"Rows: {processed:,} | Valid: {valid:,} | Invalid: {invalid:,} | "
        f"Duplicates: {duplicates:,} | {rate:,.0f} rows/s"
    )
    try:
        sys.stdout.write(status)
        sys.stdout.flush()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Build and index the SQLite Phone Lookup database.")
    parser.add_argument(
        "--source",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Path to source CSV or XLSX file (defaults to Merged_Master_Data.csv)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help="Path to target SQLite database file (defaults to data/users.db)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=30000,
        help="Batch insert size (default: 30000)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing database before building",
    )

    args = parser.parse_args()
    source_path = Path(args.source)
    db_path = Path(args.db)

    print("=" * 65)
    print("       PHONE NUMBER LOOKUP DATABASE BUILDER")
    print("=" * 65)
    print(f"Source file    : {source_path}")
    print(f"Target DB      : {db_path}")
    print(f"Batch size     : {args.batch_size:,}")
    print("-" * 65)

    if not source_path.exists():
        # Check fallback directory
        alt_paths = [
            DEFAULT_DATA_DIR / "Merged_Master_Data.xlsx",
            DEFAULT_DATA_DIR / "Paytm_Final_Master.xlsx",
            DEFAULT_DATA_DIR / "Paytm 10 Lakh.xlsx",
        ]
        found = None
        for p in alt_paths:
            if p.exists():
                found = p
                break

        if not found:
            print(f"\n[ERROR] Source file not found: {source_path}")
            print(f"Please specify a valid source file via --source <path>")
            sys.exit(1)
        else:
            print(f"\nDefault CSV not found. Falling back to: {found}")
            source_path = found

    if args.clean and db_path.exists():
        print(f"Removing existing database: {db_path}")
        try:
            db_path.unlink()
            # remove WAL / SHM files if present
            for ext in ("-wal", "-shm"):
                p = Path(str(db_path) + ext)
                if p.exists():
                    p.unlink()
        except Exception as e:
            print(f"Warning: Could not remove old DB file: {e}")

    # Estimate total rows for progress bar
    total_est = 3494058
    if source_path.suffix.lower() == ".csv":
        pass
    else:
        total_est = 1000000

    repo = SQLiteRepository(db_path)
    importer = DataImporter(
        repository=repo,
        batch_size=args.batch_size,
        progress_callback=lambda p, v, inv, d, el: render_progress(p, v, inv, d, el, total_est),
    )

    print("\nStarting ingestion pipeline...")
    start_time = time.time()

    try:
        if source_path.suffix.lower() == ".csv":
            res = importer.import_csv(source_path)
        else:
            res = importer.import_excel(source_path)

        total_time = time.time() - start_time
        print("\n" + "=" * 65)
        print("                 INGESTION COMPLETE")
        print("=" * 65)
        print(f"Total Rows Processed : {res['total_processed']:,}")
        print(f"Valid Phone Records  : {res['valid_phones']:,}")
        print(f"Invalid Rows Skipped : {res['invalid_phones']:,}")
        print(f"Duplicate Phone Keys : {res['duplicate_phones']:,}")
        print(f"Total Elapsed Time   : {total_time:.2f} seconds ({total_time / 60:.1f} minutes)")
        print(f"Overall Ingestion Rate: {res['rate_per_sec']:,.0f} rows/second")
        print("-" * 65)

        stats = repo.get_stats()
        print(f"Database Size        : {stats['size_mb']:.2f} MB")
        print(f"Total Indexed Users  : {stats['total_records']:,}")
        print(f"Unique Phone Numbers : {stats['unique_phones']:,}")
        print(f"Integrity Check      : {stats['integrity']}")
        print("=" * 65)
        print("\nReady! You can now run the lookup tool:")
        print("    python lookup.py\n")

    except Exception as e:
        print(f"\n[FATAL ERROR] Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
