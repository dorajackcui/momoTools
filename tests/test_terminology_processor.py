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
            "affix_delimiters": ["\u00b7", ":"],
            "normalization": {
                "trim": True,
                "collapse_whitespace": True,
                "punctuation_normalization": {
                    "enabled": False,
                    "map": {",": ",", ".": "."},
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
                    "delimiter": "\u00b7",
                    "emit_compound": True,
                    "emit_head": True,
                    "emit_suffix": True,
                },
            ],
        }

    def _write_config(self, path, payload):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def _run_processor(self, input_dir, config, temp_dir):
        config_path = os.path.join(temp_dir, "rules.json")
        output_path = os.path.join(temp_dir, "result.xlsx")
        self._write_config(config_path, config)

        processor = TerminologyProcessor()
        processor.set_input_folder(input_dir)
        processor.set_rule_config(config_path)
        processor.set_output_file(output_path)
        result = processor.process_files()
        workbook = pd.read_excel(output_path, sheet_name=None)
        return result, workbook

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
                    ["2.1.3", "player_name", "star basket"],
                    ["2.1.3", "desc", "row ignored by key filter"],
                    ["2.2.3", "item_name", "<tag>tag term</tag>"],
                    ["2.2.3", "item_name", "term1\u00b7suffixa"],
                    ["2.2.3", "item_name", "term1"],
                    ["2.2.3", "item_name", "suffixa"],
                ],
            )
            self._write_workbook(
                matched_full_name,
                headers=["Version", "KEY", "source"],
                rows=[
                    ["2.2.3", "npc_name", "star basket"],
                    ["2.2.3", "npc_name", "star basket crafting"],
                ],
            )
            self._write_workbook(
                skipped_file,
                headers=["version", "key", "source"],
                rows=[["2.1.3", "player_name", "should_be_skipped_by_files_filter"]],
            )

            config = self._base_config()
            result, workbook = self._run_processor(input_dir, config, temp_dir)

            self.assertEqual(result["files_total"], 2)
            self.assertEqual(result["files_succeeded"], 2)
            self.assertEqual(result["files_failed"], 0)

            self.assertSetEqual(
                set(workbook.keys()),
                {"terms_summary", "relations_summary", "review", "details"},
            )
            terms_summary_df = workbook["terms_summary"]
            relations_summary_df = workbook["relations_summary"]
            details_df = workbook["details"]

            self.assertFalse((details_df["extractor_type"] == "compound_split").any())
            self.assertTrue((details_df["file"] == "abc.xlsx").any())
            self.assertTrue((details_df["file"] == "cde.xlsx").any())
            self.assertFalse((details_df["file"] == "other.xlsx").any())

            target_term = terms_summary_df[terms_summary_df["term_norm"] == "star basket"].iloc[0]
            self.assertEqual(int(target_term["occurrences_count"]), 2)
            self.assertEqual(int(target_term["files_count"]), 2)
            self.assertEqual(str(target_term["files_list"]), "abc.xlsx;cde.xlsx")
            self.assertEqual(int(target_term["keys_count"]), 2)
            self.assertEqual(str(target_term["keys_list"]), "npc_name;player_name")

            cross_file = relations_summary_df[
                (relations_summary_df["relation_type"] == "cross_file")
                & (relations_summary_df["cross_term"] == "star basket")
            ]
            self.assertFalse(cross_file.empty)
            self.assertEqual(int(cross_file.iloc[0]["cross_files_count"]), 2)
            self.assertEqual(str(cross_file.iloc[0]["cross_files_list"]), "abc.xlsx;cde.xlsx")
            self.assertEqual(int(cross_file.iloc[0]["evidence_count"]), 2)
            single_file_cross = relations_summary_df[
                (relations_summary_df["relation_type"] == "cross_file")
                & (relations_summary_df["cross_term"] == "star basket crafting")
            ]
            self.assertTrue(single_file_cross.empty)

            prefix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "term1")
            ]
            suffix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "suffix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "suffixa")
            ]
            self.assertFalse(prefix_family.empty)
            self.assertFalse(suffix_family.empty)
            self.assertEqual(int(prefix_family.iloc[0]["affix_related_count"]), 1)
            self.assertEqual(str(prefix_family.iloc[0]["affix_related_list"]), "suffixa")
            self.assertEqual(str(prefix_family.iloc[0]["affix_delimiters"]), "\u00b7")
            self.assertEqual(int(suffix_family.iloc[0]["affix_related_count"]), 1)
            self.assertEqual(str(suffix_family.iloc[0]["affix_related_list"]), "term1")
            self.assertEqual(str(suffix_family.iloc[0]["affix_delimiters"]), "\u00b7")

            self.assertEqual(
                list(relations_summary_df.columns),
                [
                    "relation_type",
                    "evidence_count",
                    "cross_term",
                    "cross_files_count",
                    "cross_files_list",
                    "affix_role",
                    "affix_anchor_term",
                    "affix_related_count",
                    "affix_related_list",
                    "affix_delimiters",
                    "notes",
                ],
            )
            self.assertNotIn("relation_group", relations_summary_df.columns)
            self.assertNotIn("anchor_term", relations_summary_df.columns)
            self.assertNotIn("members_count", relations_summary_df.columns)
            self.assertNotIn("members_list", relations_summary_df.columns)

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
                (details_df["term_norm"] == "star basket")
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
            config["affix_delimiters"] = "\u00b7, /"
            config["extractors"][0]["key"] = ["name", "title"]
            config["extractors"][0]["key_regex"] = True
            config["extractors"][1]["open_tag"] = "<tag>, <color>"
            self._write_config(config_path, config)

            loaded = ExtractorConfigLoader().load(config_path)
            self.assertEqual(loaded.files, ("abc", "cde.xlsx"))
            self.assertEqual(loaded.versions, ("2.1.3", "2.2.3"))
            self.assertEqual(loaded.affix_delimiters, ("\u00b7", "/"))
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

    def test_loader_uses_default_affix_delimiter_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config.pop("affix_delimiters")
            self._write_config(config_path, config)

            loaded = ExtractorConfigLoader().load(config_path)
            self.assertEqual(loaded.affix_delimiters, ("\u00b7", ":"))

    def test_loader_rejects_legacy_compound_delimiters_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "rules.json")
            config = self._base_config()
            config.pop("affix_delimiters")
            config["compound_delimiters"] = "\u00b7, /"
            self._write_config(config_path, config)

            with self.assertRaises(ValueError) as ctx:
                ExtractorConfigLoader().load(config_path)
            self.assertIn("compound_delimiters is no longer supported", str(ctx.exception))

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
                rows=[["2.1.3", "player_name", "term_a"]],
            )
            self._write_workbook(
                file_b,
                headers=["version", "key", "source"],
                rows=[["2.2.3", "npc_name", "term_b"]],
            )

            config = self._base_config()
            config.pop("files")
            result, _workbook = self._run_processor(input_dir, config, temp_dir)

            self.assertEqual(result["files_total"], 2)
            self.assertEqual(result["files_succeeded"], 2)

    def test_global_versions_filter_applies_to_tag_span(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            matched_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                matched_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "desc", "<tag>hit_term</tag>"],
                    ["9.9.9", "desc", "<tag>should_not_hit</tag>"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            config["extractors"][0]["enabled"] = False
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            details_df = workbook["details"]
            self.assertTrue((details_df["term_raw"] == "hit_term").any())
            self.assertFalse((details_df["term_raw"] == "should_not_hit").any())

    def test_process_files_fails_file_when_global_versions_set_but_version_column_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["key", "source"],
                rows=[["player_name", "term_a"]],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.1.3"
            result, _workbook = self._run_processor(input_dir, config, temp_dir)

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

    def test_affix_group_supports_dot_and_colon_delimiters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "item_name", "pre1\u00b7suf1"],
                    ["2.2.3", "item_name", "pre1"],
                    ["2.2.3", "item_name", "suf1"],
                    ["2.2.3", "item_name", "pre2:suf2"],
                    ["2.2.3", "item_name", "pre2"],
                    ["2.2.3", "item_name", "suf2"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            relations_summary_df = workbook["relations_summary"]
            pre1_row = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "pre1")
            ]
            pre2_row = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "pre2")
            ]
            self.assertFalse(pre1_row.empty)
            self.assertFalse(pre2_row.empty)
            self.assertEqual(str(pre1_row.iloc[0]["affix_delimiters"]), "\u00b7")
            self.assertEqual(str(pre2_row.iloc[0]["affix_delimiters"]), ":")
            cross_pre1 = relations_summary_df[
                (relations_summary_df["relation_type"] == "cross_file")
                & (relations_summary_df["cross_term"] == "pre1")
            ]
            self.assertTrue(cross_pre1.empty)

    def test_affix_group_does_not_require_independent_terms(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "item_name", "ghost\u00b7tail"],
                    ["2.2.3", "item_name", "ghost"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            relations_summary_df = workbook["relations_summary"]
            prefix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "ghost")
            ]
            suffix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "suffix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "tail")
            ]
            self.assertFalse(prefix_family.empty)
            self.assertFalse(suffix_family.empty)

    def test_affix_group_splits_given_examples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "item_name", "Babiole ensoleill\u00e9e : prairie printani\u00e8re"],
                    ["2.2.3", "item_name", "\u5fc3\u9009\u4e4b\u793c\u00b7\u76f8\u9080"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            relations_summary_df = workbook["relations_summary"]
            french_prefix = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "Babiole ensoleill\u00e9e")
            ]
            french_suffix = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "suffix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "prairie printani\u00e8re")
            ]
            zh_prefix = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "\u5fc3\u9009\u4e4b\u793c")
            ]
            zh_suffix = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "suffix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "\u76f8\u9080")
            ]
            self.assertFalse(french_prefix.empty)
            self.assertFalse(french_suffix.empty)
            self.assertFalse(zh_prefix.empty)
            self.assertFalse(zh_suffix.empty)

    def test_affix_group_splits_on_first_delimiter_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "item_name", "A:B:C"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            relations_summary_df = workbook["relations_summary"]
            prefix_a = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "A")
            ]
            self.assertFalse(prefix_a.empty)
            self.assertEqual(str(prefix_a.iloc[0]["affix_related_list"]), "B:C")

            prefix_b = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "B")
            ]
            self.assertTrue(prefix_b.empty)

    def test_affix_group_is_independent_from_cross_file_filter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir)

            target_file = os.path.join(input_dir, "abc.xlsx")
            self._write_workbook(
                target_file,
                headers=["version", "key", "source"],
                rows=[
                    ["2.2.3", "item_name", "alpha\u00b7omega"],
                    ["2.2.3", "item_name", "alpha"],
                    ["2.2.3", "item_name", "omega"],
                ],
            )

            config = self._base_config()
            config["files"] = "*"
            config["versions"] = "2.2.3"
            _result, workbook = self._run_processor(input_dir, config, temp_dir)

            relations_summary_df = workbook["relations_summary"]
            cross_rows = relations_summary_df[relations_summary_df["relation_type"] == "cross_file"]
            self.assertTrue(cross_rows.empty)

            prefix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "prefix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "alpha")
            ]
            suffix_family = relations_summary_df[
                (relations_summary_df["relation_type"] == "affix_group")
                & (relations_summary_df["affix_role"] == "suffix_anchor")
                & (relations_summary_df["affix_anchor_term"] == "omega")
            ]
            self.assertFalse(prefix_family.empty)
            self.assertFalse(suffix_family.empty)


if __name__ == "__main__":
    unittest.main()
