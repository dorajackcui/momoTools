from core.master_merge_processor import (
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_COMBINED,
    ROW_KEY_POLICY_KEY_ONLY,
)
from ui import strings
from .base import BaseController


class BaseMasterUpdateController(BaseController):
    cell_write_policy = ""
    key_admission_policy = KEY_ADMISSION_POLICY_ALLOW_NEW
    priority_winner_policy = PRIORITY_WINNER_POLICY_LAST_PROCESSED
    task_name = "Master Update"
    summary_title = "Updated"
    row_key_policy_override: str | None = None

    def __init__(self, frame, processor, dialog_service=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.processor = processor
        self.master_file_path = ""
        self.update_folder = ""
        self.update_file_paths: list[str] = []

    def select_master_file(self):
        file_path = self._ask_excel_file("Select master file")
        if not file_path:
            return

        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self._notify_master_file_probe(file_path)
        self.processor.set_master_file(file_path)
        if self.update_folder:
            self.refresh_update_files()

    def select_update_folder(self):
        folder_path = self._ask_folder("Select update folder")
        if not folder_path:
            return
        probe_result = self._confirm_excel_folder_selection(
            folder_path=folder_path,
            list_files=self.processor.list_update_files,
            dialog_title="Confirm update files",
            allow_empty_folder=True,
        )
        if probe_result is None:
            return

        self.update_folder = folder_path
        self._require_frame().set_update_folder_label(folder_path)
        self.processor.set_update_folder(folder_path)
        self.refresh_update_files()

    def refresh_update_files(self):
        if not self.update_folder:
            return

        self.update_file_paths = self.processor.list_update_files()
        self.processor.set_priority_files(self.update_file_paths)
        self._require_frame().set_priority_files(self.update_file_paths)

    def process_files(self):
        if not self._ensure_required_values(
            [
                (
                    self.master_file_path and self.update_folder,
                    strings.REQUIRE_MASTER_TARGET,
                )
            ]
        ):
            return
        if not self._ensure_master_file_ready(self.master_file_path):
            return

        config = self._get_config_or_notify()
        if config is None:
            return

        if not config.priority_files:
            self.dialogs.error(strings.ERROR_TITLE, "Please select at least one update file.")
            return

        row_key_policy = self.row_key_policy_override
        if row_key_policy is None:
            row_key_policy = ROW_KEY_POLICY_COMBINED if config.use_combined_key else ROW_KEY_POLICY_KEY_ONLY

        def run():
            self.processor.set_columns(config.key_col, config.match_col, config.last_update_col)
            self.processor.set_priority_files(config.priority_files)
            self.processor.set_row_key_policy(row_key_policy)
            self.processor.set_policies(
                cell_write_policy=self.cell_write_policy,
                key_admission_policy=self.key_admission_policy,
                priority_winner_policy=self.priority_winner_policy,
            )
            return self.processor.process_files()

        def on_success(result):
            summary_lines = [
                f"{self.summary_title} {result.source_files} update file(s).",
                f"Updated cells: {result.updated_cells}",
                f"Added rows: {result.added_rows}",
                f"Merged keys: {result.merged_keys}",
                f"Overwritten cells: {result.overwritten_cells}",
                f"Filled blank cells: {result.filled_blank_cells}",
                f"Skipped new keys: {result.skipped_new_keys}",
            ]
            if getattr(result, "unmatched_report_path", ""):
                summary_lines.append(f"Unmatched entries: {result.unmatched_entries}")
                summary_lines.append(f"Unmatched report: {result.unmatched_report_path}")
            self.dialogs.info(
                strings.SUCCESS_TITLE,
                "\n".join(summary_lines),
            )

        self._run_action_or_notify(
            run,
            on_success=on_success,
            task_name=self.task_name,
        )
