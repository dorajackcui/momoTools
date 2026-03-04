from typing import Any, Sequence

from core.kernel import is_blank_value
from .policies import (
    CELL_WRITE_POLICY_FILL_BLANK_ONLY,
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
)

UNSET = object()


def merge_non_blank_cells_by_policy(
    *,
    target_row: list[Any],
    source_row: Sequence[Any],
    content_col_indexes: Sequence[int],
    cell_write_policy: str,
    priority_winner_policy: str,
    touched_cols: set[int] | None = None,
):
    for col_idx in content_col_indexes:
        source_value = source_row[col_idx] if col_idx < len(source_row) else None
        if is_blank_value(source_value):
            continue

        current_value = target_row[col_idx]
        if cell_write_policy == CELL_WRITE_POLICY_FILL_BLANK_ONLY:
            if (current_value is not UNSET) and (not is_blank_value(current_value)):
                continue
            target_row[col_idx] = source_value
            if touched_cols is not None:
                touched_cols.add(col_idx)
            continue

        if cell_write_policy == CELL_WRITE_POLICY_OVERWRITE_NON_BLANK:
            if priority_winner_policy == PRIORITY_WINNER_POLICY_LAST_PROCESSED:
                target_row[col_idx] = source_value
                if touched_cols is not None:
                    touched_cols.add(col_idx)
                continue
            continue

        raise ValueError(f"Unsupported cell_write_policy: {cell_write_policy}")


def values_equivalent(old_value: Any, new_value: Any) -> bool:
    if is_blank_value(old_value) and is_blank_value(new_value):
        return True
    return old_value == new_value
