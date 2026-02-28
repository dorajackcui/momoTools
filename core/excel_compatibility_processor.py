from win32com.client import Dispatch

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files


class ExcelCompatibilityProcessor:
    def __init__(self, log_callback=None):
        self.folder_path = ""
        self.log_callback = log_callback or print
        self.io_contract = ModeIOContract(
            mode_name="compatibility_processor",
            skip_header=False,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def set_log_callback(self, callback):
        self.log_callback = callback or print
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def log(self, message):
        self.log_callback(message)

    def count_excel_files(self):
        return len(
            iter_excel_files(
                self.folder_path,
                extensions=self.io_contract.extensions,
                case_sensitive=True,
            )
        )

    def _log_error(self, code, message, file_path="", exc=None):
        event = ErrorEvent(code=code, message=message, file_path=file_path, exception=exc)
        self.event_logger.error(self.stats, event)

    def process_files(self):
        if not self.folder_path:
            raise ValueError("Please set a valid folder path first")

        file_paths = iter_excel_files(
            self.folder_path,
            extensions=self.io_contract.extensions,
            case_sensitive=True,
        )
        total_files = len(file_paths)
        processed_files = 0
        excel_app = None

        try:
            excel_app = Dispatch("Excel.Application")
            excel_app.Visible = False
            excel_app.DisplayAlerts = False

            for file_path in file_paths:
                file_name = file_path.split("\\")[-1]
                try:
                    wb = excel_app.Workbooks.Open(file_path)
                    if wb is not None:
                        wb.Save()
                        wb.Close()
                        wb = None
                        processed_files += 1
                        self.log(f"Progress: {processed_files}/{total_files} - Current file: {file_name}")
                except Exception as exc:
                    self.log(f"Failed to process file {file_name}: {exc}")
                    self._log_error("E_COMPAT_FILE", "Compatibility process failed", file_path=file_path, exc=exc)
                    if "wb" in locals():
                        try:
                            wb.Close(False)
                        except Exception:
                            pass
                    continue
        finally:
            if excel_app is not None:
                try:
                    excel_app.Quit()
                except Exception:
                    pass

        self.log(f"Completed: processed {processed_files}/{total_files} files")
        return processed_files
