import os

import win32com.client

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files


class ExcelColumnClearer:
    def __init__(self):
        self.folder_path = ""
        self.column_number = 0
        self.excel = None
        self.log_callback = print
        self.io_contract = ModeIOContract(
            mode_name="column_cleaner",
            skip_header=True,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_folder_path(self, path):
        self.folder_path = path

    def set_column_number(self, number):
        self.column_number = number

    def _init_excel(self):
        if not self.excel:
            self.excel = win32com.client.Dispatch("Excel.Application")
            self.excel.Visible = False
            self.excel.DisplayAlerts = False

    def _quit_excel(self):
        if self.excel:
            self.excel.Quit()
            self.excel = None

    def _log_error(self, code, message, file_path="", exc=None):
        event = ErrorEvent(code=code, message=message, file_path=file_path, exception=exc)
        self.event_logger.error(self.stats, event)

    def _list_target_files(self):
        return iter_excel_files(
            self.folder_path,
            extensions=self.io_contract.extensions,
            case_sensitive=True,
        )

    def clear_column_in_files(self):
        processed_files = 0
        file_paths = self._list_target_files()
        total_files = len(file_paths)

        try:
            self._init_excel()

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                try:
                    processed_files += 1
                    print(f"正在处理: {file_name} ({processed_files}/{total_files})")

                    wb = self.excel.Workbooks.Open(file_path)
                    ws = wb.ActiveSheet

                    last_row = ws.UsedRange.Rows.Count
                    clear_range = ws.Range(
                        ws.Cells(2, self.column_number),
                        ws.Cells(last_row, self.column_number),
                    )
                    clear_range.ClearContents()

                    wb.Save()
                    wb.Close()
                except Exception as exc:
                    print(f"处理文件 {file_name} 时报错：{str(exc)}")
                    self._log_error("E_CLEAR_COLUMN", "清空列失败", file_path=file_path, exc=exc)
                    continue
        finally:
            self._quit_excel()

        return processed_files

    def insert_column_in_files(self):
        processed_files = 0
        file_paths = self._list_target_files()
        total_files = len(file_paths)

        try:
            self._init_excel()

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                try:
                    processed_files += 1
                    print(f"\r正在处理: {file_name} ({processed_files}/{total_files})", end="")

                    wb = self.excel.Workbooks.Open(file_path)
                    ws = wb.ActiveSheet

                    column_range = ws.Columns(self.column_number)
                    column_range.Insert()
                    ws.Cells(1, self.column_number).Value = "Translation"

                    wb.Save()
                    wb.Close()
                except Exception as exc:
                    print(f"处理文件 {file_name} 时报错：{str(exc)}")
                    self._log_error("E_INSERT_COLUMN", "插入列失败", file_path=file_path, exc=exc)
                    continue
        finally:
            self._quit_excel()

        return processed_files

    def delete_column_in_files(self):
        processed_files = 0
        file_paths = self._list_target_files()
        total_files = len(file_paths)

        try:
            self._init_excel()

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                try:
                    processed_files += 1
                    print(f"正在处理: {file_name} ({processed_files}/{total_files})")

                    wb = self.excel.Workbooks.Open(file_path)
                    ws = wb.ActiveSheet
                    ws.Columns(self.column_number).Delete()

                    wb.Save()
                    wb.Close()
                except Exception as exc:
                    print(f"处理文件 {file_name} 时报错：{str(exc)}")
                    self._log_error("E_DELETE_COLUMN", "删除列失败", file_path=file_path, exc=exc)
                    continue
        finally:
            self._quit_excel()

        return processed_files
