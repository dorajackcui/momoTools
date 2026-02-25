import os
import re

import pandas as pd

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files
from core.kernel.excel_io import open_workbook


class UntranslatedStatsProcessor:
    def __init__(self, log_callback=None):
        self.target_folder = ""
        self.source_text_col = 1
        self.translation_col = 2
        self.stats_mode = "chinese_chars"
        self.stats_results = []
        self.log_callback = log_callback
        self.io_contract = ModeIOContract(
            mode_name="untranslated_stats",
            skip_header=True,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log, self.io_contract.mode_name)

    def set_target_folder(self, folder_path):
        self.target_folder = folder_path

    def set_columns(self, source_col, translation_col):
        self.source_text_col = source_col
        self.translation_col = translation_col

    def set_stats_mode(self, mode):
        self.stats_mode = mode

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def _log_error(self, code, message, file_path="", exc=None, context=None):
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            exception=exc,
            context=context or {},
        )
        self.event_logger.error(self.stats, event)

    def count_characters(self, text):
        if not text or pd.isna(text):
            return 0

        text = str(text).strip()
        if not text:
            return 0

        if self.stats_mode == "chinese_chars":
            chinese_characters = re.findall(r"[\u4e00-\u9fa5]", text)
            return len(chinese_characters)
        if self.stats_mode == "english_words":
            english_words = re.findall(r"\b[a-zA-Z]+(?:[\'\-][a-zA-Z]+)*\b", text)
            return len(english_words)
        return 0

    def is_translation_empty(self, translation):
        if pd.isna(translation) or translation is None:
            return True
        translation_str = str(translation).strip()
        return translation_str == "" or translation_str.lower() == "nan"

    def process_single_file(self, file_path):
        try:
            with open_workbook(file_path, read_only=True, data_only=True) as workbook:
                worksheet = workbook.active

                untranslated_chars = 0
                untranslated_rows = 0
                total_chars = 0
                total_rows = 0

                for row_idx, row in enumerate(worksheet.rows, start=1):
                    try:
                        if row_idx == 1:
                            continue
                        if len(row) <= max(self.source_text_col, self.translation_col):
                            continue

                        source_cell = row[self.source_text_col]
                        translation_cell = row[self.translation_col]
                        source_text = source_cell.value if source_cell else None
                        translation_text = translation_cell.value if translation_cell else None

                        if not source_text or pd.isna(source_text) or str(source_text).strip() == "":
                            continue

                        total_rows += 1
                        total_chars += self.count_characters(source_text)

                        if self.is_translation_empty(translation_text):
                            char_count = self.count_characters(source_text)
                            untranslated_chars += char_count
                            untranslated_rows += 1
                    except Exception:
                        continue

            file_name = os.path.basename(file_path)
            return file_name, untranslated_chars, untranslated_rows, total_chars, total_rows
        except Exception as exc:
            self._log_error(
                "E_STATS_FILE",
                "处理统计文件失败",
                file_path=file_path,
                exc=exc,
            )
            return os.path.basename(file_path), 0, 0, 0, 0

    def collect_excel_files(self):
        if not self.target_folder or not os.path.exists(self.target_folder):
            raise ValueError("目标文件夹不存在或未设置！")

        return iter_excel_files(
            self.target_folder,
            extensions=self.io_contract.extensions,
            include_temp_files=False,
            case_sensitive=False,
        )

    def process_files(self):
        if not self.target_folder:
            raise ValueError("请先选择目标文件夹！")

        self.log("开始统计未翻译字数...")
        file_paths = self.collect_excel_files()
        self.log(f"找到 {len(file_paths)} 个Excel文件")

        if not file_paths:
            self.log("未找到任何Excel文件")
            return []

        self.stats_results = []
        total_untranslated_chars = 0
        total_untranslated_rows = 0

        for i, file_path in enumerate(file_paths, 1):
            self.log(f"正在处理文件 ({i}/{len(file_paths)}): {os.path.basename(file_path)}")
            file_name, untranslated_chars, untranslated_rows, total_chars, total_rows = self.process_single_file(file_path)
            self.stats_results.append(
                {
                    "file_name": file_name,
                    "untranslated_chars": untranslated_chars,
                    "untranslated_rows": untranslated_rows,
                    "total_chars": total_chars,
                    "total_rows": total_rows,
                }
            )
            total_untranslated_chars += untranslated_chars
            total_untranslated_rows += untranslated_rows

        self.log("统计完成！")
        if self.stats_mode == "chinese_chars":
            self.log(f"总计：{total_untranslated_chars} 个未翻译字符，{total_untranslated_rows} 行未翻译内容")
        elif self.stats_mode == "english_words":
            self.log(f"总计：{total_untranslated_chars} 个未翻译词，{total_untranslated_rows} 行未翻译内容")
        else:
            self.log(f"总计：{total_untranslated_chars} 个未翻译字符，{total_untranslated_rows} 行未翻译内容")

        return self.stats_results

    def export_to_excel(self, output_path):
        if not self.stats_results:
            raise ValueError("没有统计结果可导出，请先运行统计功能！")

        try:
            df = pd.DataFrame(self.stats_results)

            if self.stats_mode == "chinese_chars":
                df.columns = ["文件名", "未翻译字数", "未翻译行数", "总字数", "总行数"]
                untranslated_col_name = "未翻译字数"
                total_col_name = "总字数"
            elif self.stats_mode == "english_words":
                df.columns = ["文件名", "未翻译词数", "未翻译行数", "总词数", "总行数"]
                untranslated_col_name = "未翻译词数"
                total_col_name = "总词数"
            else:
                df.columns = ["文件名", "未翻译字数", "未翻译行数", "总字数", "总行数"]
                untranslated_col_name = "未翻译字数"
                total_col_name = "总字数"

            total_untranslated_chars = df[untranslated_col_name].sum()
            total_untranslated_rows = df["未翻译行数"].sum()
            total_chars = df[total_col_name].sum()
            total_rows = df["总行数"].sum()

            summary_row = pd.DataFrame(
                {
                    "文件名": ["总计"],
                    untranslated_col_name: [total_untranslated_chars],
                    "未翻译行数": [total_untranslated_rows],
                    total_col_name: [total_chars],
                    "总行数": [total_rows],
                }
            )

            df_with_summary = pd.concat([df, summary_row], ignore_index=True)

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df_with_summary.to_excel(writer, sheet_name="未翻译统计", index=False)

                worksheet = writer.sheets["未翻译统计"]
                worksheet.column_dimensions["A"].width = 30
                worksheet.column_dimensions["B"].width = 15
                worksheet.column_dimensions["C"].width = 15
                worksheet.column_dimensions["D"].width = 15
                worksheet.column_dimensions["E"].width = 15

                from openpyxl.styles import Font

                summary_row_idx = len(df) + 2
                for col in ["A", "B", "C", "D", "E"]:
                    worksheet[f"{col}{summary_row_idx}"].font = Font(bold=True)

            self.log(f"统计结果已导出到：{output_path}")
            return True
        except Exception as exc:
            self._log_error(
                "E_STATS_EXPORT",
                "导出统计Excel失败",
                file_path=output_path,
                exc=exc,
            )
            self.log(f"导出Excel文件失败：{str(exc)}")
            return False

    def get_summary(self):
        if not self.stats_results:
            return "暂无统计结果"

        total_files = len(self.stats_results)
        total_chars = sum(result["untranslated_chars"] for result in self.stats_results)
        total_rows = sum(result["untranslated_rows"] for result in self.stats_results)

        if self.stats_mode == "chinese_chars":
            return f"共处理 {total_files} 个文件，未翻译字数：{total_chars}，未翻译行数：{total_rows}"
        if self.stats_mode == "english_words":
            return f"共处理 {total_files} 个文件，未翻译词数：{total_chars}，未翻译行数：{total_rows}"
        return f"共处理 {total_files} 个文件，未翻译字数：{total_chars}，未翻译行数：{total_rows}"
