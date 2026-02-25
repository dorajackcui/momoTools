import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import parse_positive_int
from ui.view_models import ClearerConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_action_button


class ClearerFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("输入文件夹")
        self.folder_label = self.create_picker_with_status(
            button_text="选择目标文件夹",
            command=self.controller.select_clearer_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        column_frame = self.create_section_card("列配置")
        row = ttk.Frame(column_frame, style="Surface.TFrame")
        row.pack(anchor="w", pady=(0, theme.SPACING_XXS))
        ttk.Label(row, text="列号：", style="Surface.TLabel").pack(side=tk.LEFT)
        self.column_var = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.column_var, width=5).pack(side=tk.LEFT, padx=(theme.SPACING_XXS, 0))
        ttk.Label(row, text="列", style="Surface.TLabel").pack(side=tk.LEFT, padx=(theme.SPACING_XXS, 0))

        actions = self.create_section_card("操作")
        create_action_button(
            actions,
            text="清空列",
            command=self.controller.clear_column,
            button_style="Secondary.TButton",
            pady=(0, theme.SPACING_XS),
        )
        create_action_button(
            actions,
            text="插入列",
            command=self.controller.insert_column,
            button_style="Secondary.TButton",
            pady=(0, theme.SPACING_XS),
        )
        create_action_button(
            actions,
            text="删除列",
            command=self.controller.delete_column,
            button_style="Danger.TButton",
            pady=0,
        )

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def get_config(self):
        return ClearerConfig(column_number=parse_positive_int(self.column_var.get(), "列号"))
