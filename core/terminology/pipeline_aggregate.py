from dataclasses import dataclass

from .dedup import build_term_aggregates, build_terms_and_occurrences
from .normalize import normalize_candidates
from .relations import build_relation_summary, build_review_items
from .types import (
    Candidate,
    RelationSummaryRow,
    ReviewItem,
    TermEntry,
    TermOccurrence,
    TerminologyConfig,
    TermSummaryRow,
)


@dataclass(frozen=True)
class AggregationResult:
    terms: list[TermEntry]
    occurrences: list[TermOccurrence]
    terms_summary_rows: list[TermSummaryRow]
    relations_summary_rows: list[RelationSummaryRow]
    review_items: list[ReviewItem]
    normalized_count: int
    body_terms_count: int
    suffix_terms_count: int


def aggregate_terminology(
    candidates: list[Candidate],
    config: TerminologyConfig,
) -> AggregationResult:
    normalized = normalize_candidates(candidates, config.normalization)
    terms, occurrences, _candidate_to_term_ids, dedup_to_term_id, _term_text_to_term_id = build_terms_and_occurrences(
        normalized_candidates=normalized,
        normalization_settings=config.normalization,
        affix_delimiters=config.affix_delimiters,
    )
    term_by_id = {term.term_id: term for term in terms}

    review_items, reasons_by_term = build_review_items(
        terms=terms,
        occurrences=occurrences,
        thresholds=config.thresholds,
    )
    apply_review_reasons(terms, reasons_by_term)

    term_aggregates = build_term_aggregates(occurrences)
    terms_summary_rows = build_terms_summary_rows(terms, term_aggregates)
    relations_summary_rows = build_relation_summary(
        terms=terms,
        occurrences=occurrences,
        candidates=candidates,
        normalization_settings=config.normalization,
        dedup_to_term_id=dedup_to_term_id,
        term_by_id=term_by_id,
        affix_delimiters=config.affix_delimiters,
    )

    body_terms_count = sum(1 for term in terms if term.term_type == "body")
    suffix_terms_count = sum(1 for term in terms if term.term_type == "suffix")

    return AggregationResult(
        terms=terms,
        occurrences=occurrences,
        terms_summary_rows=terms_summary_rows,
        relations_summary_rows=relations_summary_rows,
        review_items=review_items,
        normalized_count=len(normalized),
        body_terms_count=body_terms_count,
        suffix_terms_count=suffix_terms_count,
    )


def apply_review_reasons(terms: list[TermEntry], reasons_by_term: dict[str, list[str]]) -> None:
    for term in terms:
        reasons = reasons_by_term.get(term.term_id, [])
        term.is_low_confidence = bool(reasons)
        term.review_reasons = ";".join(reasons)


def build_terms_summary_rows(
    terms: list[TermEntry],
    term_aggregates: dict[str, dict[str, str | int | set[str]]],
) -> list[TermSummaryRow]:
    rows: list[TermSummaryRow] = []
    for term in sorted(terms, key=lambda item: (item.term_type, item.term_norm, item.term_id)):
        aggregate = term_aggregates.get(term.term_id, {})
        files_count = int(aggregate.get("files_count", term.files_count))
        files_list = str(aggregate.get("files_list", ""))
        keys_count = int(aggregate.get("keys_count", 0))
        keys_list = str(aggregate.get("keys_list", ""))
        rows.append(
            TermSummaryRow(
                term_id=term.term_id,
                term_type=term.term_type,
                term_norm=term.term_norm,
                occurrences_count=term.occurrences_count,
                files_count=files_count,
                files_list=files_list,
                keys_count=keys_count,
                keys_list=keys_list,
                first_extractor=term.first_extractor,
                is_low_confidence=term.is_low_confidence,
                review_reasons=term.review_reasons,
            )
        )
    return rows
