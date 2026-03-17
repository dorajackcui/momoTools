from dataclasses import dataclass

from core.master_merge_processor import (
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_COMBINED,
    ROW_KEY_POLICY_KEY_ONLY,
)
from ui import strings
from .base import BaseController


@dataclass(frozen=True)
class SourceTranslationPipelineResult:
    source_result: object
    translation_result: object


class SourceTranslationPipelineController(BaseController):
    task_name = "Source+Translation"

    def __init__(self, frame, processor, dialog_service=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.processor = processor
        self.master_file_path = ""
        self.source_update_folder = ""
        self.translation_update_folder = ""
        self.source_update_file_paths: list[str] = []
        self.translation_update_file_paths: list[str] = []

    def select_master_file(self):
        file_path = self._ask_excel_file("Select master file")
        if not file_path:
            return

        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self._notify_master_file_probe(file_path)
        self.processor.set_master_file(file_path)
        self.refresh_source_update_files()
        self.refresh_translation_update_files()

    def select_source_update_folder(self):
        self._select_update_folder(
            title="Select Source Text update folder",
            dialog_title="Confirm Source Text update files",
            set_folder=self._set_source_update_folder,
        )

    def select_translation_update_folder(self):
        self._select_update_folder(
            title="Select Translation update folder",
            dialog_title="Confirm Translation update files",
            set_folder=self._set_translation_update_folder,
        )

    def _select_update_folder(self, *, title: str, dialog_title: str, set_folder):
        folder_path = self._ask_folder(title)
        if not folder_path:
            return
        probe_result = self._confirm_excel_folder_selection(
            folder_path=folder_path,
            list_files=self.processor.list_update_files,
            dialog_title=dialog_title,
            allow_empty_folder=True,
        )
        if probe_result is None:
            return
        set_folder(folder_path, probe_result.file_paths)

    def _set_source_update_folder(self, folder_path: str, file_paths: list[str]):
        self.source_update_folder = folder_path
        self.source_update_file_paths = list(file_paths)
        frame = self._require_frame()
        frame.set_source_update_folder_label(folder_path)
        frame.set_source_priority_files(self.source_update_file_paths)

    def _set_translation_update_folder(self, folder_path: str, file_paths: list[str]):
        self.translation_update_folder = folder_path
        self.translation_update_file_paths = list(file_paths)
        frame = self._require_frame()
        frame.set_translation_update_folder_label(folder_path)
        frame.set_translation_priority_files(self.translation_update_file_paths)

    def refresh_source_update_files(self):
        if not self.source_update_folder:
            return
        self.source_update_file_paths = self.processor.list_update_files(self.source_update_folder)
        self._require_frame().set_source_priority_files(self.source_update_file_paths)

    def refresh_translation_update_files(self):
        if not self.translation_update_folder:
            return
        self.translation_update_file_paths = self.processor.list_update_files(self.translation_update_folder)
        self._require_frame().set_translation_priority_files(self.translation_update_file_paths)

    def process_files(self):
        if not self._ensure_required_values(
            [
                (
                    self.master_file_path and self.source_update_folder and self.translation_update_folder,
                    "Please select a master file and both update folders.",
                )
            ]
        ):
            return
        if not self._ensure_master_file_ready(self.master_file_path):
            return

        config = self._get_config_or_notify()
        if config is None:
            return

        def run():
            self.processor.set_master_file(self.master_file_path)
            self.processor.set_columns(config.key_col, config.match_col, config.last_update_col)

            self.processor.log("=== Source Text stage ===")
            source_result = self._run_stage(
                update_folder=self.source_update_folder,
                priority_files=config.source_priority_files,
                row_key_policy=ROW_KEY_POLICY_KEY_ONLY,
                key_admission_policy=KEY_ADMISSION_POLICY_ALLOW_NEW,
            )

            self.processor.log("=== Translation stage ===")
            translation_result = self._run_stage(
                update_folder=self.translation_update_folder,
                priority_files=config.translation_priority_files,
                row_key_policy=ROW_KEY_POLICY_COMBINED,
                key_admission_policy=KEY_ADMISSION_POLICY_EXISTING_ONLY,
            )
            return SourceTranslationPipelineResult(
                source_result=source_result,
                translation_result=translation_result,
            )

        def on_success(result: SourceTranslationPipelineResult):
            summary_lines = self._build_stage_summary("Source Text", result.source_result)
            summary_lines.append("")
            summary_lines.extend(self._build_stage_summary("Translation", result.translation_result))
            self.dialogs.info(strings.SUCCESS_TITLE, "\n".join(summary_lines))

        self._run_action_or_notify(
            run,
            on_success=on_success,
            task_name=self.task_name,
        )

    def _run_stage(
        self,
        *,
        update_folder: str,
        priority_files: tuple[str, ...],
        row_key_policy: str,
        key_admission_policy: str,
    ):
        self.processor.set_update_folder(update_folder)
        self.processor.set_priority_files(priority_files)
        self.processor.set_row_key_policy(row_key_policy)
        self.processor.set_policies(
            cell_write_policy=CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
            key_admission_policy=key_admission_policy,
            priority_winner_policy=PRIORITY_WINNER_POLICY_LAST_PROCESSED,
        )
        return self.processor.process_files()

    @staticmethod
    def _build_stage_summary(stage_name: str, result) -> list[str]:
        summary_lines = [
            f"{stage_name}:",
            f"Updated {result.source_files} update file(s).",
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
        return summary_lines
