import os
from time import perf_counter
from typing import Any, Sequence

from core.kernel import is_blank_value, open_workbook, safe_to_str
from core.master_update.executors.base import BaseMasterUpdateExecutor
from core.master_update.io_helpers import normalize_content_row_values
from core.master_update.policies import ROW_KEY_POLICY_COMBINED
from core.master_update.source_collectors import (
    build_identity_key_from_values,
)


class MergeMastersExecutor(BaseMasterUpdateExecutor):
    def _has_required_match_value(self, row_values: Sequence[Any]) -> bool:
        if self.processor.row_key_policy == ROW_KEY_POLICY_COMBINED:
            return True
        match_value = row_values[self.match_col] if self.match_col < len(row_values) else None
        return not is_blank_value(match_value)

    def run(self, source_files: Sequence[str]):
        total_start = perf_counter()
        layout = self.resolve_layout()
        max_col = layout.max_col
        content_col_indexes = layout.content_col_indexes

        collect_start = perf_counter()
        candidate_rows = self._collect_append_candidates(
            source_files=source_files,
            max_col=max_col,
            content_col_indexes=content_col_indexes,
        )
        collect_sources_elapsed = perf_counter() - collect_start

        updated_cells = 0
        overwritten_cells = 0
        filled_blank_cells = 0
        skipped_new_keys = 0
        added_rows = 0
        master_keys: set[str] = set()

        scan_master_start = perf_counter()
        key_col_num = self.key_col + 1
        match_col_num = self.match_col + 1
        if self.processor.row_key_policy == ROW_KEY_POLICY_COMBINED:
            scan_max_col = max(key_col_num, match_col_num)
        else:
            scan_max_col = key_col_num
        try:
            with open_workbook(
                self.processor.master_file_path,
                read_only=True,
                keep_links=False,
            ) as workbook:
                worksheet = workbook.active
                for row_values in worksheet.iter_rows(
                    min_row=2,
                    min_col=1,
                    max_col=scan_max_col,
                    values_only=True,
                ):
                    identity_key = build_identity_key_from_values(
                        row_values=row_values,
                        key_col=self.key_col,
                        match_col=self.match_col,
                        row_key_policy=self.processor.row_key_policy,
                        key_separator=self.processor.io_contract.key_separator,
                    )
                    if not identity_key:
                        continue
                    self.processor.stats.rows_scanned += 1
                    master_keys.add(identity_key)
        except Exception as exc:
            self.processor.stats.files_failed += 1
            self.processor._log_error(
                "E_MASTER_MERGE",
                "Failed to scan master file for existing keys",
                file_path=self.processor.master_file_path,
                exc=exc,
            )
            raise
        scan_master_elapsed = perf_counter() - scan_master_start

        new_rows_to_append: list[list[object | None]] = []
        for identity_key, merged_values in candidate_rows.items():
            if identity_key in master_keys:
                continue
            new_rows_to_append.append(list(merged_values))
            master_keys.add(identity_key)
        added_rows = len(new_rows_to_append)

        open_apply_elapsed = 0.0
        save_elapsed = 0.0
        if new_rows_to_append:
            write_start = perf_counter()
            try:
                with open_workbook(self.processor.master_file_path, read_only=False) as workbook:
                    worksheet = workbook.active
                    for row_values in new_rows_to_append:
                        worksheet.append(row_values)

                    open_apply_elapsed = perf_counter() - write_start
                    save_start = perf_counter()
                    workbook.save(self.processor.master_file_path)
                    save_elapsed = perf_counter() - save_start
            except Exception as exc:
                self.processor.stats.files_failed += 1
                self.processor._log_error(
                    "E_MASTER_MERGE",
                    "Failed to append new rows to master file",
                    file_path=self.processor.master_file_path,
                    exc=exc,
                )
                raise

        total_elapsed = perf_counter() - total_start
        self.processor.log(
            (
                "Perf(Merge Masters): "
                f"layout_probe_used={'yes' if layout.probe_used else 'no'}, "
                f"layout_probe={layout.probe_elapsed:.2f}s, "
                f"collect_sources={collect_sources_elapsed:.2f}s, "
                f"scan_master_ro={scan_master_elapsed:.2f}s, "
                f"open_master_rw_apply={open_apply_elapsed:.2f}s, "
                f"save_master={save_elapsed:.2f}s, "
                f"total={total_elapsed:.2f}s"
            )
        )

        return self.finalize_result(
            source_files=source_files,
            merged_keys=len(master_keys),
            updated_cells=updated_cells,
            added_rows=added_rows,
            overwritten_cells=overwritten_cells,
            filled_blank_cells=filled_blank_cells,
            skipped_new_keys=skipped_new_keys,
        )

    def _collect_append_candidates(
        self,
        *,
        source_files: Sequence[str],
        max_col: int,
        content_col_indexes: Sequence[int],
    ) -> dict[str, list[Any]]:
        candidate_rows: dict[str, list[Any]] = {}
        content_col_set = set(content_col_indexes)
        for file_index, file_path in enumerate(source_files, start=1):
            self.processor.log(
                f"Merging source [{file_index}/{len(source_files)}]: {os.path.basename(file_path)}"
            )
            try:
                with open_workbook(file_path, read_only=True, keep_links=False) as workbook:
                    worksheet = workbook.active
                    for row_values in worksheet.iter_rows(
                        min_row=2,
                        min_col=1,
                        max_col=max_col,
                        values_only=True,
                    ):
                        if not self._has_required_match_value(row_values):
                            continue
                        identity_key = build_identity_key_from_values(
                            row_values=row_values,
                            key_col=self.key_col,
                            match_col=self.match_col,
                            row_key_policy=self.processor.row_key_policy,
                            key_separator=self.processor.io_contract.key_separator,
                        )
                        if not identity_key:
                            continue

                        self.processor.stats.rows_scanned += 1
                        if identity_key in candidate_rows:
                            # Merge Masters append-only mode assumes update rows are complete.
                            # Keep the first-seen full row for duplicate identities.
                            continue

                        row_buffer = normalize_content_row_values(
                            row_values=row_values,
                            max_col=max_col,
                            content_col_indexes=content_col_indexes,
                        )
                        row_buffer[self.key_col] = safe_to_str(
                            row_values[self.key_col] if self.key_col < len(row_values) else None,
                            strip=True,
                        )
                        if self.match_col not in content_col_set:
                            row_buffer[self.match_col] = safe_to_str(
                                row_values[self.match_col] if self.match_col < len(row_values) else None,
                                strip=True,
                            )
                        candidate_rows[identity_key] = row_buffer
                self.processor.stats.files_succeeded += 1
            except Exception as exc:
                self.processor.stats.files_failed += 1
                self.processor._log_error(
                    "E_SOURCE_READ",
                    "Failed to read update source file",
                    file_path=file_path,
                    exc=exc,
                )

        return candidate_rows
