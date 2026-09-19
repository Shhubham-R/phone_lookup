"""Unit tests for phone number normalization."""

import unittest
from src.normalization import normalize_phone, extract_all_phone_numbers, is_valid_phone


class TestPhoneNormalization(unittest.TestCase):
    def test_standard_10_digit_indian(self):
        self.assertEqual(normalize_phone("9876543210"), "9876543210")
        self.assertEqual(normalize_phone("8087766952"), "8087766952")
        self.assertEqual(normalize_phone("7042111225"), "7042111225")

    def test_plus_91_prefix(self):
        self.assertEqual(normalize_phone("+919876543210"), "9876543210")
        self.assertEqual(normalize_phone("+91 9876543210"), "9876543210")
        self.assertEqual(normalize_phone("+91-9876543210"), "9876543210")
        self.assertEqual(normalize_phone("+91 98765 43210"), "9876543210")

    def test_91_prefix_twelve_digits(self):
        self.assertEqual(normalize_phone("919876543210"), "9876543210")
        self.assertEqual(normalize_phone("91 9876543210"), "9876543210")

    def test_leading_zero(self):
        self.assertEqual(normalize_phone("09876543210"), "9876543210")

    def test_excel_scientific_and_float(self):
        self.assertEqual(normalize_phone("9.876543210E+09"), "9876543210")
        self.assertEqual(normalize_phone("9876543210.0"), "9876543210")

    def test_international_formats(self):
        self.assertEqual(normalize_phone("+971 50 5651438"), "+971505651438")
        self.assertEqual(normalize_phone("+1 415 555 2671"), "+14155552671")

    def test_space_and_hyphen_variations(self):
        self.assertEqual(normalize_phone("9820-012-345"), "9820012345")
        self.assertEqual(normalize_phone("(982) 001-2345"), "9820012345")

    def test_multiple_numbers(self):
        self.assertEqual(normalize_phone("9819969920, 9833020247"), "9819969920")
        self.assertEqual(normalize_phone("9819969920 9833020247"), "9819969920")
        extracted = extract_all_phone_numbers("9819969920, 9833020247")
        self.assertEqual(extracted, ["9819969920", "9833020247"])

    def test_invalid_and_empty_inputs(self):
        self.assertIsNone(normalize_phone(None))
        self.assertIsNone(normalize_phone(""))
        self.assertIsNone(normalize_phone("   "))
        self.assertIsNone(normalize_phone("NaN"))
        self.assertIsNone(normalize_phone("None"))
        self.assertIsNone(normalize_phone("abc"))
        self.assertIsNone(normalize_phone("123"))

    def test_validity_check(self):
        self.assertTrue(is_valid_phone("9876543210"))
        self.assertTrue(is_valid_phone("+971505651438"))
        self.assertFalse(is_valid_phone(None))
        self.assertFalse(is_valid_phone(""))
        self.assertFalse(is_valid_phone("123"))


if __name__ == "__main__":
    unittest.main()
