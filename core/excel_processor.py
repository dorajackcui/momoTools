import time
from threading import Lock

import pandas as pd

from core.kernel import (
    ErrorEvent,
    EventLogger,
    ModeIOContract,
    ProcessingStats,
    apply_cell_updates,
    build_combined_key,
    get_stable_workers_cap,
    is_blank_value,
    iter_excel_files,
    open_workbook,
    safe_to_str,
)
from core.pipeline import process_files_in_parallel, run_excel_com_post_process


class ExcelProcessor:
    def __init__(self, log_callback=None):
        self.master_file_path = ""
        self.target_folder = ""
        self.log_callback = log_callback or (lambda msg: None)
        self.master_columns = []

        self.target_key_col = 0
        self.target_match_col = 1
        self.target_update_col = 2

        self.master_key_col = 1
        self.master_match_col = 2
        self.master_content_col = 3

        self.debug_keys = [
            "AD159EAE417F98EE46FCF697E15D4FFD",
            "clothesdes_10208",
        ]
        self.fill_blank_only = False
        self.post_process_enabled = True

        self.io_contract = ModeIOContract(
            mode_name="master_to_target_single",
            skip_header=False,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_target_column(self, target_key, target_match, target_update):
        self.target_key_col = target_key
        self.target_match_col = target_match
        self.target_update_col = target_update

    def set_master_column(self, master_key, master_match, master_content):
        self.master_key_col = master_key
        self.master_match_col = master_match
        self.master_content_col = master_content

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

    def _read_master_dict(self):
        self.log("正在读取 Master 文件...")
        master_start_time = time.time()
        usecols = [self.master_key_col, self.master_match_col, self.master_content_col]
        try:
            master_df = pd.read_excel(
                self.master_file_path,
                engine="openpyxl",
                dtype={col: str for col in range(len(usecols))},
                keep_default_na=False,
                na_values=[""],
                na_filter=False,
                usecols=usecols,
            )
        except Exception as exc:
            raise Exception(f"读取 Master 文件失败：{exc}")

        master_dict = {}
        for row in master_df.values:
            key_text = safe_to_str(row[0], strip=True)
            if not key_text:
                continue
            combined_key = build_combined_key(key_text, row[1], separator=self.io_contract.key_separator)
            if not combined_key:
                continue
            master_dict[combined_key] = safe_to_str(row[2], strip=False)

        self.log(f"Master文件读取耗时: {time.time() - master_start_time:.2f}秒")
        self.log(f"Master 中共找到 {len(master_dict)} 个有效Key")
        return master_dict

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            raise ValueError("请先选择 Master 文件和目标文件夹！")

        self.stats = ProcessingStats()
        start_time = time.time()
        master_dict = self._read_master_dict()

        file_paths = iter_excel_files(self.target_folder, extensions=self.io_contract.extensions)
        self.stats.files_total = len(file_paths)
        self.log(f"找到 {len(file_paths)} 个目标文件")

        process_start_time = time.time()
        workers_cap = get_stable_workers_cap()
        updated_files = set()
        updated_files_lock = Lock()

        def worker(file_path):
            updated_cells = self._process_single_file(file_path, master_dict)
            if updated_cells > 0:
                with updated_files_lock:
                    updated_files.add(file_path)
            return updated_cells

        updated_count = process_files_in_parallel(
            file_paths,
            worker,
            max_workers_cap=workers_cap,
        )
        updated_file_paths = [file_path for file_path in file_paths if file_path in updated_files]
        self.log(f"文件处理耗时: {time.time() - process_start_time:.2f}秒")
        self.log(f"处理完成，共更新 {updated_count} 处数据")

        if self.post_process_enabled:
            self.log("开始后处理步骤...")
            self.log(f"Post-process files: {len(updated_file_paths)}")
            if updated_file_paths:
                self._post_process(updated_file_paths)
            else:
                self.log("No updated files, skip post-process.")
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
                required_cols = {self.target_key_col, self.target_match_col}
                if self.fill_blank_only:
                    required_cols.add(self.target_update_col)

                min_col_idx = min(required_cols)
                max_col_idx = max(required_cols)
                min_col = min_col_idx + 1
                max_col = max_col_idx + 1
                key_offset = self.target_key_col - min_col_idx
                match_offset = self.target_match_col - min_col_idx
                update_offset = self.target_update_col - min_col_idx

                for idx, row_values in enumerate(
                    worksheet.iter_rows(min_col=min_col, max_col=max_col, values_only=True),
                    start=1,
                ):
                    try:
                        combined_key = build_combined_key(
                            row_values[key_offset] if key_offset < len(row_values) else None,
                            row_values[match_offset] if match_offset < len(row_values) else None,
                            separator=self.io_contract.key_separator,
                        )
                        if not combined_key:
                            continue

                        if combined_key in master_dict:
                            current_value = (
                                row_values[update_offset]
                                if self.fill_blank_only and update_offset < len(row_values)
                                else None
                            )
                            if self.fill_blank_only and (not is_blank_value(current_value)):
                                continue
                            update_col = self.target_update_col + 1
                            updates[(idx, update_col)] = master_dict[combined_key]
                            updated += 1
                    except Exception as row_exc:
                        self._log_error(
                            "E_TARGET_ROW",
                            "目标文件行处理失败，已跳过",
                            file_path=file_path,
                            row=idx,
                            exc=row_exc,
                        )
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

        run_excel_com_post_process(
            file_paths=file_paths,
            per_file_runner=self._process_single_file_post,
            log_callback=self.log,
            fail_callback=lambda exc: self._log_error(
                "E_POST_PROCESS",
                "后处理步骤失败",
                exc=exc,
            ),
        )

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

