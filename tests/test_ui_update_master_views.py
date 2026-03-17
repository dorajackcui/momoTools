import unittest

from ui.validators import ValidationError
from ui.views.source_translation_pipeline import SourceTranslationPipelineFrame
from ui.views.update_content import UpdateContentFrame
from ui.views.update_master import UpdateMasterFrame


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class UpdateMasterViewsConfigTestCase(unittest.TestCase):
    def test_update_master_get_config(self):
        frame = UpdateMasterFrame.__new__(UpdateMasterFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.priority_files = ["a.xlsx"]

        config = frame.get_config()

        self.assertEqual(config.key_col, 1)
        self.assertEqual(config.match_col, 2)
        self.assertEqual(config.last_update_col, 10)
        self.assertEqual(config.priority_files, ("a.xlsx",))
        self.assertTrue(config.use_combined_key)

    def test_update_content_get_config_requires_files(self):
        frame = UpdateContentFrame.__new__(UpdateContentFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.priority_files = []

        with self.assertRaises(ValidationError):
            frame.get_config()

    def test_source_translation_pipeline_get_config(self):
        frame = SourceTranslationPipelineFrame.__new__(SourceTranslationPipelineFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.source_priority_files = ["source_a.xlsx"]
        frame.translation_priority_files = ["translation_a.xlsx", "translation_b.xlsx"]

        config = frame.get_config()

        self.assertEqual(config.key_col, 1)
        self.assertEqual(config.match_col, 2)
        self.assertEqual(config.last_update_col, 10)
        self.assertEqual(config.source_priority_files, ("source_a.xlsx",))
        self.assertEqual(
            config.translation_priority_files,
            ("translation_a.xlsx", "translation_b.xlsx"),
        )

    def test_source_translation_pipeline_get_config_requires_translation_files(self):
        frame = SourceTranslationPipelineFrame.__new__(SourceTranslationPipelineFrame)
        frame.key_col_var = DummyVar("2")
        frame.match_col_var = DummyVar("3")
        frame.last_update_col_var = DummyVar("11")
        frame.source_priority_files = ["source_a.xlsx"]
        frame.translation_priority_files = []

        with self.assertRaises(ValidationError):
            frame.get_config()


if __name__ == "__main__":
    unittest.main()
