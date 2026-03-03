import unittest

from ui.validators import ValidationError
from ui.views.merge_masters import MergeMastersFrame


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class MergeMastersViewConfigTestCase(unittest.TestCase):
    def test_get_config_maps_columns_and_priority_files(self):
        frame = MergeMastersFrame.__new__(MergeMastersFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.use_combined_key_var = DummyVar(True)
        frame.priority_files = ["a.xlsx", "b.xlsx"]

        config = frame.get_config()

        self.assertEqual(config.key_col, 1)
        self.assertEqual(config.match_col, 2)
        self.assertEqual(config.last_update_col, 10)
        self.assertEqual(config.priority_files, ("a.xlsx", "b.xlsx"))
        self.assertTrue(config.use_combined_key)

    def test_get_config_can_disable_combined_key(self):
        frame = MergeMastersFrame.__new__(MergeMastersFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.use_combined_key_var = DummyVar(False)
        frame.priority_files = ["a.xlsx"]

        config = frame.get_config()

        self.assertFalse(config.use_combined_key)

    def test_get_config_requires_priority_files(self):
        frame = MergeMastersFrame.__new__(MergeMastersFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.priority_files = []

        with self.assertRaises(ValidationError):
            frame.get_config()


if __name__ == "__main__":
    unittest.main()
