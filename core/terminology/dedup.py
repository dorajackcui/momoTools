from collections import defaultdict

from .types import NormalizedCandidate, TermEntry, TermOccurrence


def build_terms_and_occurrences(
    normalized_candidates: list[NormalizedCandidate],
) -> tuple[list[TermEntry], list[TermOccurrence], dict[str, str], dict[str, str], dict[str, str]]:
    grouped: dict[str, list[NormalizedCandidate]] = defaultdict(list)
    for item in normalized_candidates:
        grouped[item.dedup_key].append(item)

    terms: list[TermEntry] = []
    occurrences: list[TermOccurrence] = []
    candidate_to_term_id: dict[str, str] = {}
    dedup_to_term_id: dict[str, str] = {}
    term_text_to_term_id: dict[str, str] = {}

    for index, dedup_key in enumerate(sorted(grouped.keys()), start=1):
        items = grouped[dedup_key]
        first = items[0]
        term_id = f"T{index:06d}"
        dedup_to_term_id[dedup_key] = term_id
        term_text_to_term_id[first.term_norm] = term_id

        files = {entry.candidate.file for entry in items}
        terms.append(
            TermEntry(
                term_id=term_id,
                term_norm=first.term_norm,
                dedup_key=dedup_key,
                occurrences_count=len(items),
                files_count=len(files),
                first_extractor=first.candidate.extractor_type,
            )
        )

        for entry in items:
            candidate_to_term_id[entry.candidate_id] = term_id
            occurrences.append(
                TermOccurrence(
                    term_id=term_id,
                    term_norm=first.term_norm,
                    candidate=entry.candidate,
                )
            )

    return terms, occurrences, candidate_to_term_id, dedup_to_term_id, term_text_to_term_id


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
