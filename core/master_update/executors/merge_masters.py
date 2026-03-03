import os
from typing import Any, Sequence

from core.kernel import is_blank_value, open_workbook, safe_to_str
from core.master_update.executors.base import BaseMasterUpdateExecutor
from core.master_update.io_helpers import (
    merge_non_blank_cells_fill_blank,
    read_row_values,
    values_equivalent,
)


class MergeMastersExecutor(BaseMasterUpdateExecutor):
    def run(self, source_files: Sequence[str]):
        max_col, content_col_indexes = self.resolve_layout()
        try:
            with open_workbook(self.processor.master_file_path, read_only=False) as workbook:
                worksheet = workbook.active

                master_rows_by_key: dict[str, list[int]] = {}
                merged_rows: dict[str, list[Any]] = {}

                for row_idx in range(2, worksheet.max_row + 1):
                    row_values = read_row_values(worksheet, row_idx, max_col)
                    identity_key = self.identity_key_from_row(row_values)
                    if not identity_key:
                        continue

                    self.processor.stats.rows_scanned += 1
                    master_rows_by_key.setdefault(identity_key, []).append(row_idx)
                    if identity_key not in merged_rows:
                        merged_rows[identity_key] = list(row_values)
                        continue

                    merge_non_blank_cells_fill_blank(
                        merged_rows[identity_key],
                        row_values,
                        content_col_indexes,
                    )
                    self.processor.log(
                        f"Duplicate key in master skipped for precedence: {identity_key} (row={row_idx})"
                    )

                for file_index, file_path in enumerate(source_files, start=1):
                    self.processor.log(
                        f"Merging source [{file_index}/{len(source_files)}]: {os.path.basename(file_path)}"
                    )
                    self._merge_source_file(
                        file_path=file_path,
                        max_col=max_col,
                        content_col_indexes=content_col_indexes,
                        merged_rows=merged_rows,
                    )

                updated_cells = 0
                added_rows = 0
                overwritten_cells = 0
                filled_blank_cells = 0

                for identity_key, merged_values in merged_rows.items():
                    row_indexes = master_rows_by_key.get(identity_key)
                    if not row_indexes:
                        worksheet.append(list(merged_values))
                        added_rows += 1
                        continue

                    for row_idx in row_indexes:
                        for col_idx in content_col_indexes:
                            cell = worksheet.cell(row=row_idx, column=col_idx + 1)
                            old_value = cell.value
                            new_value = merged_values[col_idx]
                            if values_equivalent(old_value, new_value):
                                continue
                            cell.value = new_value
                            updated_cells += 1
                            if is_blank_value(old_value) and (not is_blank_value(new_value)):
                                filled_blank_cells += 1
                            elif (not is_blank_value(old_value)) and (not is_blank_value(new_value)):
                                overwritten_cells += 1

                if updated_cells > 0 or added_rows > 0:
                    workbook.save(self.processor.master_file_path)
        except Exception as exc:
            self.processor.stats.files_failed += 1
            self.processor._log_error(
                "E_MASTER_MERGE",
                "Failed to merge into master file",
                file_path=self.processor.master_file_path,
                exc=exc,
            )
            raise

        return self.finalize_result(
            source_files=source_files,
            merged_keys=len(merged_rows),
            updated_cells=updated_cells,
            added_rows=added_rows,
            overwritten_cells=overwritten_cells,
            filled_blank_cells=filled_blank_cells,
            skipped_new_keys=0,
        )

    def _merge_source_file(
        self,
        *,
        file_path: str,
        max_col: int,
        content_col_indexes: Sequence[int],
        merged_rows: dict[str, list[Any]],
    ):
        try:
            with open_workbook(file_path, read_only=True) as workbook:
                worksheet = workbook.active
                for row_values in worksheet.iter_rows(
                    min_row=2,
                    min_col=1,
                    max_col=max_col,
                    values_only=True,
                ):
                    identity_key = self.identity_key_from_row(row_values)
                    if not identity_key:
                        continue

                    self.processor.stats.rows_scanned += 1
                    if identity_key not in merged_rows:
                        base_row = [None] * max_col
                        base_row[self.key_col] = safe_to_str(
                            row_values[self.key_col] if self.key_col < len(row_values) else None,
                            strip=True,
                        )
                        base_row[self.match_col] = safe_to_str(
                            row_values[self.match_col] if self.match_col < len(row_values) else None,
                            strip=True,
                        )
                        merged_rows[identity_key] = base_row

                    merge_non_blank_cells_fill_blank(
                        merged_rows[identity_key],
                        row_values,
                        content_col_indexes,
                    )
            self.processor.stats.files_succeeded += 1
        except Exception as exc:
            self.processor.stats.files_failed += 1
            self.processor._log_error(
                "E_SOURCE_READ",
                "Failed to read update source file",
                file_path=file_path,
                exc=exc,
            )
