from typing import Sequence, Type

from core.kernel import open_workbook
from core.master_update.models import MasterMergeResult
from core.master_update.policies import (
    CELL_WRITE_POLICY_FILL_BLANK_ONLY,
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_KEY_ONLY,
)


class BaseMasterUpdateExecutor:
    def __init__(self, processor):
        self.processor = processor

    @property
    def key_col(self) -> int:
        return self.processor.key_col

    @property
    def match_col(self) -> int:
        return self.processor.match_col

    def run(self, source_files: Sequence[str]) -> MasterMergeResult:
        raise NotImplementedError

    def list_update_files(self) -> list[str]:
        return self.processor._list_update_files_internal()

    def resolve_source_files(self) -> list[str]:
        if not self.processor.master_file_path:
            raise ValueError("Please select a master file first.")
        if not self.processor.update_folder:
            raise ValueError("Please select an update folder first.")

        source_files = (
            list(self.processor.update_file_paths)
            if self.processor.update_file_paths
            else self.list_update_files()
        )
        if not source_files:
            raise ValueError("No update files found in the selected folder.")

        source_files = [path for path in source_files if self.processor._is_file(path)]
        if not source_files:
            raise ValueError("No readable update files found.")
        return source_files

    def resolve_layout(self) -> tuple[int, list[int]]:
        key_col_num = self.key_col + 1
        match_col_num = self.match_col + 1
        try:
            with open_workbook(self.processor.master_file_path, read_only=True) as probe_workbook:
                probe_sheet = probe_workbook.active
                required_col_num = max(key_col_num, match_col_num)
                max_col = max(probe_sheet.max_column, required_col_num)

                if self.processor.last_update_col is not None:
                    configured_last_update_col_num = self.processor.last_update_col + 1
                    if configured_last_update_col_num < required_col_num:
                        raise ValueError(
                            "Last update col must be greater than or equal to Key col and Match col."
                        )
                    max_col = min(max_col, configured_last_update_col_num)
        except Exception as exc:
            self.processor.stats.files_failed += 1
            self.processor._log_error(
                "E_MASTER_PROBE",
                "Failed to inspect master file columns",
                file_path=self.processor.master_file_path,
                exc=exc,
            )
            raise

        include_match_as_content = self.processor.row_key_policy == ROW_KEY_POLICY_KEY_ONLY
        content_col_indexes = [
            index
            for index in range(max_col)
            if index != self.key_col and (include_match_as_content or index != self.match_col)
        ]
        return max_col, content_col_indexes

    def finalize_result(
        self,
        *,
        source_files: Sequence[str],
        merged_keys: int,
        updated_cells: int,
        added_rows: int,
        overwritten_cells: int,
        filled_blank_cells: int,
        skipped_new_keys: int,
        unmatched_entries: int = 0,
        unmatched_report_path: str = "",
    ) -> MasterMergeResult:
        self.processor.stats.files_succeeded += 1
        self.processor.stats.cells_updated = updated_cells
        return MasterMergeResult(
            updated_cells=updated_cells,
            added_rows=added_rows,
            merged_keys=merged_keys,
            source_files=len(source_files),
            overwritten_cells=overwritten_cells,
            filled_blank_cells=filled_blank_cells,
            skipped_new_keys=skipped_new_keys,
            unmatched_entries=unmatched_entries,
            unmatched_report_path=unmatched_report_path,
        )


def resolve_executor_cls(
    *,
    cell_write_policy: str,
    key_admission_policy: str,
    priority_winner_policy: str,
    merge_executor: Type[BaseMasterUpdateExecutor],
    update_master_executor: Type[BaseMasterUpdateExecutor],
    update_content_executor: Type[BaseMasterUpdateExecutor],
) -> Type[BaseMasterUpdateExecutor]:
    policy_tuple = (
        cell_write_policy,
        key_admission_policy,
        priority_winner_policy,
    )
    if policy_tuple == (
        CELL_WRITE_POLICY_FILL_BLANK_ONLY,
        KEY_ADMISSION_POLICY_ALLOW_NEW,
        PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ):
        return merge_executor
    if policy_tuple == (
        CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
        KEY_ADMISSION_POLICY_ALLOW_NEW,
        PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ):
        return update_master_executor
    if policy_tuple == (
        CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
        KEY_ADMISSION_POLICY_EXISTING_ONLY,
        PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ):
        return update_content_executor
    raise ValueError(
        "Unsupported master update policy combination: "
        f"cell={cell_write_policy}, key={key_admission_policy}, priority={priority_winner_policy}"
    )
