import re
from dataclasses import dataclass
from typing import Any

from core.kernel import safe_to_str

from .types import Candidate, CompoundSplitRule, RecordRule, TagSpanRule


@dataclass(frozen=True)
class ExtractContext:
    file_path: str
    file_name: str
    sheet_name: str
    row_index: int
    row_values: dict[str, Any]
    row_cells_text: dict[str, str]
    header_map: dict[str, int]


class BaseExtractor:
    extractor_type: str = ""

    def required_columns(self) -> set[str]:
        raise NotImplementedError

    def extract(self, context: ExtractContext) -> list[Candidate]:
        raise NotImplementedError


class RecordRuleExtractor(BaseExtractor):
    extractor_type = "record_rule"

    def __init__(self, rule: RecordRule):
        self.rule = rule
        self._key_regex_patterns = [
            re.compile(pattern, flags=re.IGNORECASE) for pattern in self.rule.key_terms
        ] if self.rule.key_regex else []

    def required_columns(self) -> set[str]:
        required = {self.rule.term_column, "key"}
        if self.rule.versions:
            required.add("version")
        return required

    def extract(self, context: ExtractContext) -> list[Candidate]:
        if not self.rule.enabled:
            return []
        if self.rule.skip_header and context.row_index <= 1:
            return []

        version_value = safe_to_str(context.row_values.get("version"), strip=True)
        if self.rule.versions and version_value not in self.rule.versions:
            return []
        key_value = safe_to_str(context.row_values.get("key"), strip=True)
        if self.rule.key_regex:
            if not any(pattern.search(key_value) for pattern in self._key_regex_patterns):
                return []
        else:
            key_value_lower = key_value.lower()
            if not any(token.lower() in key_value_lower for token in self.rule.key_terms):
                return []

        term_value = context.row_values.get(self.rule.term_column)
        term_raw = safe_to_str(term_value, strip=False)
        if not term_raw.strip():
            return []

        return [
            Candidate(
                term_raw=term_raw,
                extractor_type=self.extractor_type,
                rule_id=self.rule.id,
                file=context.file_name,
                sheet=context.sheet_name,
                row=context.row_index,
                col=context.header_map[self.rule.term_column] + 1,
                cell_raw=context.row_cells_text.get(self.rule.term_column, ""),
                meta={
                    "term_column": self.rule.term_column,
                    "version": version_value,
                    "key": key_value,
                },
            )
        ]


class TagSpanExtractor(BaseExtractor):
    extractor_type = "tag_span"

    def __init__(self, rule: TagSpanRule):
        self.rule = rule
        open_pattern = self._build_tag_pattern(self.rule.open_tags)
        close_pattern = self._build_tag_pattern(self.rule.close_tags)
        self._pattern = re.compile(
            f"({open_pattern})(.*?)({close_pattern})",
            flags=re.DOTALL,
        )

    def required_columns(self) -> set[str]:
        return set(self.rule.source_columns)

    def extract(self, context: ExtractContext) -> list[Candidate]:
        if not self.rule.enabled:
            return []

        candidates: list[Candidate] = []
        for column in self.rule.source_columns:
            cell_text = context.row_cells_text.get(column, "")
            if not cell_text:
                continue

            for matched in self._pattern.finditer(cell_text):
                open_tag = matched.group(1)
                term_raw = matched.group(2)
                if not term_raw.strip():
                    continue
                close_tag = matched.group(3)
                key_value = safe_to_str(context.row_values.get("key"), strip=True)
                version_value = safe_to_str(context.row_values.get("version"), strip=True)
                candidates.append(
                    Candidate(
                        term_raw=term_raw,
                        extractor_type=self.extractor_type,
                        rule_id=self.rule.id,
                        file=context.file_name,
                        sheet=context.sheet_name,
                        row=context.row_index,
                        col=context.header_map[column] + 1,
                        cell_raw=cell_text,
                        meta={
                            "source_column": column,
                            "open_tag": open_tag,
                            "close_tag": close_tag,
                            "key": key_value,
                            "version": version_value,
                        },
                    )
                )

        return candidates

    @staticmethod
    def _build_tag_pattern(tags: tuple[str, ...]) -> str:
        # Longer tags first to avoid partial matching when one tag is a prefix of another.
        ordered = sorted({str(tag) for tag in tags if str(tag)}, key=len, reverse=True)
        return "|".join(re.escape(tag) for tag in ordered)


class CompoundSplitExtractor(BaseExtractor):
    extractor_type = "compound_split"

    def __init__(self, rule: CompoundSplitRule):
        self.rule = rule

    def required_columns(self) -> set[str]:
        return set(self.rule.source_columns)

    def extract(self, context: ExtractContext) -> list[Candidate]:
        if not self.rule.enabled:
            return []

        candidates: list[Candidate] = []
        for column in self.rule.source_columns:
            cell_text = context.row_cells_text.get(column, "")
            if not cell_text or self.rule.delimiter not in cell_text:
                continue

            head, suffix = cell_text.split(self.rule.delimiter, 1)
            head = head.strip()
            suffix = suffix.strip()
            if not head or not suffix:
                continue

            compound = f"{head}{self.rule.delimiter}{suffix}"
            col = context.header_map[column] + 1
            base_meta = {
                "source_column": column,
                "delimiter": self.rule.delimiter,
                "head": head,
                "suffix": suffix,
                "compound": compound,
            }
            if self.rule.emit_compound:
                candidates.append(
                    Candidate(
                        term_raw=compound,
                        extractor_type=self.extractor_type,
                        rule_id=self.rule.id,
                        file=context.file_name,
                        sheet=context.sheet_name,
                        row=context.row_index,
                        col=col,
                        cell_raw=cell_text,
                        meta={**base_meta, "split_role": "compound"},
                    )
                )
            if self.rule.emit_head:
                candidates.append(
                    Candidate(
                        term_raw=head,
                        extractor_type=self.extractor_type,
                        rule_id=self.rule.id,
                        file=context.file_name,
                        sheet=context.sheet_name,
                        row=context.row_index,
                        col=col,
                        cell_raw=cell_text,
                        meta={**base_meta, "split_role": "head"},
                    )
                )
            if self.rule.emit_suffix:
                candidates.append(
                    Candidate(
                        term_raw=suffix,
                        extractor_type=self.extractor_type,
                        rule_id=self.rule.id,
                        file=context.file_name,
                        sheet=context.sheet_name,
                        row=context.row_index,
                        col=col,
                        cell_raw=cell_text,
                        meta={**base_meta, "split_role": "suffix"},
                    )
                )

        return candidates
