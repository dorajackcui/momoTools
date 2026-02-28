from tkinter import filedialog
from typing import Callable, Iterable, Optional, Tuple

from ui import strings
from ui.dialog_service import DialogService
from ui.validators import ValidationError


class BaseController:
    def __init__(self, frame, dialog_service=None):
        self.frame = frame
        self.dialogs = dialog_service or DialogService()

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
    ):
        try:
            result = action()
            if on_success is not None:
                on_success(result)
            return result
        except Exception as exc:
            self.dialogs.error(error_title, str(exc))
            return None
