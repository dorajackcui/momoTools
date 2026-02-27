from ui import strings
from ui.validators import ValidationError
from .base import BaseController

class MultiColumnController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.master_file_path = ""
        self.target_folder = ""

    def select_multi_master_file(self):
        file_path = self._ask_excel_file("选择 Master 总表")
        if not file_path:
            return
        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self.processor.set_master_file(file_path)

    def select_multi_target_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_target_folder(folder_path)

    def process_multi_column(self):
        if not self.master_file_path or not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_MASTER_TARGET)
            return

        try:
            config = self._require_frame().get_config()
            self.processor.set_target_key_column(config.target_key_col)
            self.processor.set_match_column(config.target_match_col)
            self.processor.set_update_start_column(config.target_update_start_col)
            self.processor.set_master_key_column(config.master_key_col)
            self.processor.set_master_match_column(config.master_match_col)
            self.processor.set_start_column(config.master_start_col)
            self.processor.set_column_count(config.column_count)
            self.processor.set_fill_blank_only(config.fill_blank_only)
            self.processor.set_post_process_enabled(config.post_process_enabled)
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{strings.VALIDATION_CONFIG_PREFIX}{exc}")
            return
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
            return

        try:
            updated_count = self.processor.process_files()
            self.dialogs.info(strings.SUCCESS_TITLE, f"共更新 {updated_count} 处数据。")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
