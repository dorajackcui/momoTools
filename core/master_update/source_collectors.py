import os
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from core.kernel import build_combined_key, open_workbook, safe_to_str
from .policies import ROW_KEY_POLICY_COMBINED, ROW_KEY_POLICY_KEY_ONLY
from .io_helpers import (
    UNSET,
    merge_non_blank_cells_by_policy,
    normalize_content_row_values,
    normalize_content_value,
)
from .reporting import UnmatchedIdentityInfo


@dataclass(frozen=True)
class SourceCandidates:
    rows: dict[str, list[Any]]
    touched_cols_by_key: dict[str, set[int]]
    unmatched_info_by_key: dict[str, UnmatchedIdentityInfo]


@dataclass(frozen=True)
class DenseSourceRows:
    rows: dict[str, list[Any]]


def build_identity_key_from_values(
    *,
    row_values: Sequence[Any],
    key_col: int,
    match_col: int,
    row_key_policy: str,
    key_separator: str,
) -> str | None:
    key_value = row_values[key_col] if key_col < len(row_values) else None
    if row_key_policy == ROW_KEY_POLICY_COMBINED:
        return build_combined_key(
            key_value,
            row_values[match_col] if match_col < len(row_values) else None,
            separator=key_separator,
        )
    if row_key_policy == ROW_KEY_POLICY_KEY_ONLY:
        key_text = safe_to_str(key_value, strip=True)
        return key_text if key_text else None
    raise ValueError(f"Unsupported row_key_policy: {row_key_policy}")


def _scan_source_files(
    *,
    source_files: Sequence[str],
    key_col: int,
    match_col: int,
    row_key_policy: str,
    max_col: int,
    key_separator: str,
    on_log: Callable[[str], None],
    on_log_error: Callable[..., None],
    stats,
    on_identity_row: Callable[[str, Sequence[Any], str], None],
):
    for file_index, file_path in enumerate(source_files, start=1):
        on_log(f"Merging source [{file_index}/{len(source_files)}]: {os.path.basename(file_path)}")
        try:
            with open_workbook(file_path, read_only=True, keep_links=False) as workbook:
                worksheet = workbook.active
                for row_values in worksheet.iter_rows(
                    min_row=2,
                    min_col=1,
                    max_col=max_col,
                    values_only=True,
                ):
                    identity_key = build_identity_key_from_values(
                        row_values=row_values,
                        key_col=key_col,
                        match_col=match_col,
                        row_key_policy=row_key_policy,
                        key_separator=key_separator,
                    )
                    if not identity_key:
                        continue
                    stats.rows_scanned += 1
                    on_identity_row(identity_key, row_values, file_path)
            stats.files_succeeded += 1
        except Exception as exc:
            stats.files_failed += 1
            on_log_error(
                "E_SOURCE_READ",
                "Failed to read update source file",
                file_path=file_path,
                exc=exc,
            )


def collect_source_candidates(
    *,
    source_files: Sequence[str],
    key_col: int,
    match_col: int,
    row_key_policy: str,
    max_col: int,
    content_col_indexes: Sequence[int],
    cell_write_policy: str,
    priority_winner_policy: str,
    key_separator: str,
    on_log: Callable[[str], None],
    on_log_error: Callable[..., None],
    stats,
) -> SourceCandidates:
    candidate_rows: dict[str, list[Any]] = {}
    touched_cols_by_key: dict[str, set[int]] = {}
    unmatched_info_by_identity: dict[str, UnmatchedIdentityInfo] = {}
    content_col_set = set(content_col_indexes)

    def _on_identity_row(identity_key: str, row_values: Sequence[Any], file_path: str):
        key_text = safe_to_str(
            row_values[key_col] if key_col < len(row_values) else None,
            strip=True,
        )
        match_text = safe_to_str(
            row_values[match_col] if match_col < len(row_values) else None,
            strip=True,
        )
        is_new_identity = identity_key not in candidate_rows
        if identity_key not in candidate_rows:
            base_row = [UNSET] * max_col
            base_row[key_col] = key_text
            base_row[match_col] = (
                normalize_content_value(
                    row_values[match_col] if match_col < len(row_values) else None
                )
                if match_col in content_col_set
                else match_text
            )
            candidate_rows[identity_key] = base_row
            touched_cols_by_key[identity_key] = set()

        touched_cols_for_row: set[int] = set()

        merge_non_blank_cells_by_policy(
            target_row=candidate_rows[identity_key],
            source_row=row_values,
            content_col_indexes=content_col_indexes,
            cell_write_policy=cell_write_policy,
            priority_winner_policy=priority_winner_policy,
            touched_cols=touched_cols_for_row,
        )
        if touched_cols_for_row:
            touched_cols_by_key[identity_key].update(touched_cols_for_row)
        if is_new_identity or touched_cols_for_row:
            unmatched_info_by_identity[identity_key] = UnmatchedIdentityInfo(
                key_text=key_text,
                match_text=match_text,
                source_file=os.path.basename(file_path),
                content_values=tuple(
                    None if candidate_rows[identity_key][col_idx] is UNSET else candidate_rows[identity_key][col_idx]
                    for col_idx in content_col_indexes
                ),
            )

    _scan_source_files(
        source_files=source_files,
        key_col=key_col,
        match_col=match_col,
        row_key_policy=row_key_policy,
        max_col=max_col,
        key_separator=key_separator,
        on_log=on_log,
        on_log_error=on_log_error,
        stats=stats,
        on_identity_row=_on_identity_row,
    )

    return SourceCandidates(
        rows=candidate_rows,
        touched_cols_by_key=touched_cols_by_key,
        unmatched_info_by_key=unmatched_info_by_identity,
    )


def collect_source_rows_dense(
    *,
    source_files: Sequence[str],
    key_col: int,
    match_col: int,
    row_key_policy: str,
    max_col: int,
    content_col_indexes: Sequence[int],
    key_separator: str,
    on_log: Callable[[str], None],
    on_log_error: Callable[..., None],
    stats,
) -> DenseSourceRows:
    candidate_rows: dict[str, list[Any]] = {}
    content_col_set = set(content_col_indexes)

    def _on_identity_row(identity_key: str, row_values: Sequence[Any], _file_path: str):
        row_buffer = normalize_content_row_values(
            row_values=row_values,
            max_col=max_col,
            content_col_indexes=content_col_indexes,
        )
        row_buffer[key_col] = safe_to_str(
            row_values[key_col] if key_col < len(row_values) else None,
            strip=True,
        )
        if match_col not in content_col_set:
            row_buffer[match_col] = safe_to_str(
                row_values[match_col] if match_col < len(row_values) else None,
                strip=True,
            )
        # Dense Update Master mode treats source rows as complete.
        # For duplicate identities, later processed rows replace the whole row.
        candidate_rows[identity_key] = row_buffer

    _scan_source_files(
        source_files=source_files,
        key_col=key_col,
        match_col=match_col,
        row_key_policy=row_key_policy,
        max_col=max_col,
        key_separator=key_separator,
        on_log=on_log,
        on_log_error=on_log_error,
        stats=stats,
        on_identity_row=_on_identity_row,
    )

    return DenseSourceRows(rows=candidate_rows)
