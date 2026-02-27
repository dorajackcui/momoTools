import re

from .dedup import build_term_aggregates
from .normalize import build_dedup_key
from .types import RelationSummaryRow, ReviewItem, TermEntry, TermOccurrence, TermRelation, ThresholdSettings


def build_relations(
    terms: list[TermEntry],
    occurrences: list[TermOccurrence],
    thresholds: ThresholdSettings,
    case_insensitive_dedup: bool,
    dedup_to_term_id: dict[str, str],
    term_by_id: dict[str, TermEntry],
    compound_delimiters: tuple[str, ...] = ("·",),
) -> list[TermRelation]:
    relations: list[TermRelation] = []
    relations.extend(_build_containment_relations(terms, thresholds.containment_min_len))
    relations.extend(
        _build_compound_relations_from_terms(
            terms=terms,
            case_insensitive_dedup=case_insensitive_dedup,
            compound_delimiters=compound_delimiters,
            term_by_id=term_by_id,
        )
    )
    return relations


def build_relation_summary(
    terms: list[TermEntry],
    occurrences: list[TermOccurrence],
    relations: list[TermRelation],
) -> list[RelationSummaryRow]:
    rows: list[RelationSummaryRow] = []
    term_aggregates = build_term_aggregates(occurrences)

    for term in sorted(terms, key=lambda item: item.term_norm):
        aggregate = term_aggregates.get(term.term_id, {})
        files_count = int(aggregate.get("files_count", term.files_count))
        files_list = str(aggregate.get("files_list", ""))
        rows.append(
            RelationSummaryRow(
                relation_group="file_presence",
                anchor_term=term.term_norm,
                members_count=files_count,
                members_list=files_list,
                evidence_count=term.occurrences_count,
                notes="",
            )
        )

    suffix_members: dict[str, set[str]] = {}
    suffix_evidence: dict[str, int] = {}
    prefix_members: dict[str, set[str]] = {}
    prefix_evidence: dict[str, int] = {}

    for relation in relations:
        if relation.relation_type != "head_suffix_pair":
            continue

        head = relation.source_term
        suffix = relation.target_term

        suffix_members.setdefault(head, set()).add(suffix)
        suffix_evidence[head] = suffix_evidence.get(head, 0) + relation.evidence_count

        prefix_members.setdefault(suffix, set()).add(head)
        prefix_evidence[suffix] = prefix_evidence.get(suffix, 0) + relation.evidence_count

    for anchor in sorted(suffix_members.keys()):
        members = sorted(suffix_members[anchor])
        rows.append(
            RelationSummaryRow(
                relation_group="suffix_family",
                anchor_term=anchor,
                members_count=len(members),
                members_list=";".join(members),
                evidence_count=suffix_evidence.get(anchor, 0),
                notes="",
            )
        )

    for anchor in sorted(prefix_members.keys()):
        members = sorted(prefix_members[anchor])
        rows.append(
            RelationSummaryRow(
                relation_group="prefix_family",
                anchor_term=anchor,
                members_count=len(members),
                members_list=";".join(members),
                evidence_count=prefix_evidence.get(anchor, 0),
                notes="",
            )
        )

    return rows


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


def _build_containment_relations(terms: list[TermEntry], min_len: int) -> list[TermRelation]:
    relations: list[TermRelation] = []
    for short in terms:
        if len(short.term_norm) < min_len:
            continue
        for long in terms:
            if short.term_id == long.term_id:
                continue
            if short.term_norm in long.term_norm:
                relations.append(
                    TermRelation(
                        source_term_id=short.term_id,
                        source_term=short.term_norm,
                        relation_type="variant_of",
                        target_term_id=long.term_id,
                        target_term=long.term_norm,
                        evidence_count=1,
                        confidence=0.7,
                        rule_id="containment_simple",
                    )
                )
    return _dedup_relations(relations)


def _build_compound_relations_from_terms(
    terms: list[TermEntry],
    case_insensitive_dedup: bool,
    compound_delimiters: tuple[str, ...],
    term_by_id: dict[str, TermEntry],
) -> list[TermRelation]:
    delimiters = tuple(item for item in compound_delimiters if str(item).strip())
    if not delimiters:
        delimiters = ("·",)

    dedup_to_term_id: dict[str, str] = {
        build_dedup_key(term.term_norm, case_insensitive_dedup): term.term_id
        for term in terms
    }

    relations: list[TermRelation] = []
    for compound_term in terms:
        compound_text = compound_term.term_norm
        for delimiter in delimiters:
            if delimiter not in compound_text:
                continue

            head_text, suffix_text = compound_text.split(delimiter, 1)
            head_text = head_text.strip()
            suffix_text = suffix_text.strip()
            if not head_text or not suffix_text:
                continue

            head_id = dedup_to_term_id.get(build_dedup_key(head_text, case_insensitive_dedup))
            suffix_id = dedup_to_term_id.get(build_dedup_key(suffix_text, case_insensitive_dedup))
            if not head_id or not suffix_id:
                continue

            relations.append(
                TermRelation(
                    source_term_id=compound_term.term_id,
                    source_term=compound_text,
                    relation_type="has_head",
                    target_term_id=head_id,
                    target_term=term_by_id[head_id].term_norm,
                    evidence_count=1,
                    confidence=1.0,
                    rule_id="compound_postprocess",
                )
            )
            relations.append(
                TermRelation(
                    source_term_id=compound_term.term_id,
                    source_term=compound_text,
                    relation_type="has_suffix",
                    target_term_id=suffix_id,
                    target_term=term_by_id[suffix_id].term_norm,
                    evidence_count=1,
                    confidence=1.0,
                    rule_id="compound_postprocess",
                )
            )
            relations.append(
                TermRelation(
                    source_term_id=head_id,
                    source_term=term_by_id[head_id].term_norm,
                    relation_type="head_suffix_pair",
                    target_term_id=suffix_id,
                    target_term=term_by_id[suffix_id].term_norm,
                    evidence_count=1,
                    confidence=1.0,
                    rule_id="compound_postprocess",
                )
            )

    return _dedup_relations(relations)


def _dedup_relations(relations: list[TermRelation]) -> list[TermRelation]:
    merged: dict[tuple[str, str, str, str], TermRelation] = {}
    for rel in relations:
        key = (
            rel.source_term_id,
            rel.relation_type,
            rel.target_term_id,
            rel.rule_id,
        )
        existing = merged.get(key)
        if existing is None:
            merged[key] = rel
        else:
            merged[key] = TermRelation(
                source_term_id=existing.source_term_id,
                source_term=existing.source_term,
                relation_type=existing.relation_type,
                target_term_id=existing.target_term_id,
                target_term=existing.target_term,
                evidence_count=existing.evidence_count + rel.evidence_count,
                confidence=max(existing.confidence, rel.confidence),
                rule_id=existing.rule_id,
            )
    return list(merged.values())


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
