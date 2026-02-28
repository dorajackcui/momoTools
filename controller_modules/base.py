from tkinter import filedialog
from typing import Callable, Iterable, Optional, Tuple

from ui import strings
from ui.dialog_service import DialogService
from ui.validators import ValidationError
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
