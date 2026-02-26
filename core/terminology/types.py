from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecordRule:
    id: str
    type: str
    enabled: bool
    skip_header: bool
    term_column: str
    versions: tuple[str, ...]
    key_terms: tuple[str, ...]
    key_regex: bool = False


@dataclass(frozen=True)
class TagSpanRule:
    id: str
    type: str
    enabled: bool
    source_columns: tuple[str, ...]
    open_tags: tuple[str, ...]
    close_tags: tuple[str, ...]


@dataclass(frozen=True)
class CompoundSplitRule:
    id: str
    type: str
    enabled: bool
    source_columns: tuple[str, ...]
    delimiter: str
    emit_compound: bool
    emit_head: bool
    emit_suffix: bool


ExtractorRule = RecordRule | TagSpanRule | CompoundSplitRule


@dataclass(frozen=True)
class PunctuationNormalization:
    enabled: bool
    mapping: dict[str, str]


@dataclass(frozen=True)
class NormalizationSettings:
    trim: bool
    collapse_whitespace: bool
    punctuation: PunctuationNormalization
    min_term_length: int
    case_insensitive_dedup: bool


@dataclass(frozen=True)
class ThresholdSettings:
    containment_min_len: int
    review_short_len_le: int
    review_noise_ratio_ge: float


@dataclass(frozen=True)
class TerminologyConfig:
    version: int
    files: tuple[str, ...]
    compound_delimiters: tuple[str, ...]
    normalization: NormalizationSettings
    thresholds: ThresholdSettings
    extractors: tuple[ExtractorRule, ...]


@dataclass
class Candidate:
    term_raw: str
    extractor_type: str
    rule_id: str
    file: str
    sheet: str
    row: int
    col: int
    cell_raw: str
    meta: dict[str, Any] = field(default_factory=dict)
    candidate_id: str = ""


@dataclass(frozen=True)
class NormalizedCandidate:
    candidate_id: str
    term_norm: str
    dedup_key: str
    candidate: Candidate


@dataclass
class TermEntry:
    term_id: str
    term_norm: str
    dedup_key: str
    occurrences_count: int
    files_count: int
    first_extractor: str
    is_low_confidence: bool = False
    review_reasons: str = ""


@dataclass(frozen=True)
class TermOccurrence:
    term_id: str
    term_norm: str
    candidate: Candidate


@dataclass(frozen=True)
class TermRelation:
    source_term_id: str
    source_term: str
    relation_type: str
    target_term_id: str
    target_term: str
    evidence_count: int
    confidence: float
    rule_id: str


@dataclass(frozen=True)
class ReviewItem:
    term_id: str
    term_norm: str
    reason: str
    severity: str
    occurrences_count: int
    sample_file: str
    sample_row: int
    sample_col: int


@dataclass(frozen=True)
class TermSummaryRow:
    term_id: str
    term_norm: str
    occurrences_count: int
    files_count: int
    files_list: str
    keys_count: int
    keys_list: str
    first_extractor: str
    is_low_confidence: bool
    review_reasons: str


@dataclass(frozen=True)
class RelationSummaryRow:
    relation_group: str
    anchor_term: str
    members_count: int
    members_list: str
    evidence_count: int
    notes: str = ""
