import dataclasses
import unittest

from ui.view_models import ClearerConfig, MultiColumnConfig, ReverseConfig, StatsConfig, UpdaterConfig


class ViewModelsTestCase(unittest.TestCase):
    def test_updater_config_fields(self):
        config = UpdaterConfig(
            target_key_col=0,
            target_match_col=1,
            target_update_start_col=2,
            master_key_col=1,
            master_match_col=2,
            master_content_start_col=3,
            column_count=1,
            fill_blank_only=True,
            post_process_enabled=False,
        )
        self.assertEqual(config.target_update_start_col, 2)
        self.assertEqual(config.column_count, 1)
        self.assertTrue(config.fill_blank_only)
        self.assertFalse(config.post_process_enabled)

    def test_multi_column_config_fields(self):
        config = MultiColumnConfig(
            target_key_col=1,
            target_match_col=2,
            target_update_start_col=4,
            master_key_col=1,
            master_match_col=2,
            master_start_col=4,
            column_count=7,
            fill_blank_only=False,
            post_process_enabled=True,
        )
        self.assertEqual(config.column_count, 7)
        self.assertTrue(config.post_process_enabled)

    def test_frozen_dataclass(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            config.source_col = 3  # type: ignore[misc]

    def test_other_configs(self):
        reverse = ReverseConfig(0, 1, 2, 1, 2, 3, False)
        clearer = ClearerConfig(5)
        self.assertEqual(reverse.master_update_col, 3)
        self.assertEqual(clearer.column_number, 5)


if __name__ == "__main__":
    unittest.main()
