from typing import Any, Sequence
from time import perf_counter

from core.kernel import is_blank_value, open_workbook
from core.master_update.executors.base import BaseMasterUpdateExecutor
from core.master_update.io_helpers import UNSET, values_equivalent
from core.master_update.policies import (
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    ROW_KEY_POLICY_COMBINED,
    ROW_KEY_POLICY_KEY_ONLY,
)
from core.master_update.source_collectors import (
    build_identity_key_from_values,
    collect_source_candidates,
    collect_source_rows_dense,
)
from core.master_update.reporting import (
    UnmatchedIdentityInfo,
    build_unmatched_report_path,
    build_unmatched_report_rows,
    export_unmatched_report,
)


class UpdateMasterExecutor(BaseMasterUpdateExecutor):
    required_row_key_policy = ROW_KEY_POLICY_KEY_ONLY

    def run(self, source_files: Sequence[str]):
        self.processor.row_key_policy = self.required_row_key_policy
        # Historical policy name `overwrite_non_blank` maps to dense-row overwrite here.
        return self._run_with_collector(
            source_files=source_files,
            mode_name="Update Master",
            collector_mode="dense",
        )

    def _run_sparse_overwrite(self, source_files: Sequence[str], *, mode_name: str):
        # Update Content uses sparse non-blank cell semantics.
        return self._run_with_collector(
            source_files=source_files,
            mode_name=mode_name,
            collector_mode="sparse",
        )

    def _run_with_collector(
        self,
        *,
        source_files: Sequence[str],
        mode_name: str,
        collector_mode: str,
    ):
        total_start = perf_counter()

        layout = self.resolve_layout()
        max_col = layout.max_col
        content_col_indexes = layout.content_col_indexes

        collect_start = perf_counter()
        candidate_rows: dict[str, list[Any]]
        touched_cols_by_key: dict[str, set[int]] | None
        unmatched_info_by_identity: dict[str, UnmatchedIdentityInfo] = {}
        if collector_mode == "dense":
            source_rows = collect_source_rows_dense(
                source_files=source_files,
                key_col=self.key_col,
                match_col=self.match_col,
                row_key_policy=self.processor.row_key_policy,
                max_col=max_col,
                content_col_indexes=content_col_indexes,
                key_separator=self.processor.io_contract.key_separator,
                on_log=self.processor.log,
                on_log_error=self.processor._log_error,
                stats=self.processor.stats,
            )
            candidate_rows = source_rows.rows
            touched_cols_by_key = None
        elif collector_mode == "sparse":
            source_candidates = collect_source_candidates(
                source_files=source_files,
                key_col=self.key_col,
                match_col=self.match_col,
                row_key_policy=self.processor.row_key_policy,
                max_col=max_col,
                content_col_indexes=content_col_indexes,
                cell_write_policy=self.processor.cell_write_policy,
                priority_winner_policy=self.processor.priority_winner_policy,
                key_separator=self.processor.io_contract.key_separator,
                on_log=self.processor.log,
                on_log_error=self.processor._log_error,
                stats=self.processor.stats,
            )
            candidate_rows = source_candidates.rows
            touched_cols_by_key = source_candidates.touched_cols_by_key
            unmatched_info_by_identity = source_candidates.unmatched_info_by_key
        else:
            raise ValueError(f"Unsupported collector_mode: {collector_mode}")

        collect_sources_elapsed = perf_counter() - collect_start
        candidate_key_set = set(candidate_rows.keys())

        updated_cells = 0
        added_rows = 0
        overwritten_cells = 0
        filled_blank_cells = 0
        skipped_new_keys = 0
        master_keys: set[str] = set()
        pending_cell_updates: dict[tuple[int, int], object] = {}

        scan_master_elapsed = 0.0
        plan_updates_elapsed = 0.0
        if candidate_rows:
            scan_master_start = perf_counter()
            max_touched_col_num = 0
            if touched_cols_by_key is not None:
                max_touched_col_num = max(
                    (max(cols) + 1 for cols in touched_cols_by_key.values() if cols),
                    default=0,
                )
            try:
                with open_workbook(
                    self.processor.master_file_path,
                    read_only=True,
                    keep_links=False,
                ) as workbook:
                    worksheet = workbook.active

                    key_col_num = self.key_col + 1
                    match_col_num = self.match_col + 1
                    if self.processor.row_key_policy == ROW_KEY_POLICY_COMBINED:
                        scan_key_max_col = max(key_col_num, match_col_num)
                    else:
                        scan_key_max_col = key_col_num
                    if touched_cols_by_key is None:
                        scan_max_col = max(scan_key_max_col, max_col, 1)
                    else:
                        scan_max_col = max(scan_key_max_col, max_touched_col_num, 1)

                    for row_idx, row_values in enumerate(
                        worksheet.iter_rows(
                            min_row=2,
                            min_col=1,
                            max_col=scan_max_col,
                            values_only=True,
                        ),
                        start=2,
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
                        merged_values = candidate_rows.get(identity_key)
                        if merged_values is None:
                            continue

                        plan_start = perf_counter()
                        if touched_cols_by_key is None:
                            for col_idx in content_col_indexes:
                                new_value = (
                                    merged_values[col_idx] if col_idx < len(merged_values) else None
                                )
                                old_value = row_values[col_idx] if col_idx < len(row_values) else None
                                if values_equivalent(old_value, new_value):
                                    continue
                                pending_cell_updates[(row_idx, col_idx + 1)] = new_value
                                updated_cells += 1
                                if is_blank_value(old_value) and (not is_blank_value(new_value)):
                                    filled_blank_cells += 1
                                elif (not is_blank_value(old_value)) and (not is_blank_value(new_value)):
                                    overwritten_cells += 1
                        else:
                            touched_cols = touched_cols_by_key.get(identity_key)
                            if touched_cols:
                                for col_idx in touched_cols:
                                    new_value = merged_values[col_idx]
                                    if new_value is UNSET:
                                        continue
                                    old_value = row_values[col_idx] if col_idx < len(row_values) else None
                                    if values_equivalent(old_value, new_value):
                                        continue
                                    pending_cell_updates[(row_idx, col_idx + 1)] = new_value
                                    updated_cells += 1
                                    if is_blank_value(old_value) and (not is_blank_value(new_value)):
                                        filled_blank_cells += 1
                                    elif (not is_blank_value(old_value)) and (not is_blank_value(new_value)):
                                        overwritten_cells += 1
                        plan_updates_elapsed += perf_counter() - plan_start
            except Exception as exc:
                self.processor.stats.files_failed += 1
                self.processor._log_error(
                    "E_MASTER_MERGE",
                    "Failed to scan master file for update planning",
                    file_path=self.processor.master_file_path,
                    exc=exc,
                )
                raise
            scan_master_elapsed = perf_counter() - scan_master_start

        new_rows_to_append: list[list[object | None]] = []
        unmatched_entries = 0
        unmatched_report_path = ""
        if self.processor.key_admission_policy == KEY_ADMISSION_POLICY_ALLOW_NEW:
            for identity_key, merged_values in candidate_rows.items():
                if identity_key in master_keys:
                    continue
                if touched_cols_by_key is None:
                    row_to_append = list(merged_values)
                else:
                    row_to_append = [None if value is UNSET else value for value in merged_values]
                new_rows_to_append.append(row_to_append)
                master_keys.add(identity_key)
            added_rows = len(new_rows_to_append)
        if self.processor.key_admission_policy == KEY_ADMISSION_POLICY_EXISTING_ONLY:
            unmatched_identity_keys = candidate_key_set - master_keys
            skipped_new_keys = len(unmatched_identity_keys)
            unmatched_entries = skipped_new_keys
            unmatched_report_rows = build_unmatched_report_rows(
                {
                    identity_key: unmatched_info_by_identity[identity_key]
                    for identity_key in unmatched_identity_keys
                    if identity_key in unmatched_info_by_identity
                }
            )
            unmatched_report_path = build_unmatched_report_path(self.processor.update_folder)
            try:
                export_unmatched_report(
                    unmatched_report_path,
                    unmatched_report_rows,
                    content_col_indexes=content_col_indexes,
                )
                self.processor.log(f"Translation unmatched report written: {unmatched_report_path}")
            except Exception as exc:
                self.processor.stats.files_failed += 1
                self.processor._log_error(
                    "E_MASTER_REPORT",
                    "Failed to export translation unmatched report",
                    file_path=unmatched_report_path,
                    exc=exc,
                )
                raise

        open_apply_elapsed = 0.0
        save_elapsed = 0.0
        if pending_cell_updates or new_rows_to_append:
            write_start = perf_counter()
            try:
                with open_workbook(self.processor.master_file_path, read_only=False) as workbook:
                    worksheet = workbook.active

                    for (row_idx, col_idx), new_value in pending_cell_updates.items():
                        worksheet.cell(row=row_idx, column=col_idx).value = new_value
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
                    "Failed to apply planned updates to master file",
                    file_path=self.processor.master_file_path,
                    exc=exc,
                )
                raise

        total_elapsed = perf_counter() - total_start
        self.processor.log(
            (
                f"Perf({mode_name}): "
                f"layout_probe_used={'yes' if layout.probe_used else 'no'}, "
                f"layout_probe={layout.probe_elapsed:.2f}s, "
                f"collect_sources={collect_sources_elapsed:.2f}s, "
                f"scan_master_ro={scan_master_elapsed:.2f}s, "
                f"plan_updates={plan_updates_elapsed:.2f}s, "
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
            unmatched_entries=unmatched_entries,
            unmatched_report_path=unmatched_report_path,
        )
