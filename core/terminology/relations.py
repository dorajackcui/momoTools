import re
from collections import defaultdict

from .dedup import build_term_aggregates, split_term_by_first_delimiter
from .normalize import build_dedup_key, normalize_term
from .types import (
    Candidate,
    NormalizationSettings,
    RelationSummaryRow,
    ReviewItem,
    TermEntry,
    TermOccurrence,
    ThresholdSettings,
)


def build_cross_file_rows(
    terms: list[TermEntry],
    occurrences: list[TermOccurrence],
) -> list[RelationSummaryRow]:
    rows: list[RelationSummaryRow] = []
    term_aggregates = build_term_aggregates(occurrences)
    for term in sorted(terms, key=lambda item: (item.term_type, item.term_norm, item.term_id)):
        aggregate = term_aggregates.get(term.term_id, {})
        files_count = int(aggregate.get("files_count", term.files_count))
        if files_count < 2:
            continue
        files_list = str(aggregate.get("files_list", ""))
        rows.append(
            RelationSummaryRow(
                relation_type="cross_file",
                evidence_count=term.occurrences_count,
                cross_term=term.term_norm,
                cross_files_count=files_count,
                cross_files_list=files_list,
                notes="",
            )
        )
    return rows


def build_affix_group_rows(
    candidates: list[Candidate],
    normalization_settings: NormalizationSettings,
    dedup_to_term_id: dict[tuple[str, str], str],
    term_by_id: dict[str, TermEntry],
    affix_delimiters: tuple[str, ...],
) -> list[RelationSummaryRow]:
    delimiters = tuple(item for item in affix_delimiters if str(item).strip())
    if not delimiters:
        delimiters = ("\u00b7", ":")

    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    pair_delimiters: dict[tuple[str, str], set[str]] = defaultdict(set)
    body_key_to_display: dict[str, str] = {}
    suffix_key_to_display: dict[str, str] = {}

    for candidate in candidates:
        split_result = split_term_by_first_delimiter(candidate.term_raw, delimiters)
        if split_result is None:
            continue
        body_raw, suffix_raw, delimiter = split_result

        body_norm = normalize_term(body_raw, normalization_settings)
        suffix_norm = normalize_term(suffix_raw, normalization_settings)
        if not body_norm or not suffix_norm:
            continue

        body_dedup_key = build_dedup_key(body_norm, normalization_settings.case_insensitive_dedup)
        suffix_dedup_key = build_dedup_key(suffix_norm, normalization_settings.case_insensitive_dedup)

        body_term_id = dedup_to_term_id.get(("body", body_dedup_key))
        suffix_term_id = dedup_to_term_id.get(("suffix", suffix_dedup_key))
        if not body_term_id or not suffix_term_id:
            continue

        body_display = term_by_id[body_term_id].term_norm
        suffix_display = term_by_id[suffix_term_id].term_norm
        body_key_to_display.setdefault(body_dedup_key, body_display)
        suffix_key_to_display.setdefault(suffix_dedup_key, suffix_display)

        pair_key = (body_dedup_key, suffix_dedup_key)
        pair_counts[pair_key] += 1
        pair_delimiters[pair_key].add(delimiter)

    body_related_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    body_delimiters: dict[str, set[str]] = defaultdict(set)
    suffix_related_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    suffix_delimiters: dict[str, set[str]] = defaultdict(set)

    for (body_key, suffix_key), count in pair_counts.items():
        body_related_counts[body_key][suffix_key] += count
        suffix_related_counts[suffix_key][body_key] += count

        delimiters_for_pair = pair_delimiters.get((body_key, suffix_key), set())
        body_delimiters[body_key].update(delimiters_for_pair)
        suffix_delimiters[suffix_key].update(delimiters_for_pair)

    rows: list[RelationSummaryRow] = []

    for body_key in sorted(body_related_counts.keys(), key=lambda item: body_key_to_display.get(item, item)):
        anchor_term = body_key_to_display.get(body_key, body_key)
        related_keys = sorted(body_related_counts[body_key].keys(), key=lambda item: suffix_key_to_display.get(item, item))
        related_terms = [suffix_key_to_display.get(item, item) for item in related_keys]
        evidence_count = sum(body_related_counts[body_key].values())
        rows.append(
            RelationSummaryRow(
                relation_type="affix_group",
                evidence_count=evidence_count,
                affix_role="prefix_anchor",
                affix_anchor_term=anchor_term,
                affix_related_count=len(related_terms),
                affix_related_list=";".join(related_terms),
                affix_delimiters=";".join(sorted(body_delimiters.get(body_key, set()))),
                notes="",
            )
        )

    for suffix_key in sorted(suffix_related_counts.keys(), key=lambda item: suffix_key_to_display.get(item, item)):
        anchor_term = suffix_key_to_display.get(suffix_key, suffix_key)
        related_keys = sorted(suffix_related_counts[suffix_key].keys(), key=lambda item: body_key_to_display.get(item, item))
        related_terms = [body_key_to_display.get(item, item) for item in related_keys]
        evidence_count = sum(suffix_related_counts[suffix_key].values())
        rows.append(
            RelationSummaryRow(
                relation_type="affix_group",
                evidence_count=evidence_count,
                affix_role="suffix_anchor",
                affix_anchor_term=anchor_term,
                affix_related_count=len(related_terms),
                affix_related_list=";".join(related_terms),
                affix_delimiters=";".join(sorted(suffix_delimiters.get(suffix_key, set()))),
                notes="",
            )
        )

    return rows


