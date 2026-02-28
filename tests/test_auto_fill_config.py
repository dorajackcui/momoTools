import json
import os
import tempfile
import unittest

from core.auto_fill_config import (
    AutoFillConfig,
    AutoFillRule,
    load_auto_fill_config,
    parse_payload,
    save_auto_fill_config,
    validate_payload,
)


class AutoFillConfigTestCase(unittest.TestCase):
    def test_validate_payload_success(self):
        payload = {
            "rules": [
                {"keyword": "[fr]", "variable_column": 6},
                {"keyword": "[de]", "variable_column": 7},
            ],
            "match_rule": "prefix",
            "scan_depth": 1,
        }
        self.assertEqual(validate_payload(payload), [])

    def test_validate_payload_failure(self):
        payload = {
            "rules": [{"keyword": "", "variable_column": 0}],
            "match_rule": "contains",
            "scan_depth": 2,
        }
        errors = validate_payload(payload)
        self.assertTrue(any("match_rule" in item for item in errors))
        self.assertTrue(any("scan_depth" in item for item in errors))
        self.assertTrue(any("keyword is required" in item for item in errors))
        self.assertTrue(any("positive integer" in item for item in errors))

    def test_parse_payload_non_strict_ignores_bad_rules(self):
        payload = {
            "rules": [
                {"keyword": "[fr]", "variable_column": 6},
                {"keyword": "", "variable_column": 0},
            ],
            "match_rule": "contains",
            "scan_depth": 9,
        }
        config = parse_payload(payload, strict=False)
        self.assertEqual(len(config.rules), 1)
        self.assertEqual(config.rules[0].keyword, "[fr]")
        self.assertEqual(config.match_rule, "prefix")
        self.assertEqual(config.scan_depth, 1)

    def test_load_missing_returns_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "not_exists.json")
            config = load_auto_fill_config(path)
        self.assertEqual(config, AutoFillConfig())

    def test_save_and_load_roundtrip(self):
        config = AutoFillConfig(
            rules=(
                AutoFillRule(keyword="[fr]", variable_column=6),
                AutoFillRule(keyword="[de]", variable_column=7),
            ),
            match_rule="prefix",
            scan_depth=1,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "auto_fill_rules.json")
            save_auto_fill_config(config, path)
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            loaded = load_auto_fill_config(path)

        self.assertEqual(payload["match_rule"], "prefix")
        self.assertEqual(payload["scan_depth"], 1)
        self.assertEqual(len(payload["rules"]), 2)
        self.assertEqual(loaded.rules[1].variable_column, 7)


if __name__ == "__main__":
    unittest.main()
