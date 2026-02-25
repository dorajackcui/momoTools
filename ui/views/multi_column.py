import tkinter as tk
from tkinter import ttk

from ui import strings
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
        self.master_label = self.create_picker_with_status(
            button_text="选择 Master 总表",
            command=self.controller.select_multi_master_file,
            default_text=strings.DEFAULT_FILE_TEXT,
        )
        self.folder_label = self.create_picker_with_status(
            button_text="选择目标文件夹",
            command=self.controller.select_multi_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
        )

        target_frame = ttk.LabelFrame(self, text="目标文件列配置", padding=(10, 5))
        target_frame.pack(pady=10, padx=10, fill="x")
        self.target_key_col_var = tk.StringVar(value="2")
        self.match_column_var = tk.StringVar(value="3")
        self.update_start_column_var = tk.StringVar(value="5")
        create_labeled_entry(target_frame, row=0, column=0, label_text="Key 列:", variable=self.target_key_col_var, label_padx=(0, 0))
        create_labeled_entry(target_frame, row=0, column=2, label_text="原文列:", variable=self.match_column_var)
        create_labeled_entry(target_frame, row=0, column=4, label_text="更新开始列:", variable=self.update_start_column_var)

        master_frame = ttk.LabelFrame(self, text="Master表列配置", padding=(10, 5))
        master_frame.pack(pady=10, padx=10, fill="x")
        self.master_key_col_var = tk.StringVar(value="2")
        self.master_match_col_var = tk.StringVar(value="3")
        self.start_column_var = tk.StringVar(value="5")
        create_labeled_entry(master_frame, row=0, column=0, label_text="Key 列:", variable=self.master_key_col_var, label_padx=(0, 0))
        create_labeled_entry(master_frame, row=0, column=2, label_text="原文列:", variable=self.master_match_col_var)
        create_labeled_entry(master_frame, row=0, column=4, label_text="内容开始列:", variable=self.start_column_var)

        params_frame = ttk.LabelFrame(self, text="处理参数", padding=(10, 5))
        params_frame.pack(pady=10, padx=10, fill="x")
        self.column_count_var = tk.StringVar(value="7")
        create_labeled_entry(params_frame, row=0, column=0, label_text="更新列数:", variable=self.column_count_var, label_padx=(0, 0))

        self.post_process_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="启用后处理（兼容性保存）",
            variable=self.post_process_var,
            pady=(5, 5),
        )

        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            pady=(0, 5),
        )

        tk.Button(
            self,
            text="开始处理",
            command=self.controller.process_multi_column,
            **self.button_style,
        ).pack(pady=20)

    def set_master_file_label(self, file_path):
        self.set_selected_file_label(self.master_label, file_path)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def get_config(self):
        return MultiColumnConfig(
            target_key_col=parse_column_1_based_to_0_based(self.target_key_col_var.get(), "目标 Key 列"),
            target_match_col=parse_column_1_based_to_0_based(self.match_column_var.get(), "目标原文列"),
            target_update_start_col=parse_column_1_based_to_0_based(self.update_start_column_var.get(), "目标更新开始列"),
            master_key_col=parse_column_1_based_to_0_based(self.master_key_col_var.get(), "Master Key 列"),
            master_match_col=parse_column_1_based_to_0_based(self.master_match_col_var.get(), "Master 原文列"),
            master_start_col=parse_column_1_based_to_0_based(self.start_column_var.get(), "Master 内容开始列"),
            column_count=parse_positive_int(self.column_count_var.get(), "更新列数"),
            fill_blank_only=bool(self.fill_blank_var.get()),
            post_process_enabled=bool(self.post_process_var.get()),
        )