def build_relation_summary(
    terms: list[TermEntry],
    occurrences: list[TermOccurrence],
    candidates: list[Candidate],
    normalization_settings: NormalizationSettings,
    dedup_to_term_id: dict[tuple[str, str], str],
    term_by_id: dict[str, TermEntry],
    affix_delimiters: tuple[str, ...],
) -> list[RelationSummaryRow]:
    rows: list[RelationSummaryRow] = []
    rows.extend(build_cross_file_rows(terms, occurrences))
    # affix_group checks are independent from cross_file filtering.
    rows.extend(
        build_affix_group_rows(
            candidates=candidates,
            normalization_settings=normalization_settings,
            dedup_to_term_id=dedup_to_term_id,
            term_by_id=term_by_id,
            affix_delimiters=affix_delimiters,
        )
    )
    return sorted(
        rows,
        key=lambda row: (
            row.relation_type,
            row.affix_role,
            row.affix_anchor_term,
            row.affix_related_list,
            row.cross_term,
        ),
    )


def build_review_items(
    terms: list[TermEntry],
    occurrences: list[TermOccurrence],
    thresholds: ThresholdSettings,
) -> tuple[list[ReviewItem], dict[str, list[str]]]:
    sample_by_term: dict[str, TermOccurrence] = {}
    for occ in occurrences:
        if occ.term_id not in sample_by_term:
            sample_by_term[occ.term_id] = occ

    review_items: list[ReviewItem] = []
    reasons_by_term: dict[str, list[str]] = {}
    for term in terms:
        reasons = _term_review_reasons(term.term_norm, thresholds)
        if not reasons:
            continue
        reasons_by_term[term.term_id] = reasons
        sample = sample_by_term.get(term.term_id)
        sample_file = sample.candidate.file if sample else ""
        sample_row = sample.candidate.row if sample else 0
        sample_col = sample.candidate.col if sample else 0

        for reason in reasons:
            review_items.append(
                ReviewItem(
                    term_id=term.term_id,
                    term_norm=term.term_norm,
                    reason=reason,
                    severity="medium",
                    occurrences_count=term.occurrences_count,
                    sample_file=sample_file,
                    sample_row=sample_row,
                    sample_col=sample_col,
                )
            )

    return review_items, reasons_by_term


def _term_review_reasons(term: str, thresholds: ThresholdSettings) -> list[str]:
    reasons: list[str] = []
    if len(term) <= thresholds.review_short_len_le:
        reasons.append("too_short")

    if _is_symbol_or_number_heavy(term):
        reasons.append("symbol_or_number_heavy")

    if term:
        noise_ratio = _noise_ratio(term)
        if noise_ratio >= thresholds.review_noise_ratio_ge:
            reasons.append("high_noise_ratio")
    return reasons


def _is_symbol_or_number_heavy(term: str) -> bool:
    cleaned = term.strip()
    if not cleaned:
        return False
    return bool(re.fullmatch(r"[0-9\W_]+", cleaned, flags=re.UNICODE))


def _noise_ratio(term: str) -> float:
    if not term:
        return 0.0
    noise = 0
    for ch in term:
        if _is_signal_char(ch):
            continue
        noise += 1
    return noise / len(term)


def _is_signal_char(ch: str) -> bool:
    if ch.isalnum():
        return True
    code = ord(ch)
    return 0x4E00 <= code <= 0x9FFF
