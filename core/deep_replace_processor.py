import os
import shutil

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files


class DeepReplaceProcessor:
    def __init__(self, log_callback=None):
        self.source_folder = ""
        self.target_folder = ""
        self.log_callback = log_callback or (lambda msg: None)
        self.processed_files = 0
        self.io_contract = ModeIOContract(
            mode_name="deep_replace",
            skip_header=False,
        )
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)

    def set_source_folder(self, folder_path):
        self.source_folder = folder_path

    def set_target_folder(self, folder_path):
        self.target_folder = folder_path

    def list_target_files(self, folder_path=None):
        folder = self.target_folder if folder_path is None else folder_path
        return iter_excel_files(
            folder,
            extensions=self.io_contract.extensions,
            include_temp_files=False,
            case_sensitive=True,
        )

    def log(self, message):
        self.log_callback(message)

    def _log_error(self, code, message, file_path="", exc=None, context=None):
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            exception=exc,
            context=context or {},
        )
        self.event_logger.error(self.stats, event)

    def find_file_in_directory(self, filename, search_path):
        for root, _, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def process_files(self):
        if not self.source_folder or not self.target_folder:
            raise ValueError("请先选择源文件夹和目标文件夹！")

        if not os.path.exists(self.source_folder) or not os.path.exists(self.target_folder):
            raise ValueError("源文件夹或目标文件夹不存在！")

        self.processed_files = 0
        self.stats = ProcessingStats()
        source_file_paths = iter_excel_files(
            self.source_folder,
            extensions=self.io_contract.extensions,
            include_temp_files=False,
            case_sensitive=True,
        )
        source_files = [(os.path.basename(path), path) for path in source_file_paths]

        for source_file, source_path in source_files:
            self.log(f"正在处理文件：{source_file}")
            target_file_path = self.find_file_in_directory(source_file, self.target_folder)

            if target_file_path:
                backup_path = target_file_path + ".bak"
                try:
                    shutil.copy2(target_file_path, backup_path)
                    shutil.copy2(source_path, target_file_path)
                    self.processed_files += 1
                    self.log(f"成功替换文件：{target_file_path}")
                    os.remove(backup_path)
                except Exception as exc:
                    self.log(f"替换文件 {source_file} 时发生错误：{str(exc)}")
                    self._log_error(
                        "E_REPLACE_FILE",
                        "替换文件失败",
                        file_path=target_file_path,
                        exc=exc,
                        context={"source_path": source_path},
                    )
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, target_file_path)
                        os.remove(backup_path)
            else:
                self.log(f"未找到匹配的目标文件：{source_file}")

        return self.processed_files
