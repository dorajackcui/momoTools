import unittest

from core.terminology.extractors import ExtractContext, RecordRuleExtractor, TagSpanExtractor
from core.terminology.types import RecordRule, TagSpanRule


class TerminologyExtractorsTestCase(unittest.TestCase):
    def _context(self, source_text: str, version: str = "2.1.3", key_text: str = "name") -> ExtractContext:
        return ExtractContext(
            file_path="C:/tmp/abc.xlsx",
            file_name="abc.xlsx",
            sheet_name="Sheet1",
            row_index=2,
            row_values={"version": version, "key": key_text, "source": source_text},
            row_cells_text={"version": version, "key": key_text, "source": source_text},
            header_map={"version": 0, "key": 1, "source": 2},
        )

    def test_record_rule_extractor_matches_version_and_key(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3", "2.2.3"),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        output = extractor.extract(self._context("海星花篮", version="2.2.3", key_text="player_name"))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].term_raw, "海星花篮")
        self.assertEqual(output[0].file, "abc.xlsx")
        self.assertEqual(output[0].meta["key"], "player_name")
        self.assertEqual(output[0].meta["version"], "2.2.3")

    def test_record_rule_extractor_non_match_version(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3",),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        output = extractor.extract(self._context("海星花篮", version="2.3.0", key_text="player_name"))
        self.assertEqual(output, [])

    def test_record_rule_extractor_non_match_key(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3",),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        output = extractor.extract(self._context("海星花篮", version="2.1.3", key_text="desc"))
        self.assertEqual(output, [])

    def test_record_rule_key_contains_is_case_insensitive(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3",),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        output = extractor.extract(self._context("海星花篮", version="2.1.3", key_text="PlayerName"))
        self.assertEqual(len(output), 1)

    def test_record_rule_key_regex_matching(self):
        rule = RecordRule(
            id="record_regex",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3",),
            key_terms=(r"^(player|npc)_name$",),
            key_regex=True,
        )
        extractor = RecordRuleExtractor(rule)
        hit = extractor.extract(self._context("海星花篮", version="2.1.3", key_text="npc_name"))
        miss = extractor.extract(self._context("海星花篮", version="2.1.3", key_text="player_desc"))
        self.assertEqual(len(hit), 1)
        self.assertEqual(miss, [])

    def test_record_rule_required_columns(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=("2.1.3",),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        self.assertEqual(extractor.required_columns(), {"version", "key", "source"})

    def test_record_rule_without_version_filter(self):
        rule = RecordRule(
            id="record_1",
            type="record_rule",
            enabled=True,
            skip_header=True,
            term_column="source",
            versions=tuple(),
            key_terms=("name",),
        )
        extractor = RecordRuleExtractor(rule)
        output = extractor.extract(self._context("海星花篮", version="9.9.9", key_text="player_name"))
        self.assertEqual(len(output), 1)
        self.assertEqual(extractor.required_columns(), {"key", "source"})

    def test_tag_span_extractor_matches_two_close_tags(self):
        rule = TagSpanRule(
            id="tag_1",
            type="tag_span",
            enabled=True,
            source_columns=("source",),
            open_tags=("<tag>",),
            close_tags=("</tag>", "</>"),
        )
        extractor = TagSpanExtractor(rule)
        context = self._context("<tag>术语A</tag> xx <tag>术语B</>")
        output = extractor.extract(context)
        self.assertEqual([item.term_raw for item in output], ["术语A", "术语B"])

    def test_tag_span_extractor_supports_multiple_open_tags(self):
        rule = TagSpanRule(
            id="tag_2",
            type="tag_span",
            enabled=True,
            source_columns=("source",),
            open_tags=("<RedBold>", "<BlueBold>"),
            close_tags=("</tag>", "</>"),
        )
        extractor = TagSpanExtractor(rule)
        context = self._context("<RedBold>术语A</tag> xx <BlueBold>术语B</>")
        output = extractor.extract(context)
        self.assertEqual([item.term_raw for item in output], ["术语A", "术语B"])
        self.assertEqual([item.meta["open_tag"] for item in output], ["<RedBold>", "<BlueBold>"])


if __name__ == "__main__":
    unittest.main()
