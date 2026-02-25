import tkinter as tk

from ui import strings, theme
from ui.validators import parse_positive_int
from ui.view_models import ClearerConfig
from ui.views.base import BaseFrame


class ClearerFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.folder_label = self.create_picker_with_status(
            button_text="选择目标文件夹",
            command=self.controller.select_clearer_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
        )

        column_frame = tk.Frame(self, bg=theme.APP_BG)
        column_frame.pack(pady=10)
        tk.Label(column_frame, text="列号：", **self.label_style).pack(side=tk.LEFT)
        self.column_var = tk.StringVar(value="")
        tk.Entry(column_frame, textvariable=self.column_var, width=5).pack(side=tk.LEFT)
        tk.Label(column_frame, text="列", **self.label_style).pack(side=tk.LEFT)

        tk.Button(self, text="清空列", command=self.controller.clear_column, **self.button_style).pack(pady=5)
        tk.Button(self, text="插入列", command=self.controller.insert_column, **self.button_style).pack(pady=5)
        tk.Button(self, text="删除列", command=self.controller.delete_column, **self.button_style).pack(pady=5)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def get_config(self):
        return ClearerConfig(column_number=parse_positive_int(self.column_var.get(), "列号"))

