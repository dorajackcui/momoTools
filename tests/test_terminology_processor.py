import json
import os
import tempfile
import unittest

import pandas as pd
from openpyxl import Workbook

from core.terminology import TerminologyProcessor
from core.terminology.config import ExtractorConfigLoader


class TerminologyProcessorTestCase(unittest.TestCase):
    def _write_workbook(self, path, headers, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        wb.save(path)
        wb.close()

    def _base_config(self):
        return {
            "version": 1,
            "files": ["abc", "cde.xlsx"],
            "versions": ["2.1.3", "2.2.3"],
            "compound_delimiters": ["·"],
            "normalization": {
                "trim": True,
                "collapse_whitespace": True,
                "punctuation_normalization": {
                    "enabled": False,
                    "map": {"，": ",", "。": "."},
                },
                "min_term_length": 1,
                "case_insensitive_dedup": True,
            },
            "thresholds": {
                "containment_min_len": 2,
                "review_short_len_le": 1,
                "review_noise_ratio_ge": 0.6,
            },
            "extractors": [
                {
                    "id": "record_source_v1",
                    "type": "record_rule",
                    "enabled": True,
                    "skip_header": True,
                    "term_column": "source",
                    "key": "name",
                },
                {
                    "id": "tag_span_v1",
                    "type": "tag_span",
                    "enabled": True,
                    "source_columns": ["source"],
                    "open_tag": "<tag>",
                    "close_tags": ["</tag>", "</>"],
                },
                {
                    "id": "compound_split_dot_v1",
                    "type": "compound_split",
                    "enabled": True,
                    "source_columns": ["source"],
                    "delimiter": "·",
                    "emit_compound": True,
                    "emit_head": True,
                    "emit_suffix": True,
                },
            ],
        }

    def _write_config(self, path, payload):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def test_process_files_filters_files_and_builds_summary_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            matched_file = os.path.join(input_dir, "abc.xlsx")
            matched_full_name = os.path.join(input_dir, "cde.xlsx")
            skipped_file = os.path.join(input_dir, "other.xlsx")

            self._write_workbook(
                matched_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.1.3", "player_name", "海星花篮"],
                    ["2.1.3", "desc", "这行key不命中"],
                    ["2.2.3", "item_name", "<tag>标签术语</tag>"],
                    ["2.2.3", "item_name", "术语1·后缀a"],
                    ["2.2.3", "item_name", "术语1"],
                    ["2.2.3", "item_name", "后缀a"],
                ],
            )
            self._write_workbook(
                matched_full_name,
                headers=["Version", "KEY", "source"],
                rows=[
                    ["2.2.3", "npc_name", "海星花篮"],
                    ["2.2.3", "npc_name", "海星花篮的制作图纸"],
                ],
            )
            self._write_workbook(
                skipped_file,
                headers=["version", "key", "source"],
                rows=[["2.1.3", "player_name", "应被文件过滤跳过"]],
            )

            config_path = os.path.join(temp_dir, "rules.json")
            output_path = os.path.join(temp_dir, "result.xlsx")
            config = self._base_config()
            self._write_config(config_path, config)

            processor = TerminologyProcessor()
            processor.set_input_folder(input_dir)
            processor.set_rule_config(config_path)
            processor.set_output_file(output_path)

            result = processor.process_files()

            self.assertEqual(result["files_total"], 2)
            self.assertEqual(result["files_succeeded"], 2)
            self.assertEqual(result["files_failed"], 0)
            self.assertTrue(os.path.exists(output_path))

            workbook = pd.read_excel(output_path, sheet_name=None)
            self.assertSetEqual(
                set(workbook.keys()),
                {"terms_summary", "relations_summary", "review", "details"},
            )
            terms_summary_df = workbook["terms_summary"]
            relations_summary_df = workbook["relations_summary"]
            details_df = workbook["details"]

            # compound_split extractor exists in config but should be ignored.
            self.assertFalse((details_df["extractor_type"] == "compound_split").any())
            self.assertTrue((details_df["file"] == "abc.xlsx").any())
            self.assertTrue((details_df["file"] == "cde.xlsx").any())
            self.assertFalse((details_df["file"] == "other.xlsx").any())

            target_term = terms_summary_df[terms_summary_df["term_norm"] == "海星花篮"].iloc[0]
            self.assertEqual(int(target_term["occurrences_count"]), 2)
            self.assertEqual(int(target_term["files_count"]), 2)
            self.assertEqual(str(target_term["files_list"]), "abc.xlsx;cde.xlsx")
            self.assertEqual(int(target_term["keys_count"]), 2)
            self.assertEqual(str(target_term["keys_list"]), "npc_name;player_name")

            file_presence = relations_summary_df[
                (relations_summary_df["relation_group"] == "file_presence")
                & (relations_summary_df["anchor_term"] == "海星花篮")
            ]
            self.assertFalse(file_presence.empty)
            self.assertEqual(int(file_presence.iloc[0]["members_count"]), 2)
            self.assertEqual(str(file_presence.iloc[0]["members_list"]), "abc.xlsx;cde.xlsx")
            self.assertEqual(int(file_presence.iloc[0]["evidence_count"]), 2)

            suffix_family = relations_summary_df[
                (relations_summary_df["relation_group"] == "suffix_family")
                & (relations_summary_df["anchor_term"] == "术语1")
            ]
            prefix_family = relations_summary_df[
                (relations_summary_df["relation_group"] == "prefix_family")
                & (relations_summary_df["anchor_term"] == "后缀a")
            ]
            self.assertFalse(suffix_family.empty)
            self.assertFalse(prefix_family.empty)
            self.assertEqual(int(suffix_family.iloc[0]["members_count"]), 1)
            self.assertEqual(str(suffix_family.iloc[0]["members_list"]), "后缀a")
            self.assertEqual(int(prefix_family.iloc[0]["members_count"]), 1)
            self.assertEqual(str(prefix_family.iloc[0]["members_list"]), "术语1")

            self.assertEqual(
                list(details_df.columns),
                [
                    "term_id",
                    "term_norm",
                    "candidate_id",
                    "extractor_type",
                    "rule_id",
                    "file",
                    "sheet",
                    "row",
                    "col",
                    "key_value",
                    "version_value",
                    "term_raw",
                    "cell_raw",
                ],
            )
            detail_item = details_df[
                (details_df["term_norm"] == "海星花篮")
                & (details_df["file"] == "abc.xlsx")
            ].iloc[0]
            self.assertEqual(str(detail_item["key_value"]), "player_name")
            self.assertEqual(str(detail_item["version_value"]), "2.1.3")

    def test_loader_supports_files_versions_key_and_delimiters_string_or_array(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config["files"] = "abc, cde.xlsx"
            config["versions"] = "2.1.3, 2.2.3"
            config["compound_delimiters"] = "·, /"
            config["extractors"][0]["key"] = ["name", "title"]
            config["extractors"][0]["key_regex"] = True
            config["extractors"][1]["open_tag"] = "<tag>, <color>"
            self._write_config(config_path, config)

            loaded = ExtractorConfigLoader().load(config_path)
            self.assertEqual(loaded.files, ("abc", "cde.xlsx"))
            self.assertEqual(loaded.versions, ("2.1.3", "2.2.3"))
            self.assertEqual(loaded.compound_delimiters, ("·", "/"))
            record_rule = loaded.extractors[0]
            tag_rule = loaded.extractors[1]
            self.assertEqual(record_rule.key_terms, ("name", "title"))
            self.assertTrue(record_rule.key_regex)
            self.assertEqual(tag_rule.open_tags, ("<tag>", "<color>"))

    def test_loader_defaults_to_all_versions_when_versions_missing_or_wildcard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path_missing = os.path.join(temp_dir, "rules_missing.json")
            config_missing = self._base_config()
            config_missing.pop("versions")
            self._write_config(config_path_missing, config_missing)
            loaded_missing = ExtractorConfigLoader().load(config_path_missing)
            self.assertEqual(loaded_missing.versions, tuple())

            config_path_wildcard = os.path.join(temp_dir, "rules_wildcard.json")
            config_wildcard = self._base_config()
            config_wildcard["versions"] = "*"
            self._write_config(config_path_wildcard, config_wildcard)
            loaded_wildcard = ExtractorConfigLoader().load(config_path_wildcard)
            self.assertEqual(loaded_wildcard.versions, tuple())

    def test_loader_rejects_legacy_record_rule_version_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config["extractors"][0]["version"] = "2.1.3"
            self._write_config(config_path, config)

            with self.assertRaises(ValueError) as ctx:
                ExtractorConfigLoader().load(config_path)
            self.assertIn("record_rule.version is no longer supported", str(ctx.exception))

    def test_loader_supports_tag_span_open_tags_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config["extractors"][1].pop("open_tag")
            config["extractors"][1]["open_tags"] = ["<RedBold>", "<BlueBold>"]
            self._write_config(config_path, config)

            loaded = ExtractorConfigLoader().load(config_path)
            tag_rule = loaded.extractors[1]
            self.assertEqual(tag_rule.open_tags, ("<RedBold>", "<BlueBold>"))

    def test_loader_uses_default_compound_delimiter_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config.pop("compound_delimiters")
            self._write_config(config_path, config)

            loaded = ExtractorConfigLoader().load(config_path)
            self.assertEqual(loaded.compound_delimiters, ("·",))

    def test_loader_defaults_to_all_files_when_files_missing_or_wildcard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path_missing = os.path.join(temp_dir, "rules_missing.json")
            config_missing = self._base_config()
            config_missing.pop("files")
            self._write_config(config_path_missing, config_missing)
            loaded_missing = ExtractorConfigLoader().load(config_path_missing)
            self.assertEqual(loaded_missing.files, tuple())

            config_path_wildcard = os.path.join(temp_dir, "rules_wildcard.json")
            config_wildcard = self._base_config()
            config_wildcard["files"] = "*"
            self._write_config(config_path_wildcard, config_wildcard)
            loaded_wildcard = ExtractorConfigLoader().load(config_path_wildcard)
            self.assertEqual(loaded_wildcard.files, tuple())

    def test_process_files_defaults_to_all_files_when_files_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            file_a = os.path.join(input_dir, "a.xlsx")
            file_b = os.path.join(input_dir, "b.xlsx")
            self._write_workbook(
                file_a,
                headers=["version", "key", "source"],
                rows=[["2.1.3", "player_name", "术语A"]],
            )
            self._write_workbook(
                file_b,
                headers=["version", "key", "source"],
                rows=[["2.2.3", "npc_name", "术语B"]],
            )

            config_path = os.path.join(temp_dir, "rules.json")
            output_path = os.path.join(temp_dir, "result.xlsx")
            config = self._base_config()
            config.pop("files")
            self._write_config(config_path, config)

            processor = TerminologyProcessor()
            processor.set_input_folder(input_dir)
            processor.set_rule_config(config_path)
            processor.set_output_file(output_path)

            result = processor.process_files()
            self.assertEqual(result["files_total"], 2)
            self.assertEqual(result["files_succeeded"], 2)
            self.assertTrue(os.path.exists(output_path))

    def test_global_versions_filter_applies_to_tag_span(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            matched_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                matched_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "desc", "<tag>命中术语</tag>"],
                    ["9.9.9", "desc", "<tag>不应命中</tag>"],
                ],
            )

            config_path = os.path.join(temp_dir, "rules.json")
            output_path = os.path.join(temp_dir, "result.xlsx")
            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            config["extractors"][0]["enabled"] = False
            self._write_config(config_path, config)

            processor = TerminologyProcessor()
            processor.set_input_folder(input_dir)
            processor.set_rule_config(config_path)
            processor.set_output_file(output_path)
            processor.process_files()

            workbook = pd.read_excel(output_path, sheet_name=None)
            details_df = workbook["details"]
            self.assertTrue((details_df["term_raw"] == "命中术语").any())
            self.assertFalse((details_df["term_raw"] == "不应命中").any())

    def test_process_files_fails_file_when_global_versions_set_but_version_column_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["key", "source"],
                rows=[["player_name", "术语A"]],
            )

            config_path = os.path.join(temp_dir, "rules.json")
            output_path = os.path.join(temp_dir, "result.xlsx")
            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.1.3"
            self._write_config(config_path, config)

            processor = TerminologyProcessor()
            processor.set_input_folder(input_dir)
            processor.set_rule_config(config_path)
            processor.set_output_file(output_path)
            result = processor.process_files()

            self.assertEqual(result["files_total"], 1)
            self.assertEqual(result["files_succeeded"], 0)
            self.assertEqual(result["files_failed"], 1)

    def test_loader_rejects_legacy_record_rule_conditions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config["extractors"][0].pop("key")
            config["extractors"][0]["conditions"] = [{"column": "version", "equals": "2.1.3"}]
            self._write_config(config_path, config)

            with self.assertRaises(ValueError) as ctx:
                ExtractorConfigLoader().load(config_path)
            self.assertIn("record_rule.conditions is no longer supported", str(ctx.exception))

    def test_loader_rejects_invalid_key_regex(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config["extractors"][0]["key_regex"] = True
            config["extractors"][0]["key"] = "([a-z"
            self._write_config(config_path, config)

            with self.assertRaises(ValueError) as ctx:
                ExtractorConfigLoader().load(config_path)
            self.assertIn("contains invalid regex", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
