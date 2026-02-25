from tkinter import filedialog

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


class UpdaterController(BaseController):
    def __init__(self, frame, single_processor, multi_processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
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
        if not self.master_file_path or not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_MASTER_TARGET)
            return

        try:
            config = self._require_frame().get_config()
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{strings.VALIDATION_CONFIG_PREFIX}{exc}")
            return
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
            return

        try:
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
                self.single_processor.set_post_process_enabled(config.post_process_enabled)
                updated_count = self.single_processor.process_files()
            else:
                self.multi_processor.set_target_key_column(config.target_key_col)
                self.multi_processor.set_match_column(config.target_match_col)
                self.multi_processor.set_update_start_column(config.target_update_start_col)
                self.multi_processor.set_master_key_column(config.master_key_col)
                self.multi_processor.set_master_match_column(config.master_match_col)
                self.multi_processor.set_start_column(config.master_content_start_col)
                self.multi_processor.set_column_count(config.column_count)
                self.multi_processor.set_fill_blank_only(config.fill_blank_only)
                self.multi_processor.set_post_process_enabled(config.post_process_enabled)
                updated_count = self.multi_processor.process_files()

            self.dialogs.info(strings.SUCCESS_TITLE, f"共更新 {updated_count} 处数据。")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))


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


class CompatibilityController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.target_folder = ""

    def select_compatibility_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_folder_path(folder_path)

    def process_compatibility(self):
        if not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_TARGET_FOLDER)
            return

        try:
            processed_files = self.processor.process_files()
            self.dialogs.info(strings.SUCCESS_TITLE, f"共处理 {processed_files} 个文件。")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))


class DeepReplaceController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.source_folder = ""
        self.target_folder = ""

    def select_source_folder(self):
        folder_path = self._ask_folder("选择源文件夹")
        if not folder_path:
            return
        self.source_folder = folder_path
        self._require_frame().set_source_folder_label(folder_path)
        self.processor.set_source_folder(folder_path)

    def select_target_folder(self):
        folder_path = self._ask_folder("选择目标文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_target_folder(folder_path)

    def process_files(self):
        if not self.source_folder or not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_SOURCE_TARGET)
            return

        try:
            processed_files = self.processor.process_files()
            self.dialogs.info(strings.SUCCESS_TITLE, f"共处理 {processed_files} 个文件。")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))


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
        if not self.master_file_path or not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_MASTER_TARGET)
            return

        try:
            config = self._require_frame().get_config()
            self.processor.set_target_columns(config.target_key_col, config.target_match_col, config.target_content_col)
            self.processor.set_master_columns(config.master_key_col, config.master_match_col, config.master_update_col)
            self.processor.set_fill_blank_only(config.fill_blank_only)
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{strings.VALIDATION_CONFIG_PREFIX}{exc}")
            return
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
            return

        try:
            updated_count = self.processor.process_files()
            self.dialogs.info(strings.SUCCESS_TITLE, f"共更新 {updated_count} 行。")
        except Exception as exc:
            self.dialogs.error("处理失败", str(exc))


class UntranslatedStatsController(BaseController):
    def __init__(self, frame, processor, dialog_service=None):
        super().__init__(frame, dialog_service=dialog_service)
        self.processor = processor
        self.target_folder = ""
        self.output_file = ""

    def select_target_folder(self):
        folder_path = self._ask_folder("选择小表文件夹")
        if not folder_path:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.processor.set_target_folder(folder_path)

    def select_output_file(self):
        file_path = self._ask_output_excel_file("选择输出文件")
        if not file_path:
            return
        self.output_file = file_path
        self._require_frame().set_output_file_label(file_path)

    def process_stats(self):
        if not self.target_folder:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_STATS_FOLDER)
            return

        if not self.output_file:
            self.dialogs.error(strings.ERROR_TITLE, strings.REQUIRE_OUTPUT_FILE)
            return

        try:
            config = self._require_frame().get_config()
            self.processor.set_columns(config.source_col, config.translation_col)
            self.processor.set_stats_mode(config.stats_mode)
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"{strings.VALIDATION_CONFIG_PREFIX}{exc}")
            return
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
            return

        try:
            stats_results = self.processor.process_files()
            if not stats_results:
                self.dialogs.warning(strings.WARNING_TITLE, "未找到任何Excel文件或所有文件都没有未翻译内容")
                return

            self.processor.export_to_excel(self.output_file)
            self.dialogs.info(
                strings.SUCCESS_TITLE,
                f"统计完成！\n共处理 {len(stats_results)} 个文件\n结果已保存到: {self.output_file}",
            )
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"处理过程中发生错误：{exc}")
