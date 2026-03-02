from ui import strings
from .base import BaseController


class UpdaterController(BaseController):
    def __init__(self, frame, single_processor, multi_processor, dialog_service=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.single_processor = single_processor
        self.multi_processor = multi_processor
        self.master_file_path = ""
        self.target_folder = ""

    def select_master_file(self):
        file_path = self._ask_excel_file("选择 Master 总表")
        if not file_path:
            return
        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self._ensure_master_file_ready(file_path)
        self.single_processor.set_master_file(file_path)
        self.multi_processor.set_master_file(file_path)

    def select_target_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.single_processor.set_target_folder(folder_path)
        self.multi_processor.set_target_folder(folder_path)

    def process_files(self):
        if not self._ensure_required_values(
            [(self.master_file_path and self.target_folder, strings.REQUIRE_MASTER_TARGET)]
        ):
            return
        if not self._ensure_master_file_ready(self.master_file_path):
            return

        config = self._get_config_or_notify()
        if config is None:
            return

        def run():
            if config.column_count == 1:
                self.single_processor.set_target_column(
                    config.target_key_col,
                    config.target_match_col,
                    config.target_update_start_col,
                )
                self.single_processor.set_master_column(
                    config.master_key_col,
                    config.master_match_col,
                    config.master_content_start_col,
                )
                self.single_processor.set_fill_blank_only(config.fill_blank_only)
                self.single_processor.set_allow_blank_write(config.allow_blank_write)
                self.single_processor.set_post_process_enabled(config.post_process_enabled)
                return self.single_processor.process_files()

            self.multi_processor.set_target_key_column(config.target_key_col)
            self.multi_processor.set_match_column(config.target_match_col)
            self.multi_processor.set_update_start_column(config.target_update_start_col)
            self.multi_processor.set_master_key_column(config.master_key_col)
            self.multi_processor.set_master_match_column(config.master_match_col)
            self.multi_processor.set_start_column(config.master_content_start_col)
            self.multi_processor.set_column_count(config.column_count)
            self.multi_processor.set_fill_blank_only(config.fill_blank_only)
            self.multi_processor.set_allow_blank_write(config.allow_blank_write)
            self.multi_processor.set_post_process_enabled(config.post_process_enabled)
            return self.multi_processor.process_files()

        self._run_action_or_notify(
            run,
            on_success=lambda updated_count: self.dialogs.info(
                strings.SUCCESS_TITLE,
                f"共更新 {updated_count} 处数据。",
            ),
            task_name="Master->Target",
        )

