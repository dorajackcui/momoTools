import os
import time
from typing import Sequence

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files
from core.master_update import (
    CELL_WRITE_POLICY_FILL_BLANK_ONLY,
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_COMBINED,
    ROW_KEY_POLICY_KEY_ONLY,
    MasterMergeResult,
    validate_cell_write_policy,
    validate_key_admission_policy,
    validate_priority_winner_policy,
    validate_row_key_policy,
)
from core.master_update.executors import (
    MergeMastersExecutor,
    UpdateContentExecutor,
    UpdateMasterExecutor,
    resolve_executor_cls,
)


class MasterMergeProcessor:
    def __init__(self, log_callback=None):
        self.master_file_path = ""
        self.update_folder = ""
        self.update_file_paths: list[str] = []
        self.log_callback = log_callback or (lambda msg: None)

        self.key_col = 1
        self.match_col = 2
        self.last_update_col: int | None = None

        self.cell_write_policy = CELL_WRITE_POLICY_FILL_BLANK_ONLY
        self.key_admission_policy = KEY_ADMISSION_POLICY_ALLOW_NEW
        self.priority_winner_policy = PRIORITY_WINNER_POLICY_LAST_PROCESSED
        self.row_key_policy = ROW_KEY_POLICY_COMBINED

        self.io_contract = ModeIOContract(
            mode_name="master_merge",
            skip_header=True,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_master_file(self, file_path: str):
        self.master_file_path = str(file_path or "")

    def set_update_folder(self, folder_path: str):
        self.update_folder = str(folder_path or "")

    def set_columns(self, key_col: int, match_col: int, last_update_col: int | None = None):
        self.key_col = int(key_col)
        self.match_col = int(match_col)
        self.last_update_col = None if last_update_col is None else int(last_update_col)

    def set_priority_files(self, file_paths: Sequence[str]):
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_path in file_paths:
            path = str(raw_path or "").strip()
            if not path:
                continue
            key = os.path.normcase(os.path.abspath(path))
            if key in seen:
                continue
            seen.add(key)
            normalized.append(path)
        self.update_file_paths = normalized

    def set_policies(
        self,
        *,
        cell_write_policy: str | None = None,
        key_admission_policy: str | None = None,
        priority_winner_policy: str | None = None,
    ):
        if cell_write_policy is not None:
            self.cell_write_policy = validate_cell_write_policy(cell_write_policy)

        if key_admission_policy is not None:
            self.key_admission_policy = validate_key_admission_policy(key_admission_policy)

        if priority_winner_policy is not None:
            self.priority_winner_policy = validate_priority_winner_policy(priority_winner_policy)

    def set_row_key_policy(self, row_key_policy: str):
        self.row_key_policy = validate_row_key_policy(row_key_policy)

    def list_update_files(self) -> list[str]:
        return self._list_update_files_internal()

    def _list_update_files_internal(self) -> list[str]:
        folder = str(self.update_folder or "").strip()
        if not folder or not os.path.isdir(folder):
            return []

        files = iter_excel_files(
            folder,
            extensions=self.io_contract.extensions,
            include_temp_files=False,
        )
        files.sort(key=lambda path: os.path.basename(path).lower())

        master_abs = os.path.normcase(os.path.abspath(self.master_file_path)) if self.master_file_path else ""
        return [
            path
            for path in files
            if self._is_file(path)
            and (not master_abs or os.path.normcase(os.path.abspath(path)) != master_abs)
        ]

    @staticmethod
    def _is_file(path: str) -> bool:
        return os.path.isfile(path)

    def log(self, message: str):
        self.log_callback(message)

    def _log_error(self, code, message, file_path="", row=None, col=None, exc=None, context=None):
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            row=row,
            col=col,
            exception=exc,
            context=context or {},
        )
        self.event_logger.error(self.stats, event)

    def _resolve_executor_cls(self):
        return resolve_executor_cls(
            cell_write_policy=self.cell_write_policy,
            key_admission_policy=self.key_admission_policy,
            priority_winner_policy=self.priority_winner_policy,
            merge_executor=MergeMastersExecutor,
            update_master_executor=UpdateMasterExecutor,
            update_content_executor=UpdateContentExecutor,
        )

    def process_files(self) -> MasterMergeResult:
        executor_cls = self._resolve_executor_cls()
        executor = executor_cls(self)
        source_files = executor.resolve_source_files()

        start_time = time.time()
        self.stats = ProcessingStats()
        self.stats.files_total = len(source_files) + 1

        self.log("Reading master and merging update files...")
        result = executor.run(source_files)
        self.log(
            (
                f"Merge finished. updated_cells={result.updated_cells}, "
                f"added_rows={result.added_rows}, merged_keys={result.merged_keys}"
            )
        )
        self.log(f"Elapsed: {time.time() - start_time:.2f}s")
        return result
