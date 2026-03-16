import os
from tkinter import filedialog
from typing import Callable, Iterable, Optional, Tuple

from ui import strings
from ui.dialog_service import DialogService
from ui.validators import ValidationError
from .path_preflight import (
    MASTER_FAILURE_MISSING,
    build_preview_items,
    probe_excel_folder,
    probe_master_file,
)
from .task_runner import InlineTaskRunner, TaskRunner


class BaseController:
    def __init__(self, frame, dialog_service=None, task_runner: Optional[TaskRunner] = None):
        self.frame = frame
        self.dialogs = dialog_service or DialogService()
        self.task_runner = task_runner or InlineTaskRunner()

    def _require_frame(self):
        if self.frame is None:
            raise RuntimeError("UI frame is not attached")
        return self.frame

    @staticmethod
    def _ask_excel_file(title):
        return filedialog.askopenfilename(
            title=title,
            filetypes=[("Excel 文件", "*.xlsx *.xls")],
        )

    @staticmethod
    def _ask_folder(title):
        return filedialog.askdirectory(title=title)

    @staticmethod
    def _ask_output_excel_file(title):
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
        )

    def _ensure_required_values(self, requirements: Iterable[Tuple[object, str]]) -> bool:
        for value, message in requirements:
            if value:
                continue
            self.dialogs.error(strings.ERROR_TITLE, message)
            return False
        return True

    @staticmethod
    def _build_folder_summary_lines(
        folder_path: str,
        *,
        file_count: int,
        sampled_file: str = "",
        sample_writable: bool | None = None,
    ) -> list[str]:
        summary_lines = [
            f"Folder: {folder_path}",
            f"Excel files: {file_count}",
        ]
        if sampled_file:
            summary_lines.append(f"Sampled file: {os.path.basename(sampled_file)}")
        if sample_writable is True:
            summary_lines.append("Writable check: OK")
        return summary_lines

    def _notify_master_file_probe(self, master_file_path: str):
        result = probe_master_file(master_file_path)
        if (
            (not result.ok)
            and result.warning_message
            and result.failure_reason != MASTER_FAILURE_MISSING
        ):
            self.dialogs.warning(strings.WARNING_TITLE, result.warning_message)
        return result

    def _ensure_master_file_ready(self, master_file_path: str) -> bool:
        result = probe_master_file(master_file_path)
        if result.ok or result.failure_reason == MASTER_FAILURE_MISSING:
            return True
        if result.warning_message:
            self.dialogs.warning(strings.WARNING_TITLE, result.warning_message)
        return False

    def _confirm_excel_folder_selection(
        self,
        *,
        folder_path: str,
        list_files: Callable[[str], list[str]],
        dialog_title: str,
        require_writable_sample: bool = False,
        sample_seed_key: str = "",
        allow_empty_folder: bool = False,
    ):
        file_paths = list_files(folder_path)
        probe_result = probe_excel_folder(
            file_paths,
            require_writable_sample=require_writable_sample,
            sample_seed_key=sample_seed_key,
        )
        if not probe_result.file_paths:
            if allow_empty_folder:
                return probe_result
            self.dialogs.error(
                strings.ERROR_TITLE,
                probe_result.warning_message or strings.EXCEL_FOLDER_EMPTY,
            )
            return None
        if require_writable_sample and probe_result.sample_writable is False:
            self.dialogs.warning(strings.WARNING_TITLE, probe_result.warning_message)
            return None

        preview_items = build_preview_items(probe_result.file_paths, folder_path)
        summary_lines = self._build_folder_summary_lines(
            folder_path,
            file_count=len(probe_result.file_paths),
            sampled_file=probe_result.sampled_file,
            sample_writable=probe_result.sample_writable,
        )
        confirmed = self.dialogs.confirm_file_list(
            self.frame,
            dialog_title,
            preview_items,
            summary_lines,
        )
        if not confirmed:
            return None
        return probe_result

    def _get_config_or_notify(self, validation_prefix: str = strings.VALIDATION_CONFIG_PREFIX):
        try:
            return self._require_frame().get_config()
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{validation_prefix}{exc}")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
        return None

    def _run_action_or_notify(
        self,
        action: Callable[[], object],
        *,
        on_success: Optional[Callable[[object], None]] = None,
        error_title: str = strings.ERROR_TITLE,
        task_name: str = "",
    ):
        has_result = {"value": False}
        result_holder = {"value": None}

        def success_callback(result):
            has_result["value"] = True
            result_holder["value"] = result
            if on_success is not None:
                on_success(result)

        def error_callback(exc: Exception):
            self.dialogs.error(error_title, str(exc))

        started = self.task_runner.run(
            task_name=task_name,
            action=action,
            on_success=success_callback,
            on_error=error_callback,
        )
        if not started:
            self.dialogs.warning(strings.WARNING_TITLE, strings.TASK_ALREADY_RUNNING)
            return None
        if has_result["value"]:
            return result_holder["value"]
        return None
