import unittest

from ui.validators import ValidationError
from ui.views.updater import UpdaterFrame


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class UpdaterViewConfigTestCase(unittest.TestCase):
    def _build_frame_stub(
        self,
        target_key="1",
        target_match="2",
        target_start="3",
        master_key="2",
        master_match="3",
        master_start="4",
        column_count="1",
        fill_blank=False,
        post_process=True,
        allow_blank_write=False,
    ):
        frame = UpdaterFrame.__new__(UpdaterFrame)
        frame.target_key_col_var = DummyVar(target_key)
        frame.target_match_col_var = DummyVar(target_match)
        frame.target_update_start_col_var = DummyVar(target_start)
        frame.master_key_col_var = DummyVar(master_key)
        frame.master_match_col_var = DummyVar(master_match)
        frame.master_content_start_col_var = DummyVar(master_start)
        frame.column_count_var = DummyVar(column_count)
        frame.fill_blank_var = DummyVar(fill_blank)
        frame.post_process_var = DummyVar(post_process)
        frame.allow_blank_write_var = DummyVar(allow_blank_write)
        return frame

    def test_get_config_default_mapping(self):
        frame = self._build_frame_stub()
        config = frame.get_config()

        self.assertEqual(config.target_key_col, 0)
        self.assertEqual(config.target_match_col, 1)
        self.assertEqual(config.target_update_start_col, 2)
        self.assertEqual(config.master_key_col, 1)
        self.assertEqual(config.master_match_col, 2)
        self.assertEqual(config.master_content_start_col, 3)
        self.assertEqual(config.column_count, 1)
        self.assertFalse(config.fill_blank_only)
        self.assertFalse(config.allow_blank_write)
        self.assertTrue(config.post_process_enabled)

    def test_get_config_invalid_column_count(self):
        frame = self._build_frame_stub(column_count="0")
        with self.assertRaises(ValidationError):
            frame.get_config()


if __name__ == "__main__":
    unittest.main()
