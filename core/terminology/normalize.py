import re

from .types import Candidate, NormalizationSettings, NormalizedCandidate


def normalize_term(term_raw: str, settings: NormalizationSettings) -> str:
    text = term_raw
    if settings.trim:
        text = text.strip()
    if settings.collapse_whitespace:
        text = re.sub(r"\s+", " ", text)
    if settings.punctuation.enabled:
        for src, dst in settings.punctuation.mapping.items():
            text = text.replace(src, dst)
    return text


def build_dedup_key(term_norm: str, case_insensitive: bool) -> str:
    if case_insensitive:
        return term_norm.lower()
    return term_norm


def normalize_candidates(
    candidates: list[Candidate],
    settings: NormalizationSettings,
) -> list[NormalizedCandidate]:
    normalized: list[NormalizedCandidate] = []
    for candidate in candidates:
        term_norm = normalize_term(candidate.term_raw, settings)
        if len(term_norm) < settings.min_term_length:
            continue
        dedup_key = build_dedup_key(term_norm, settings.case_insensitive_dedup)
        normalized.append(
            NormalizedCandidate(
                candidate_id=candidate.candidate_id,
                term_norm=term_norm,
                dedup_key=dedup_key,
                candidate=candidate,
            )
        )
    return normalized
