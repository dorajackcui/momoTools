import os

from ui import strings
from .base import BaseController


class UntranslatedStatsController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.target_folder = ""
        self.output_file = ""

    @staticmethod
    def _build_auto_output_file(target_folder):
        normalized_folder = os.path.normpath(target_folder)
        parent_folder = os.path.dirname(normalized_folder) or normalized_folder
        base_name = "未翻译统计"
        extension = ".xlsx"

        output_path = os.path.join(parent_folder, f"{base_name}{extension}")
        if not os.path.exists(output_path):
            return output_path

        index = 1
        while True:
            candidate = os.path.join(parent_folder, f"{base_name} ({index}){extension}")
            if not os.path.exists(candidate):
                return candidate
            index += 1

    def _set_output_file(self, path):
        self.output_file = path
        self._require_frame().set_output_file_label(path)

    def select_target_folder(self):
        folder_path = self._ask_folder("选择小表文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_target_folder(folder_path)
        auto_output_path = self._build_auto_output_file(folder_path)
        self._set_output_file(auto_output_path)

    def select_output_file(self):
        file_path = self._ask_output_excel_file("选择输出文件")
        if not file_path:
            return
        self._set_output_file(file_path)

    def process_stats(self):
        if not self._ensure_required_values([(self.target_folder, strings.REQUIRE_STATS_FOLDER)]):
            return

        if not self.output_file:
            self._set_output_file(self._build_auto_output_file(self.target_folder))

        config = self._get_config_or_notify()
        if config is None:
            return
        self.processor.set_columns(config.source_col, config.translation_col)
        self.processor.set_stats_mode(config.stats_mode)

        def run():
            stats_results = self.processor.process_files()
            if not stats_results:
                self.dialogs.warning(strings.WARNING_TITLE, "未找到任何Excel文件或所有文件都没有未翻译内容")
                return

            self.processor.export_to_excel(self.output_file)
            self.dialogs.info(
                strings.SUCCESS_TITLE,
                f"统计完成：\n共处理 {len(stats_results)} 个文件\n结果已保存到: {self.output_file}",
            )

        self._run_action_or_notify(
            run,
            error_title=strings.ERROR_TITLE,
        )
