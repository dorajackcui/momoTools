from ui import strings
from .base import BaseController


class ReverseUpdaterController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.master_file_path = ""
        self.target_folder = ""

    def select_master_file(self):
        file_path = self._ask_excel_file("选择 Master 总表")
        if not file_path:
            return
        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self.processor.set_master_file(file_path)

    def select_target_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_target_folder(folder_path)

    def process_files(self):
        if not self._ensure_required_values(
            [(self.master_file_path and self.target_folder, strings.REQUIRE_MASTER_TARGET)]
        ):
            return

        config = self._get_config_or_notify()
        if config is None:
            return

        def run():
            self.processor.set_target_columns(
                config.target_key_col,
                config.target_match_col,
                config.target_content_col,
            )
            self.processor.set_master_columns(
                config.master_key_col,
                config.master_match_col,
                config.master_update_col,
            )
            self.processor.set_fill_blank_only(config.fill_blank_only)
            return self.processor.process_files()

        self._run_action_or_notify(
            run,
            on_success=lambda updated_count: self.dialogs.info(
                strings.SUCCESS_TITLE,
                f"共更新 {updated_count} 行。",
            ),
            error_title="处理失败",
        )
