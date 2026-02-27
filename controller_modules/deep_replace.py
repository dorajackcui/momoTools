from ui import strings
from .base import BaseController

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
