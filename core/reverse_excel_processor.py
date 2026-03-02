import os
import time

from core.kernel import (
    ErrorEvent,
    EventLogger,
    ModeIOContract,
    ProcessingStats,
    build_combined_key,
    get_stable_workers_cap,
    is_blank_value,
    iter_excel_files,
    run_parallel_map,
    safe_to_str,
)
from core.kernel.excel_io import open_workbook


class ReverseExcelProcessor:
    def __init__(self, log_callback=None):
        self.master_file_path = ""
        self.target_folder = ""
        self.log_callback = log_callback or (lambda msg: None)

        self.target_key_col = 0
        self.target_match_col = 1
        self.target_content_col = 2

        self.master_key_col = 1
        self.master_match_col = 2
        self.master_update_col = 3
        self.fill_blank_only = False

        self.io_contract = ModeIOContract(
            mode_name="target_to_master_reverse",
            skip_header=True,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_target_columns(self, key_col, match_col, content_col):
        self.target_key_col = key_col
        self.target_match_col = match_col
        self.target_content_col = content_col

    def set_master_columns(self, key_col, match_col, update_col):
        self.master_key_col = key_col
        self.master_match_col = match_col
        self.master_update_col = update_col

    def set_master_file(self, file_path):
        self.master_file_path = file_path

    def set_target_folder(self, folder_path):
        self.target_folder = folder_path

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

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            raise ValueError("请先选择 Master 文件和目标文件夹！")

        self.stats = ProcessingStats()
        start_time = time.time()
        self.log("开始处理文件...")

        self.log("正在从目标文件夹中的小文件读取数据...")
        target_data_dict = self._read_target_files()
        self.log(f"从小文件中读取了 {len(target_data_dict)} 条数据。")

        self.log("正在更新 Master 文件...")
        updated_count = self._update_master_file(target_data_dict)
        self.log(f"Master 文件更新完成，共更新 {updated_count} 处数据。")

        self.log(f"总耗时: {time.time() - start_time:.2f}秒")
        return updated_count

    def _read_target_files(self):
        file_paths = sorted(
            iter_excel_files(self.target_folder, extensions=self.io_contract.extensions),
            key=lambda path: path.lower(),
        )
        self.stats.files_total = len(file_paths)
        self.log(f"找到 {len(file_paths)} 个目标文件")

        workers_cap = get_stable_workers_cap()
        results = run_parallel_map(
            file_paths,
            self._read_single_target_file,
            max_workers_cap=workers_cap,
        )
        data_dict = {}
        for local_dict in results:
            data_dict.update(local_dict)

        return data_dict

    def _read_single_target_file(self, file_path):
        local_dict = {}
        required_cols = {
            self.target_key_col,
            self.target_match_col,
            self.target_content_col,
        }
        min_col_idx = min(required_cols)
        max_col_idx = max(required_cols)
        min_col = min_col_idx + 1
        max_col = max_col_idx + 1
        key_offset = self.target_key_col - min_col_idx
        match_offset = self.target_match_col - min_col_idx
        content_offset = self.target_content_col - min_col_idx
        try:
            with open_workbook(file_path, read_only=True) as workbook:
                worksheet = workbook.active
                for row_values in worksheet.iter_rows(
                    min_row=2,
                    min_col=min_col,
                    max_col=max_col,
                    values_only=True,
                ):
                    try:
                        combined_key = build_combined_key(
                            row_values[key_offset] if key_offset < len(row_values) else None,
                            row_values[match_offset] if match_offset < len(row_values) else None,
                            separator=self.io_contract.key_separator,
                        )
                        if not combined_key:
                            continue

                        content_val = safe_to_str(
                            row_values[content_offset] if content_offset < len(row_values) else None,
                            strip=False,
                        )
                        local_dict[combined_key] = content_val
                    except IndexError:
                        continue
        except Exception as exc:
            self._log_error(
                "E_TARGET_READ",
                "读取小表文件失败",
                file_path=file_path,
                exc=exc,
                context={"file_name": os.path.basename(file_path)},
            )
            return {}

        self.stats.files_succeeded += 1
        return local_dict

    def _update_master_file(self, target_data_dict):
        if not target_data_dict:
            self.log("没有从目标文件中读取到任何数据，无需更新。")
            return 0

        updated_count = 0
        required_cols = {
            self.master_key_col,
            self.master_match_col,
            self.master_update_col,
        }
        min_col_idx = min(required_cols)
        max_col_idx = max(required_cols)
        min_col = min_col_idx + 1
        max_col = max_col_idx + 1
        key_offset = self.master_key_col - min_col_idx
        match_offset = self.master_match_col - min_col_idx
        update_offset = self.master_update_col - min_col_idx
        try:
            with open_workbook(self.master_file_path, read_only=False) as workbook:
                worksheet = workbook.active
                for row in worksheet.iter_rows(min_col=min_col, max_col=max_col):
                    master_key_cell = row[key_offset] if key_offset < len(row) else None
                    master_match_cell = row[match_offset] if match_offset < len(row) else None
                    combined_key = build_combined_key(
                        master_key_cell.value if master_key_cell else None,
                        master_match_cell.value if master_match_cell else None,
                        separator=self.io_contract.key_separator,
                    )
                    if not combined_key:
                        continue

                    if combined_key in target_data_dict:
                        update_cell = row[update_offset] if update_offset < len(row) else None
                        if update_cell is None:
                            continue
                        if self.fill_blank_only and (not is_blank_value(update_cell.value)):
                            continue
                        update_cell.value = target_data_dict[combined_key]
                        updated_count += 1

                if updated_count > 0:
                    workbook.save(self.master_file_path)
        except Exception as exc:
            self._log_error(
                "E_MASTER_UPDATE",
                "更新 Master 文件失败",
                file_path=self.master_file_path,
                exc=exc,
            )
            return 0

        return updated_count
