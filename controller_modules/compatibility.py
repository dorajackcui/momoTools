from ui import strings
from .base import BaseController


class CompatibilityController(BaseController):
    def __init__(self, frame, processor, dialog_service=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
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
        if not self._ensure_required_values([(self.target_folder, strings.REQUIRE_TARGET_FOLDER)]):
            return

        self._run_action_or_notify(
            self.processor.process_files,
            on_success=lambda processed_files: self.dialogs.info(
                strings.SUCCESS_TITLE,
                f"共处理 {processed_files} 个文件。",
            ),
            task_name="Compatibility",
        )
