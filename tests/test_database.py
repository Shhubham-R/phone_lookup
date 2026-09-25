"""Unit tests for SQLite database repository, batch insert, and indexing."""

import unittest
import tempfile
import os
from pathlib import Path
from src.database import SQLiteRepository
from src.schema import UserRecord


class TestDatabaseRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_users.db"
        self.repo = SQLiteRepository(self.db_path)
        self.repo.connect()
        self.repo.init_schema()

    def tearDown(self):
        self.repo.close()
        self.temp_dir.cleanup()

    def test_schema_and_batch_insert(self):
        records = [
            UserRecord(
                phone_normalized="9876543210",
                phone_raw="+91 98765 43210",
                name="John Doe",
                email="john@example.com",
                city="Mumbai",
                state="Maharashtra",
                bank="HDFC",
                income="10 Lakhs",
            ),
            UserRecord(
                phone_normalized="9876543210",
                phone_raw="09876543210",
                name="Jane Doe",
                email="jane@example.com",
                city="Pune",
                state="Maharashtra",
                bank="ICICI",
            ),
            UserRecord(
                phone_normalized="9998887776",
                phone_raw="9998887776",
                name="Alice Smith",
                email="alice@example.com",
                city="Delhi",
                state="Delhi",
            ),
        ]

        with self.repo.conn:
            inserted = self.repo.insert_batch(records)
        self.assertEqual(inserted, 3)

        # Test find multiple records for duplicate phone number
        results, dur = self.repo.find_by_phone("9876543210")
        self.assertEqual(len(results), 2)
        names = {r.name for r in results}
        self.assertEqual(names, {"John Doe", "Jane Doe"})

        # Test single record
        results, dur = self.repo.find_by_phone("9998887776")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alice Smith")

        # Test non-existent record
        results, dur = self.repo.find_by_phone("1112223334")
        self.assertEqual(len(results), 0)

    def test_stats_and_integrity(self):
        records = [
            UserRecord(phone_normalized="9876543210", name="User 1"),
            UserRecord(phone_normalized="9876543210", name="User 2"),
            UserRecord(phone_normalized="9123456780", name="User 3"),
        ]
        with self.repo.conn:
            self.repo.insert_batch(records)

        stats = self.repo.get_stats()
        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(stats["unique_phones"], 2)
        self.assertEqual(stats["duplicate_phone_keys"], 1)
        self.assertEqual(stats["integrity"], "ok")


if __name__ == "__main__":
    unittest.main()
