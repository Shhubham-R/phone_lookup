"""Benchmark suite for database lookup performance."""

from __future__ import annotations
import argparse
import statistics
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


def run_benchmark(db_path: Path, iterations: int = 1000):
    if not db_path.exists():
        print(f"[ERROR] Database not found at: {db_path}")
        print("Please run 'python build_database.py' first.")
        sys.exit(1)

    repo = SQLiteRepository(db_path)
    engine = LookupEngine(repo)

    stats = repo.get_stats()
    total_records = stats["total_records"]

    print("=" * 55)
    print("           DATABASE LOOKUP BENCHMARK")
    print("=" * 55)
    print(f"Database File     : {db_path}")
    print(f"Total Records     : {total_records:,}")
    print(f"Benchmark Queries : {iterations:,}")
    print("-" * 55)

    print("Fetching sample test keys from database...")
    sample_size = min(iterations, 5000)
    samples = repo.get_sample_phones(sample_size)

    if not samples:
        print("[ERROR] No records found in database to benchmark.")
        sys.exit(1)

    print("Warming up database cache...")
    for s in samples[:50]:
        engine.lookup(s)

    print(f"Executing {iterations:,} indexed phone lookups...")

    db_latencies_ms = []
    total_latencies_ms = []

    start_bench = time.perf_counter()

    for i in range(iterations):
        query_phone = samples[i % len(samples)]
        res = engine.lookup(query_phone)
        db_latencies_ms.append(res["db_time_ms"])
        total_latencies_ms.append(res["total_time_ms"])

    total_bench_duration = time.perf_counter() - start_bench
    repo.close()

    db_latencies_ms.sort()
    total_latencies_ms.sort()

    def p(arr, percentile):
        idx = int(len(arr) * (percentile / 100.0))
        return arr[min(idx, len(arr) - 1)]

    qps = iterations / total_bench_duration if total_bench_duration > 0 else 0

    print("\n" + "=" * 55)
    print("                BENCHMARK RESULTS")
    print("=" * 55)
    print(f"Total Queries Executed : {iterations:,}")
    print(f"Total Wall Clock Time  : {total_bench_duration:.3f} s")
    print(f"Query Throughput       : {qps:,.1f} lookups/sec")
    print("-" * 55)
    print("DATABASE QUERY TIME (Pure SQL Indexed Lookup):")
    print(f"  Minimum              : {min(db_latencies_ms):.3f} ms")
    print(f"  Average              : {statistics.mean(db_latencies_ms):.3f} ms")
    print(f"  Median (P50)         : {statistics.median(db_latencies_ms):.3f} ms")
    print(f"  95th Percentile (P95): {p(db_latencies_ms, 95):.3f} ms")
    print(f"  99th Percentile (P99): {p(db_latencies_ms, 99):.3f} ms")
    print(f"  Maximum              : {max(db_latencies_ms):.3f} ms")
    print("-" * 55)
    print("TOTAL APPLICATION TIME (Normalization + Validation + Query + Object Mapping):")
    print(f"  Minimum              : {min(total_latencies_ms):.3f} ms")
    print(f"  Average              : {statistics.mean(total_latencies_ms):.3f} ms")
    print(f"  Median (P50)         : {statistics.median(total_latencies_ms):.3f} ms")
    print(f"  95th Percentile (P95): {p(total_latencies_ms, 95):.3f} ms")
    print(f"  99th Percentile (P99): {p(total_latencies_ms, 99):.3f} ms")
    print(f"  Maximum              : {max(total_latencies_ms):.3f} ms")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Benchmark database phone lookup latency.")
    parser.add_argument(
        "--queries",
        type=int,
        default=1000,
        help="Number of lookup queries to execute (e.g. 100, 1000, 10000). Default: 1000",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help="Path to users.db SQLite file",
    )
    args = parser.parse_args()
    run_benchmark(Path(args.db), args.queries)


if __name__ == "__main__":
    main()
