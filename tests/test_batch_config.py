import json
import os
import tempfile
import unittest

from core.batch_config import (
    MODE_MASTER_TO_TARGET_SINGLE,
    MODE_TARGET_TO_MASTER_REVERSE,
    dump_config,
    load_config,
    validate_config,
)


class BatchConfigTestCase(unittest.TestCase):
    def test_load_single_config_success(self):
        payload = {
            "schema_version": 1,
            "mode": MODE_MASTER_TO_TARGET_SINGLE,
            "master_file": "C:/master.xlsx",
            "defaults": {
                "target_key_col": 1,
                "target_match_col": 2,
                "target_update_start_col": 3,
                "master_key_col": 2,
                "master_match_col": 3,
                "fill_blank_only": False,
                "post_process_enabled": True,
            },
            "jobs": [
                {
                    "name": "pkg1",
                    "target_folder": "C:/pkg1",
                    "master_content_start_col": 4,
                }
            ],
            "runtime": {"continue_on_error": True},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "single.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

            config = load_config(path)

        self.assertEqual(config.mode, MODE_MASTER_TO_TARGET_SINGLE)
        self.assertEqual(config.defaults.target_key_col, 1)
        self.assertEqual(config.jobs[0].variable_column, 4)
        self.assertTrue(config.runtime.continue_on_error)
        self.assertEqual(config.legacy_auto_fill_rules, tuple())

    def test_load_reverse_config_success(self):
        payload = {
            "schema_version": 1,
            "mode": MODE_TARGET_TO_MASTER_REVERSE,
            "master_file": "C:/master.xlsx",
            "defaults": {
                "target_key_col": 1,
                "target_match_col": 2,
                "target_content_col": 3,
                "master_key_col": 2,
                "master_match_col": 3,
                "fill_blank_only": True,
            },
            "jobs": [
                {
                    "name": "",
                    "target_folder": "C:/pkg1",
                    "master_update_col": 10,
                }
            ],
            "runtime": {"continue_on_error": True},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "reverse.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

            config = load_config(path)

        self.assertEqual(config.mode, MODE_TARGET_TO_MASTER_REVERSE)
        self.assertEqual(config.jobs[0].name, "job-1")
        self.assertEqual(config.jobs[0].variable_column, 10)

    def test_validate_invalid_schema_and_mode_and_missing_fields(self):
        payload = {
            "schema_version": 2,
            "mode": "unknown_mode",
            "master_file": "",
            "defaults": {},
            "jobs": [],
            "runtime": {},
            "auto_fill": {"rules": [{"keyword": "[fr]", "variable_column": 6}]},
        }
        errors = validate_config(payload)
        self.assertTrue(any("schema_version" in item for item in errors))
        self.assertTrue(any("mode must be one of" in item for item in errors))
        self.assertTrue(any("master_file is required" in item for item in errors))
        self.assertTrue(any("jobs must contain at least one item" in item for item in errors))

    def test_validate_columns_jobs_and_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_master = os.path.join(temp_dir, "master.xlsx")
            payload = {
                "schema_version": 1,
                "mode": MODE_MASTER_TO_TARGET_SINGLE,
                "master_file": missing_master,
                "defaults": {
                    "target_key_col": 0,
                    "target_match_col": 2,
                    "target_update_start_col": 3,
                    "master_key_col": 2,
                    "master_match_col": 3,
                    "fill_blank_only": False,
                    "post_process_enabled": True,
                },
                "jobs": [
                    {
                        "name": "pkg1",
                        "target_folder": os.path.join(temp_dir, "missing_folder"),
                        "master_content_start_col": 0,
                    }
                ],
                "runtime": {"continue_on_error": True},
            }
            errors = validate_config(payload, check_paths=True)
        self.assertTrue(any("master_file not found" in item for item in errors))
        self.assertTrue(any("target_folder not found" in item for item in errors))
        self.assertTrue(any("positive integer" in item for item in errors))

    def test_roundtrip_dump_and_load_without_auto_fill_in_output(self):
        payload = {
            "schema_version": 1,
            "mode": MODE_MASTER_TO_TARGET_SINGLE,
            "master_file": "C:/master.xlsx",
            "defaults": {
                "target_key_col": 1,
                "target_match_col": 2,
                "target_update_start_col": 3,
                "master_key_col": 2,
                "master_match_col": 3,
                "fill_blank_only": False,
                "post_process_enabled": True,
            },
            "jobs": [
                {
                    "name": "pkg1",
                    "target_folder": "C:/pkg1",
                    "master_content_start_col": 4,
                },
                {
                    "name": "pkg2",
                    "target_folder": "C:/pkg2",
                    "master_content_start_col": 5,
                },
            ],
            "runtime": {"continue_on_error": True},
            "auto_fill": {
                "rules": [
                    {"keyword": "[fr]", "variable_column": 6},
                    {"keyword": "[de]", "variable_column": 7},
                ]
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = os.path.join(temp_dir, "src.json")
            out_path = os.path.join(temp_dir, "out.json")
            with open(src_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

            config = load_config(src_path)
            self.assertEqual(len(config.legacy_auto_fill_rules), 2)

            dump_config(config, out_path)
            with open(out_path, "r", encoding="utf-8") as handle:
                dumped = json.load(handle)
            loaded = load_config(out_path)

        self.assertNotIn("auto_fill", dumped)
        self.assertEqual(loaded.mode, MODE_MASTER_TO_TARGET_SINGLE)
        self.assertEqual(len(loaded.jobs), 2)
        self.assertEqual(loaded.jobs[1].variable_column, 5)
        self.assertEqual(len(loaded.legacy_auto_fill_rules), 0)


if __name__ == "__main__":
    unittest.main()
