from ui import strings
from ui.validators import ValidationError
from .base import BaseController

class ClearerController(BaseController):
    def __init__(self, frame, clearer, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.clearer = clearer
        self.target_folder = ""

    def select_clearer_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.clearer.set_folder_path(folder_path)

    def _with_column_config(self, action, success_template, confirm_message=None):
        if not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_TARGET_FOLDER)
            return

        try:
            config = self._require_frame().get_config()
            self.clearer.set_column_number(config.column_number)
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{strings.VALIDATION_COLUMN_PREFIX}{exc}")
            return
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
            return

        if confirm_message:
            if not self.dialogs.confirm(strings.CONFIRM_TITLE, confirm_message.format(column_number=config.column_number)):
                return

        try:
            processed_files = action()
            self.dialogs.info(strings.SUCCESS_TITLE, success_template.format(processed_files=processed_files))
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))

    def clear_column(self):
        self._with_column_config(
            action=self.clearer.clear_column_in_files,
            success_template="共处理 {processed_files} 个文件。",
        )

    def insert_column(self):
        self._with_column_config(
            action=self.clearer.insert_column_in_files,
            success_template="共处理 {processed_files} 个文件。",
        )

    def delete_column(self):
        self._with_column_config(
            action=self.clearer.delete_column_in_files,
            success_template="共处理 {processed_files} 个文件。",
            confirm_message="确定要删除所有Excel文件的第{column_number}列吗？\n此操作不可撤销！",
        )
