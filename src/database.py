"""Database repository layer with support for SQLite and future PostgreSQL extensibility."""

from __future__ import annotations
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.schema import (
    UserRecord,
    CREATE_USERS_TABLE_SQL,
    CREATE_INDEXES_SQL,
)


class DatabaseRepository(ABC):
    """Abstract repository for user record persistence and querying."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def init_schema(self) -> None:
        """Initialize tables and indexes."""
        pass

    @abstractmethod
    def insert_batch(self, records: List[UserRecord]) -> int:
        """Batch insert records inside a transaction."""
        pass

    @abstractmethod
    def find_by_phone(self, phone_normalized: str) -> Tuple[List[UserRecord], float]:
        """Lookup records by normalized phone number. Returns (records, duration_ms)."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Retrieve database statistics."""
        pass

    @abstractmethod
    def get_sample_phones(self, count: int = 100) -> List[str]:
        """Fetch sample normalized phone numbers for benchmarking."""
        pass

    @abstractmethod
    def check_integrity(self) -> str:
        """Run database integrity check."""
        pass


class SQLiteRepository(DatabaseRepository):
    """Production-grade SQLite implementation with WAL mode and indexing."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self.conn is not None:
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0,
        )
        self.conn.row_factory = sqlite3.Row

        # Safe production PRAGMAs
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY;")
        self.conn.execute("PRAGMA mmap_size = 268435456;")  # 256MB memory map

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def init_schema(self) -> None:
        """Create table and indexes."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        with self.conn:
            self.conn.execute(CREATE_USERS_TABLE_SQL)
            for idx_sql in CREATE_INDEXES_SQL:
                self.conn.execute(idx_sql)

    def prepare_for_bulk_import(self) -> None:
        """Optimize SQLite PRAGMAs temporarily for fast bulk ingestion."""
        if not self.conn:
            self.connect()
        assert self.conn is not None
        self.conn.execute("PRAGMA synchronous = OFF;")
        self.conn.execute("PRAGMA journal_mode = MEMORY;")

    def finalize_bulk_import(self) -> None:
        """Restore safe production PRAGMAs, create indexes, and optimize."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        # Build indexes
        for idx_sql in CREATE_INDEXES_SQL:
            self.conn.execute(idx_sql)

        # Restore WAL & synchronous normal
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.conn.execute("PRAGMA optimize;")
        self.conn.commit()

    def insert_batch(self, records: List[UserRecord]) -> int:
        """Insert a batch of UserRecord instances using a single parameterized transaction."""
        if not records:
            return 0
        if not self.conn:
            self.connect()
        assert self.conn is not None

        sql = """
        INSERT INTO users (
            phone_normalized, phone_raw, name, email, city, state, address,
            gender, dob, bank, account_type, income, pan, profession_1,
            profession_2, mobile_alerts, extra_data, source_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        tuples = [r.to_tuple() for r in records]
        cursor = self.conn.cursor()
        cursor.executemany(sql, tuples)
        return len(tuples)

    def find_by_phone(self, phone_normalized: str) -> Tuple[List[UserRecord], float]:
        """Perform fast indexed lookup by normalized phone number."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        sql = "SELECT * FROM users WHERE phone_normalized = ?"
        start_time = time.perf_counter()
        cursor = self.conn.cursor()
        cursor.execute(sql, (phone_normalized,))
        rows = cursor.fetchall()
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        records: List[UserRecord] = []
        for r in rows:
            rec = UserRecord(
                id=r["id"],
                phone_normalized=r["phone_normalized"],
                phone_raw=r["phone_raw"],
                name=r["name"],
                email=r["email"],
                city=r["city"],
                state=r["state"],
                address=r["address"],
                gender=r["gender"],
                dob=r["dob"],
                bank=r["bank"],
                account_type=r["account_type"],
                income=r["income"],
                pan=r["pan"],
                profession_1=r["profession_1"],
                profession_2=r["profession_2"],
                mobile_alerts=r["mobile_alerts"],
                extra_data=r["extra_data"],
                source_file=r["source_file"],
            )
            records.append(rec)

        return records, duration_ms

    def get_stats(self) -> Dict[str, Any]:
        """Gather database statistics."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        cursor = self.conn.cursor()

        # Database size
        size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        size_mb = size_bytes / (1024 * 1024)

        # Total records
        cursor.execute("SELECT COUNT(*) FROM users")
        total_records = cursor.fetchone()[0]

        # Unique phone numbers
        cursor.execute("SELECT COUNT(DISTINCT phone_normalized) FROM users")
        unique_phones = cursor.fetchone()[0]

        # Duplicate phone numbers count
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT phone_normalized FROM users GROUP BY phone_normalized HAVING COUNT(*) > 1
            )
        """)
        dup_phone_keys = cursor.fetchone()[0]

        # Columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [row["name"] for row in cursor.fetchall()]

        # Indexes
        cursor.execute("PRAGMA index_list(users)")
        indexes = [row["name"] for row in cursor.fetchall()]

        # Integrity check
        integrity = self.check_integrity()

        return {
            "db_path": str(self.db_path),
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "total_records": total_records,
            "unique_phones": unique_phones,
            "duplicate_phone_keys": dup_phone_keys,
            "columns": columns,
            "column_count": len(columns),
            "indexes": indexes,
            "integrity": integrity,
        }

    def get_sample_phones(self, count: int = 100) -> List[str]:
        """Retrieve a sample of phone numbers for benchmarking."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT phone_normalized FROM users WHERE id IN "
            "(SELECT id FROM users ORDER BY RANDOM() LIMIT ?)",
            (count,),
        )
        rows = cursor.fetchall()
        if not rows:
            # Fallback if ORDER BY RANDOM is slow on huge datasets
            cursor.execute("SELECT phone_normalized FROM users LIMIT ?", (count,))
            rows = cursor.fetchall()
        return [r[0] for r in rows]

    def check_integrity(self) -> str:
        """Run quick integrity check."""
        if not self.conn:
            self.connect()
        assert self.conn is not None

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA quick_check;")
        res = cursor.fetchone()
        return res[0] if res else "UNKNOWN"
