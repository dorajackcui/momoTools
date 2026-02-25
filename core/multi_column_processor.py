import os
import time

import pandas as pd
from win32com.client import Dispatch

from core.kernel import (
    ErrorEvent,
    EventLogger,
    ModeIOContract,
    ProcessingStats,
    apply_cell_updates,
    build_combined_key,
    is_blank_value,
    iter_excel_files,
    run_parallel_sum,
    safe_to_str,
)
from core.kernel.excel_io import open_workbook


class MultiColumnExcelProcessor:
    def __init__(self, log_callback=None):
        self.master_file_path = ""
        self.target_folder = ""
        self.log_callback = log_callback or (lambda msg: None)

        self.target_key_column_index = 1
        self.match_column_index = 2
        self.update_start_column_index = 4

        self.master_key_column_index = 1
        self.master_match_column_index = 2
        self.start_column_index = 4

        self.column_count = 7
        self.debug_keys = [
            "LDLG_Text_ZH_q101102_1_d1_cd_Line_14",
            "clothesdes_10208",
        ]
        self.fill_blank_only = False
        self.post_process_enabled = True

        self.io_contract = ModeIOContract(
            mode_name="master_to_target_multi",
            skip_header=False,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_target_key_column(self, column_index):
        self.target_key_column_index = column_index

    def set_master_key_column(self, column_index):
        self.master_key_column_index = column_index

    def set_master_match_column(self, column_index):
        self.master_match_column_index = column_index

    def set_match_column(self, column_index):
        self.match_column_index = column_index

    def set_start_column(self, column_index):
        self.start_column_index = column_index

    def set_update_start_column(self, column_index):
        self.update_start_column_index = column_index

    def set_column_count(self, count):
        self.column_count = count

    def set_master_file(self, file_path):
        self.master_file_path = file_path

    def set_target_folder(self, folder_path):
        self.target_folder = folder_path

    def set_post_process_enabled(self, enabled: bool):
        self.post_process_enabled = bool(enabled)

    def set_fill_blank_only(self, enabled: bool):
        self.fill_blank_only = bool(enabled)

    def log(self, message):
        self.log_callback(message)

    def _log_error(self, code, message, file_path="", row=None, col=None, exc=None, context=None):
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            row=row,
            col=col,
            exception=exc,
            context=context or {},
        )
        self.event_logger.error(self.stats, event)

    def debug_key_info(self, master_dict, keys_to_check):
        for key in keys_to_check:
            found = False
            for combined_key, value in master_dict.items():
                if combined_key.startswith(f"{key}|"):
                    self.log(f"Debug - Key '{key}' 的组合键 '{combined_key}' 内容: {value}")
                    found = True
            if not found:
                self.log(f"Debug - 未找到Key: {key}")

    def _build_usecols(self):
        usecols = []
        key_col = max(0, self.master_key_column_index)
        usecols.append(key_col)

        match_col = max(0, self.master_match_column_index)
        if match_col not in usecols:
            usecols.append(match_col)

        for i in range(self.column_count):
            content_col = max(0, self.start_column_index + i)
            if content_col not in usecols:
                usecols.append(content_col)

        usecols.sort()
        return usecols

    def _read_master_dataframe(self, usecols):
        try:
            return pd.read_excel(
                self.master_file_path,
                engine="openpyxl",
                dtype={col: str for col in range(len(usecols))},
                keep_default_na=False,
                na_values=[],
                na_filter=False,
                usecols=usecols,
            )
        except Exception as excel_err:
            self.log(f"使用指定列读取失败，尝试读取全部列: {excel_err}")
            return pd.read_excel(
                self.master_file_path,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False,
                na_values=[],
                na_filter=False,
            )

    def _build_master_dict(self, master_df, usecols):
        col_mapping = {col_idx: i for i, col_idx in enumerate(usecols)}
        master_dict = {}

        for row in master_df.values:
            try:
                if len(row) == 0:
                    continue

                key_idx = col_mapping.get(self.master_key_column_index, 0)
                key_val = row[key_idx] if key_idx < len(row) else ""

                match_idx = col_mapping.get(self.master_match_column_index, 1)
                match_val = row[match_idx] if match_idx < len(row) else ""

                combined_key = build_combined_key(
                    key_val,
                    match_val,
                    separator=self.io_contract.key_separator,
                )
                if not combined_key:
                    continue

                content_values = []
                for i in range(self.column_count):
                    content_col_idx = self.start_column_index + i
                    mapped_idx = col_mapping.get(content_col_idx, -1)
                    if mapped_idx >= 0 and mapped_idx < len(row):
                        content_values.append(safe_to_str(row[mapped_idx], strip=False))
                    else:
                        content_values.append("")

                master_dict[combined_key] = content_values
            except Exception as row_err:
                self._log_error(
                    "E_MASTER_ROW",
                    "处理 Master 行失败，已跳过",
                    exc=row_err,
                )
                continue

        return master_dict

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            raise ValueError("请先选择 Master 文件和目标文件夹！")

        self.stats = ProcessingStats()
        start_time = time.time()

        try:
            self.log("正在读取 Master 文件...")
            master_start_time = time.time()
            usecols = self._build_usecols()
            self.log(f"将读取以下列: {usecols}")
            master_df = self._read_master_dataframe(usecols)
            self.log(f"Master文件读取耗时: {time.time() - master_start_time:.2f}秒")
            self.log(f"成功读取，共 {len(master_df)} 行数据")
        except Exception as exc:
            raise Exception(f"读取 Master 文件失败：{exc}")

        master_dict = self._build_master_dict(master_df, usecols)
        self.log(f"Master 中共找到 {len(master_dict)} 个有效Key")

        file_paths = iter_excel_files(self.target_folder, extensions=self.io_contract.extensions)
        self.stats.files_total = len(file_paths)
        self.log(f"找到 {len(file_paths)} 个目标文件")

        process_start_time = time.time()
        updated_count = run_parallel_sum(
            file_paths,
            lambda fp: self._process_single_file(fp, master_dict),
            max_workers_cap=32,
        )
        self.log(f"文件处理耗时: {time.time() - process_start_time:.2f}秒")
        self.log(f"处理完成，共更新 {updated_count} 处数据")

        if self.post_process_enabled:
            self.log("开始后处理步骤...")
            self._post_process(file_paths)
            self.log("后处理步骤完成")
        else:
            self.log("后处理已关闭，跳过")

        self.log(f"总耗时: {time.time() - start_time:.2f}秒")

        return updated_count

    def _process_single_file(self, file_path, master_dict):
        updates = {}
        updated = 0

        try:
            with open_workbook(file_path, read_only=True) as workbook:
                worksheet = workbook.active
                for idx, row in enumerate(worksheet.rows, start=1):
                    try:
                        key_cell = row[self.target_key_column_index] if len(row) > self.target_key_column_index else None
                        match_cell = row[self.match_column_index] if len(row) > self.match_column_index else None
                        if match_cell is None:
                            continue

                        combined_key = build_combined_key(
                            key_cell.value if key_cell else None,
                            match_cell.value if match_cell else None,
                            separator=self.io_contract.key_separator,
                        )
                        if not combined_key or combined_key not in master_dict:
                            continue

                        content_values = master_dict[combined_key]
                        for i, content_value in enumerate(content_values):
                            target_col_index = self.update_start_column_index + i
                            current_value = row[target_col_index].value if len(row) > target_col_index else None
                            if self.fill_blank_only and (not is_blank_value(current_value)):
                                continue
                            update_col = self.update_start_column_index + i + 1
                            updates[(idx, update_col)] = content_value
                            updated += 1
                    except Exception:
                        continue
        except Exception as exc:
            self.stats.files_failed += 1
            self._log_error(
                "E_TARGET_SCAN",
                "扫描目标文件失败",
                file_path=file_path,
                exc=exc,
            )
            return 0

        if updates and not apply_cell_updates(file_path, updates):
            self.stats.files_failed += 1
            self._log_error(
                "E_TARGET_SAVE",
                "写回目标文件失败",
                file_path=file_path,
            )
            return 0

        self.stats.files_succeeded += 1
        self.stats.cells_updated += updated
        return updated

    def _post_process(self, file_paths):
        if not file_paths:
            return

        try:
            post_process_start_time = time.time()
            total_files = len(file_paths)
            excel_app = Dispatch("Excel.Application")
            excel_app.Visible = False
            excel_app.DisplayAlerts = False

            try:
                for index, file_path in enumerate(file_paths, 1):
                    print(
                        f"\r正在后处理文件 ({index}/{total_files}): {os.path.basename(file_path)}",
                        end="",
                    )
                    self._process_single_file_post(file_path, excel_app)
            finally:
                if excel_app is not None:
                    try:
                        excel_app.Quit()
                    except Exception:
                        pass
                    excel_app = None

            self.log(f"后处理步骤耗时: {time.time() - post_process_start_time:.2f}秒")
        except Exception as exc:
            self._log_error("E_POST_PROCESS", "后处理步骤失败", exc=exc)

    def _process_single_file_post(self, file_path, excel_app):
        try:
            workbook = excel_app.Workbooks.Open(file_path)
            if workbook is not None:
                workbook.Save()
                workbook.Close(True)
                workbook = None
        except Exception as exc:
            self._log_error(
                "E_POST_PROCESS_FILE",
                "后处理文件失败",
                file_path=file_path,
                exc=exc,
            )
