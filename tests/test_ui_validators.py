import unittest

from ui.validators import ValidationError, parse_column_1_based_to_0_based, parse_positive_int


class ValidatorsTestCase(unittest.TestCase):
    def test_parse_positive_int_success(self):
        self.assertEqual(parse_positive_int("7", "列号"), 7)

    def test_parse_positive_int_invalid(self):
        with self.assertRaises(ValidationError):
            parse_positive_int("", "列号")
        with self.assertRaises(ValidationError):
            parse_positive_int("abc", "列号")
        with self.assertRaises(ValidationError):
            parse_positive_int("0", "列号")

    def test_parse_column_success(self):
        self.assertEqual(parse_column_1_based_to_0_based("1", "原文列"), 0)
        self.assertEqual(parse_column_1_based_to_0_based("5", "译文列"), 4)


if __name__ == "__main__":
    unittest.main()

