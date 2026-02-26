import json
import re
from typing import Any

from .types import (
    CompoundSplitRule,
    ExtractorRule,
    NormalizationSettings,
    PunctuationNormalization,
    RecordRule,
    TagSpanRule,
    TerminologyConfig,
    ThresholdSettings,
)


class ExtractorConfigLoader:
    def load(self, path: str) -> TerminologyConfig:
        try:
            # Use utf-8-sig to accept both plain UTF-8 and UTF-8 with BOM.
            with open(path, "r", encoding="utf-8-sig") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON config: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read config file: {path}") from exc

        if not isinstance(raw, dict):
            raise ValueError("Config root must be an object")

        version = int(raw.get("version", 0))
        if version != 1:
            raise ValueError("Config version must be 1")

        files = self._parse_file_filters(raw.get("files"))
        compound_delimiters = self._parse_list_value(
            raw.get("compound_delimiters"),
            "compound_delimiters",
            required=False,
        ) or ("·",)
        normalization = self._parse_normalization(raw.get("normalization") or {})
        thresholds = self._parse_thresholds(raw.get("thresholds") or {})
        extractors = self._parse_extractors(raw.get("extractors"))

        return TerminologyConfig(
            version=version,
            files=files,
            compound_delimiters=compound_delimiters,
            normalization=normalization,
            thresholds=thresholds,
            extractors=extractors,
        )

    def _parse_normalization(self, payload: dict[str, Any]) -> NormalizationSettings:
        if not isinstance(payload, dict):
            raise ValueError("normalization must be an object")

        punctuation_payload = payload.get("punctuation_normalization") or {}
        if not isinstance(punctuation_payload, dict):
            raise ValueError("normalization.punctuation_normalization must be an object")
        mapping = punctuation_payload.get("map") or {}
        if not isinstance(mapping, dict):
            raise ValueError("normalization.punctuation_normalization.map must be an object")
        punctuation = PunctuationNormalization(
            enabled=bool(punctuation_payload.get("enabled", False)),
            mapping={str(k): str(v) for k, v in mapping.items()},
        )

        min_term_length = int(payload.get("min_term_length", 1))
        if min_term_length < 1:
            raise ValueError("normalization.min_term_length must be >= 1")

        return NormalizationSettings(
            trim=bool(payload.get("trim", True)),
            collapse_whitespace=bool(payload.get("collapse_whitespace", True)),
            punctuation=punctuation,
            min_term_length=min_term_length,
            case_insensitive_dedup=bool(payload.get("case_insensitive_dedup", True)),
        )

    def _parse_thresholds(self, payload: dict[str, Any]) -> ThresholdSettings:
        if not isinstance(payload, dict):
            raise ValueError("thresholds must be an object")

        containment_min_len = int(payload.get("containment_min_len", 2))
        review_short_len_le = int(payload.get("review_short_len_le", 1))
        review_noise_ratio_ge = float(payload.get("review_noise_ratio_ge", 0.6))

        if containment_min_len < 1:
            raise ValueError("thresholds.containment_min_len must be >= 1")
        if review_short_len_le < 0:
            raise ValueError("thresholds.review_short_len_le must be >= 0")
        if review_noise_ratio_ge < 0 or review_noise_ratio_ge > 1:
            raise ValueError("thresholds.review_noise_ratio_ge must be in [0, 1]")

        return ThresholdSettings(
            containment_min_len=containment_min_len,
            review_short_len_le=review_short_len_le,
            review_noise_ratio_ge=review_noise_ratio_ge,
        )

    def _parse_extractors(self, payload: Any) -> tuple[ExtractorRule, ...]:
        if not isinstance(payload, list) or not payload:
            raise ValueError("extractors must be a non-empty list")

        rules: list[ExtractorRule] = []
        for raw_rule in payload:
            if not isinstance(raw_rule, dict):
                raise ValueError("each extractor config must be an object")
            extractor_type = str(raw_rule.get("type", "")).strip()
            if extractor_type == "record_rule":
                rules.append(self._parse_record_rule(raw_rule))
            elif extractor_type == "tag_span":
                rules.append(self._parse_tag_span_rule(raw_rule))
            elif extractor_type == "compound_split":
                rules.append(self._parse_compound_split_rule(raw_rule))
            else:
                raise ValueError(f"Unsupported extractor type: {extractor_type}")

        return tuple(rules)

    @staticmethod
    def _parse_rule_identity(raw_rule: dict[str, Any], expected_type: str) -> tuple[str, bool]:
        rule_id = str(raw_rule.get("id", "")).strip()
        if not rule_id:
            raise ValueError(f"{expected_type}.id is required")
        enabled = bool(raw_rule.get("enabled", True))
        return rule_id, enabled

    def _parse_record_rule(self, raw_rule: dict[str, Any]) -> RecordRule:
        rule_id, enabled = self._parse_rule_identity(raw_rule, "record_rule")
        if "conditions" in raw_rule:
            raise ValueError(
                f"record_rule.conditions is no longer supported (id={rule_id}); "
                "use record_rule.version + record_rule.key"
            )

        term_column = str(raw_rule.get("term_column", "")).strip()
        if not term_column:
            raise ValueError(f"record_rule.term_column is required (id={rule_id})")

        versions = self._parse_record_rule_versions(raw_rule.get("version"), rule_id)
        key_terms = self._parse_list_value(
            raw_rule.get("key"),
            f"record_rule.key (id={rule_id})",
            required=True,
        )
        key_regex = bool(raw_rule.get("key_regex", False))
        if key_regex:
            self._validate_regex_patterns(key_terms, f"record_rule.key (id={rule_id})")

        return RecordRule(
            id=rule_id,
            type="record_rule",
            enabled=enabled,
            skip_header=bool(raw_rule.get("skip_header", True)),
            term_column=term_column,
            versions=versions,
            key_terms=key_terms,
            key_regex=key_regex,
        )

    def _parse_record_rule_versions(self, value: Any, rule_id: str) -> tuple[str, ...]:
        # Missing/empty/"*"/"all" means no version filtering.
        if value is None:
            return tuple()
        versions = self._parse_list_value(
            value,
            f"record_rule.version (id={rule_id})",
            required=False,
        )
        if not versions:
            return tuple()
        lowered = {item.strip().lower() for item in versions}
        if "*" in lowered or "all" in lowered:
            return tuple()
        return versions

    def _parse_tag_span_rule(self, raw_rule: dict[str, Any]) -> TagSpanRule:
        rule_id, enabled = self._parse_rule_identity(raw_rule, "tag_span")
        source_columns = self._parse_source_columns(raw_rule, rule_id, "tag_span")
        open_tags = self._parse_tag_span_open_tags(raw_rule, rule_id)
        close_tags = raw_rule.get("close_tags") or ["</tag>", "</>"]
        if not isinstance(close_tags, list) or not close_tags:
            raise ValueError(f"tag_span.close_tags must be non-empty list (id={rule_id})")

        return TagSpanRule(
            id=rule_id,
            type="tag_span",
            enabled=enabled,
            source_columns=source_columns,
            open_tags=open_tags,
            close_tags=tuple(str(item) for item in close_tags),
        )

    def _parse_tag_span_open_tags(self, raw_rule: dict[str, Any], rule_id: str) -> tuple[str, ...]:
        if "open_tags" in raw_rule:
            return self._parse_list_value(
                raw_rule.get("open_tags"),
                f"tag_span.open_tags (id={rule_id})",
                required=True,
            )
        if "open_tag" in raw_rule:
            return self._parse_list_value(
                raw_rule.get("open_tag"),
                f"tag_span.open_tag (id={rule_id})",
                required=True,
            )
        return ("<tag>",)

    def _parse_compound_split_rule(self, raw_rule: dict[str, Any]) -> CompoundSplitRule:
        rule_id, enabled = self._parse_rule_identity(raw_rule, "compound_split")
        source_columns = self._parse_source_columns(raw_rule, rule_id, "compound_split")
        delimiter = str(raw_rule.get("delimiter", "·"))
        if not delimiter:
            raise ValueError(f"compound_split.delimiter is required (id={rule_id})")

        return CompoundSplitRule(
            id=rule_id,
            type="compound_split",
            enabled=enabled,
            source_columns=source_columns,
            delimiter=delimiter,
            emit_compound=bool(raw_rule.get("emit_compound", True)),
            emit_head=bool(raw_rule.get("emit_head", True)),
            emit_suffix=bool(raw_rule.get("emit_suffix", True)),
        )

    @staticmethod
    def _parse_source_columns(raw_rule: dict[str, Any], rule_id: str, extractor_type: str) -> tuple[str, ...]:
        columns = raw_rule.get("source_columns")
        if not isinstance(columns, list) or not columns:
            raise ValueError(f"{extractor_type}.source_columns must be a non-empty list (id={rule_id})")
        result = tuple(str(item).strip() for item in columns if str(item).strip())
        if not result:
            raise ValueError(f"{extractor_type}.source_columns cannot be blank (id={rule_id})")
        return result

    @staticmethod
    def _parse_list_value(value: Any, field_name: str, required: bool) -> tuple[str, ...]:
        if value is None:
            if required:
                raise ValueError(f"{field_name} is required")
            return tuple()

        result: list[str] = []
        if isinstance(value, str):
            result = [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    result.append(text)
        else:
            raise ValueError(f"{field_name} must be list or comma-separated string")

        if required and not result:
            raise ValueError(f"{field_name} cannot be empty")
        return tuple(result)

    def _parse_file_filters(self, value: Any) -> tuple[str, ...]:
        # Empty/omitted files means "process all discovered files".
        if value is None:
            return tuple()
        filters = self._parse_list_value(value, "files", required=False)
        if not filters:
            return tuple()
        lowered = {item.strip().lower() for item in filters}
        if "*" in lowered or "all" in lowered:
            return tuple()
        return filters

    @staticmethod
    def _validate_regex_patterns(patterns: tuple[str, ...], field_name: str) -> None:
        for pattern in patterns:
            try:
                re.compile(pattern, flags=re.IGNORECASE)
            except re.error as exc:
                raise ValueError(f"{field_name} contains invalid regex: {pattern} ({exc})") from exc
