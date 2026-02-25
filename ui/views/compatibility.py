import tkinter as tk

from ui import strings
from ui.views.base import BaseFrame


class CompatibilityFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.folder_label = self.create_picker_with_status(
            button_text="选择目标文件夹",
            command=self.controller.select_compatibility_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
        )
        tk.Button(
            self,
            text="开始处理",
            command=self.controller.process_compatibility,
            **self.button_style,
        ).pack(pady=10)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

