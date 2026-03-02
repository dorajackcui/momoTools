import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import parse_column_1_based_to_0_based, parse_positive_int
from ui.view_models import MultiColumnConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_labeled_entry


class MultiColumnFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("输入文件")
        self.master_label = self.create_picker_with_status(
            button_text="选择 Master 总表",
            command=self.controller.select_multi_master_file,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )
        self.folder_label = self.create_picker_with_status(
            button_text="选择目标文件夹",
            command=self.controller.select_multi_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=theme.SPACING_SM,
        )

        target_frame = self.create_section_card("目标文件列配置")
        self.target_key_col_var = tk.StringVar(value="2")
        self.match_column_var = tk.StringVar(value="3")
        self.update_start_column_var = tk.StringVar(value="5")
        create_labeled_entry(
            target_frame,
            row=0,
            column=0,
            label_text="Key 列:",
            variable=self.target_key_col_var,
            label_padx=(0, 0),
        )
        create_labeled_entry(
            target_frame,
            row=0,
            column=2,
            label_text="原文列:",
            variable=self.match_column_var,
        )
        create_labeled_entry(
            target_frame,
            row=0,
            column=4,
            label_text="更新开始列:",
            variable=self.update_start_column_var,
        )

        master_frame = self.create_section_card("Master 表列配置")
        self.master_key_col_var = tk.StringVar(value="2")
        self.master_match_col_var = tk.StringVar(value="3")
        self.start_column_var = tk.StringVar(value="5")
        create_labeled_entry(
            master_frame,
            row=0,
            column=0,
            label_text="Key 列:",
            variable=self.master_key_col_var,
            label_padx=(0, 0),
        )
        create_labeled_entry(
            master_frame,
            row=0,
            column=2,
            label_text="原文列:",
            variable=self.master_match_col_var,
        )
        create_labeled_entry(
            master_frame,
            row=0,
            column=4,
            label_text="内容开始列:",
            variable=self.start_column_var,
        )

        params_frame = self.create_section_card("处理参数")
        self.column_count_var = tk.StringVar(value="7")
        create_labeled_entry(
            params_frame,
            row=0,
            column=0,
            label_text="更新列数:",
            variable=self.column_count_var,
            label_padx=(0, 0),
        )

        toggle_frame = ttk.Frame(params_frame, style="Surface.TFrame")
        toggle_frame.grid(
            row=1,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(theme.SPACING_XS, 0),
        )

        self.post_process_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="启用后处理（兼容性保存）",
            variable=self.post_process_var,
            parent=toggle_frame,
            pady=(0, theme.SPACING_XXS),
        )

        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            parent=toggle_frame,
            pady=(0, theme.SPACING_XS),
        )

        self.allow_blank_write_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="允许写入空白值（谨慎）",
            variable=self.allow_blank_write_var,
            parent=toggle_frame,
            pady=(0, theme.SPACING_XS),
        )

        self.create_primary_button(
            text="开始处理",
            command=self.controller.process_multi_column,
        )

    def set_master_file_label(self, file_path):
        self.set_selected_file_label(self.master_label, file_path)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def get_config(self):
        return MultiColumnConfig(
            target_key_col=parse_column_1_based_to_0_based(self.target_key_col_var.get(), "目标 Key 列"),
            target_match_col=parse_column_1_based_to_0_based(self.match_column_var.get(), "目标原文列"),
            target_update_start_col=parse_column_1_based_to_0_based(
                self.update_start_column_var.get(),
                "目标更新开始列",
            ),
            master_key_col=parse_column_1_based_to_0_based(self.master_key_col_var.get(), "Master Key 列"),
            master_match_col=parse_column_1_based_to_0_based(self.master_match_col_var.get(), "Master 原文列"),
            master_start_col=parse_column_1_based_to_0_based(self.start_column_var.get(), "Master 内容开始列"),
            column_count=parse_positive_int(self.column_count_var.get(), "更新列数"),
            fill_blank_only=bool(self.fill_blank_var.get()),
            allow_blank_write=bool(self.allow_blank_write_var.get()),
            post_process_enabled=bool(self.post_process_var.get()),
        )
