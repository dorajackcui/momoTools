import os
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from core.kernel import build_combined_key, open_workbook, safe_to_str
from .policies import ROW_KEY_POLICY_COMBINED, ROW_KEY_POLICY_KEY_ONLY
from .io_helpers import UNSET, merge_non_blank_cells_by_policy


@dataclass(frozen=True)
class SourceCandidates:
    rows: dict[str, list[Any]]
    touched_cols_by_key: dict[str, set[int]]


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
    on_identity_row: Callable[[str, Sequence[Any]], None],
):
    for file_index, file_path in enumerate(source_files, start=1):
        on_log(f"Merging source [{file_index}/{len(source_files)}]: {os.path.basename(file_path)}")
        try:
            with open_workbook(file_path, read_only=True) as workbook:
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
                    on_identity_row(identity_key, row_values)
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

    def _on_identity_row(identity_key: str, row_values: Sequence[Any]):
        if identity_key not in candidate_rows:
            base_row = [UNSET] * max_col
            base_row[key_col] = safe_to_str(
                row_values[key_col] if key_col < len(row_values) else None,
                strip=True,
            )
            base_row[match_col] = safe_to_str(
                row_values[match_col] if match_col < len(row_values) else None,
                strip=True,
            )
            candidate_rows[identity_key] = base_row
            touched_cols_by_key[identity_key] = set()

        merge_non_blank_cells_by_policy(
            target_row=candidate_rows[identity_key],
            source_row=row_values,
            content_col_indexes=content_col_indexes,
            cell_write_policy=cell_write_policy,
            priority_winner_policy=priority_winner_policy,
            touched_cols=touched_cols_by_key[identity_key],
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
    )


def collect_source_rows_dense(
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
) -> DenseSourceRows:
    candidate_rows: dict[str, list[Any]] = {}

    def _on_identity_row(identity_key: str, row_values: Sequence[Any]):
        row_buffer = [
            row_values[col_idx] if col_idx < len(row_values) else None
            for col_idx in range(max_col)
        ]
        row_buffer[key_col] = safe_to_str(
            row_values[key_col] if key_col < len(row_values) else None,
            strip=True,
        )
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
