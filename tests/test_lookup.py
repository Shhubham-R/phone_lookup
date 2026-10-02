"""Unit tests for lookup engine, input validation, and result formatting."""

import unittest
import tempfile
from pathlib import Path
from src.database import SQLiteRepository
from src.lookup import LookupEngine
from src.schema import UserRecord


class TestLookupEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_lookup.db"
        self.repo = SQLiteRepository(self.db_path)
        self.repo.connect()
        self.repo.init_schema()

        records = [
            UserRecord(
                phone_normalized="9876543210",
                phone_raw="+91 98765 43210",
                name="Siddharth Sharma",
                email="siddharth@example.com",
                city="Bangalore",
                state="Karnataka",
                pan="ABCDE1234F",
            ),
            UserRecord(
                phone_normalized="9876543210",
                phone_raw="09876543210",
                name="Siddharth Business",
                email="sid.biz@example.com",
                city="Bangalore",
                state="Karnataka",
            ),
            UserRecord(
                phone_normalized="8087766952",
                phone_raw="8087766952",
                name="Pooja Patil",
                email="pooja@example.com",
                city="Pune",
                state="Maharashtra",
            ),
        ]
        with self.repo.conn:
            self.repo.insert_batch(records)

        self.engine = LookupEngine(self.repo)

    def tearDown(self):
        self.repo.close()
        self.temp_dir.cleanup()

    def test_query_variations(self):
        # 1. Plain 10 digit
        r1 = self.engine.lookup("9876543210")
        self.assertTrue(r1["success"])
        self.assertEqual(r1["count"], 2)

        # 2. +91 with spaces
        r2 = self.engine.lookup("+91 98765 43210")
        self.assertTrue(r2["success"])
        self.assertEqual(r2["count"], 2)

        # 3. 0 prefix
        r3 = self.engine.lookup("09876543210")
        self.assertTrue(r3["success"])
        self.assertEqual(r3["count"], 2)

        # 4. Single result
        r4 = self.engine.lookup("+91-8087766952")
        self.assertTrue(r4["success"])
        self.assertEqual(r4["count"], 1)
        self.assertEqual(r4["records"][0].name, "Pooja Patil")

        # 5. Non existent number
        r5 = self.engine.lookup("9999999999")
        self.assertTrue(r5["success"])
        self.assertEqual(r5["count"], 0)

        # 6. Invalid input
        r6 = self.engine.lookup("invalid-text")
        self.assertFalse(r6["success"])

    def test_format_record(self):
        rec = UserRecord(
            phone_normalized="9876543210",
            phone_raw="+91 98765 43210",
            name="John Doe",
            email="john@example.com",
            city="Mumbai",
        )
        formatted = LookupEngine.format_record(rec)
        self.assertIn("John Doe", formatted)
        self.assertIn("9876543210", formatted)
        self.assertIn("Mumbai", formatted)


if __name__ == "__main__":
    unittest.main()
