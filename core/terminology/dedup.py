from collections import defaultdict
from dataclasses import dataclass

from .normalize import build_dedup_key, normalize_term
from .types import NormalizationSettings, NormalizedCandidate, TermEntry, TermOccurrence


@dataclass(frozen=True)
class _SplitTermCandidate:
    term_type: str
    dedup_key: str
    display_term: str
    normalized_candidate: NormalizedCandidate


def build_terms_and_occurrences(
    normalized_candidates: list[NormalizedCandidate],
    normalization_settings: NormalizationSettings,
    affix_delimiters: tuple[str, ...],
) -> tuple[
    list[TermEntry],
    list[TermOccurrence],
    dict[str, list[str]],
    dict[tuple[str, str], str],
    dict[str, str],
]:
    grouped: dict[tuple[str, str], list[_SplitTermCandidate]] = defaultdict(list)

    for item in normalized_candidates:
        for term_type, raw_text in _split_term_components(item.candidate.term_raw, affix_delimiters):
            term_norm = normalize_term(raw_text, normalization_settings)
            if len(term_norm) < normalization_settings.min_term_length:
                continue
            dedup_key = build_dedup_key(term_norm, normalization_settings.case_insensitive_dedup)
            grouped[(term_type, dedup_key)].append(
                _SplitTermCandidate(
                    term_type=term_type,
                    dedup_key=dedup_key,
                    display_term=raw_text,
                    normalized_candidate=item,
                )
            )

    terms: list[TermEntry] = []
    occurrences: list[TermOccurrence] = []
    candidate_to_term_ids: dict[str, list[str]] = {}
    dedup_to_term_id: dict[tuple[str, str], str] = {}
    term_text_to_term_id: dict[str, str] = {}

    sorted_keys = sorted(grouped.keys(), key=lambda it: (it[0], it[1]))
    for index, key in enumerate(sorted_keys, start=1):
        term_type, dedup_key = key
        items = grouped[key]
        first = items[0]
        term_id = f"T{index:06d}"
        dedup_to_term_id[(term_type, dedup_key)] = term_id
        term_text_to_term_id[f"{term_type}:{first.display_term}"] = term_id

        files = {entry.normalized_candidate.candidate.file for entry in items}
        terms.append(
            TermEntry(
                term_id=term_id,
                term_type=term_type,
                term_norm=first.display_term,
                dedup_key=dedup_key,
                occurrences_count=len(items),
                files_count=len(files),
                first_extractor=first.normalized_candidate.candidate.extractor_type,
            )
        )

        for entry in items:
            candidate_id = entry.normalized_candidate.candidate_id
            candidate_to_term_ids.setdefault(candidate_id, []).append(term_id)
            occurrences.append(
                TermOccurrence(
                    term_id=term_id,
                    term_type=term_type,
                    term_norm=first.display_term,
                    candidate=entry.normalized_candidate.candidate,
                )
            )

    return terms, occurrences, candidate_to_term_ids, dedup_to_term_id, term_text_to_term_id


def build_term_aggregates(
    occurrences: list[TermOccurrence],
) -> dict[str, dict[str, str | int | set[str]]]:
    grouped: dict[str, dict[str, str | int | set[str]]] = {}
    for occ in occurrences:
        entry = grouped.setdefault(
            occ.term_id,
            {
                "files_set": set(),
                "keys_set": set(),
            },
        )
        files_set = entry["files_set"]
        keys_set = entry["keys_set"]
        if isinstance(files_set, set):
            files_set.add(str(occ.candidate.file))
        key_value = str(occ.candidate.meta.get("key", "")).strip()
        if key_value and isinstance(keys_set, set):
            keys_set.add(key_value)

    for data in grouped.values():
        files_set = data["files_set"] if isinstance(data["files_set"], set) else set()
        keys_set = data["keys_set"] if isinstance(data["keys_set"], set) else set()
        files_sorted = sorted(files_set)
        keys_sorted = sorted(keys_set)
        data["files_count"] = len(files_sorted)
        data["files_list"] = ";".join(files_sorted)
        data["keys_count"] = len(keys_sorted)
        data["keys_list"] = ";".join(keys_sorted)
    return grouped


def split_term_by_first_delimiter(
    text: str,
    delimiters: tuple[str, ...],
) -> tuple[str, str, str] | None:
    cleaned_delimiters = tuple(item for item in delimiters if str(item)) or ("\u00b7", ":")

    best_index: int | None = None
    best_delimiter = ""

    for delimiter in cleaned_delimiters:
        index = text.find(delimiter)
        if index < 0:
            continue
        if best_index is None or index < best_index:
            best_index = index
            best_delimiter = delimiter

    if best_index is None:
        return None

    body_raw = text[:best_index].strip()
    suffix_payload = text[best_index + len(best_delimiter) :]
    if not body_raw.strip() or not suffix_payload.strip():
        return None

    suffix_raw = f"{best_delimiter}{suffix_payload}"
    return body_raw, suffix_raw, best_delimiter


def _split_term_components(term_raw: str, delimiters: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    split_result = split_term_by_first_delimiter(term_raw, delimiters)
    if split_result is None:
        return (("body", term_raw),)

    body_raw, suffix_raw, _delimiter = split_result
    return (("body", body_raw), ("suffix", suffix_raw))

