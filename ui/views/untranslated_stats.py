import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import ValidationError, parse_column_1_based_to_0_based
from ui.view_models import StatsConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_labeled_entry


class UntranslatedStatsFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.folder_label = self.create_picker_with_status(
            button_text="选择小表文件夹",
            command=self.controller.select_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
        )

        column_frame = ttk.LabelFrame(self, text="列配置", padding=(10, 5))
        column_frame.pack(pady=10, padx=10, fill="x")
        self.source_col_var = tk.StringVar(value="2")
        self.translation_col_var = tk.StringVar(value="3")
        create_labeled_entry(column_frame, row=0, column=0, label_text="原文列:", variable=self.source_col_var, label_padx=(0, 0))
        create_labeled_entry(column_frame, row=0, column=2, label_text="译文列:", variable=self.translation_col_var)

        mode_frame = ttk.LabelFrame(self, text="统计模式", padding=(10, 5))
        mode_frame.pack(pady=10, padx=10, fill="x")
        self.stats_mode_var = tk.StringVar(value="chinese_chars")
        tk.Radiobutton(
            mode_frame,
            text="中文字符模式",
            variable=self.stats_mode_var,
            value="chinese_chars",
            bg=theme.APP_BG,
        ).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(
            mode_frame,
            text="英文词模式",
            variable=self.stats_mode_var,
            value="english_words",
            bg=theme.APP_BG,
        ).grid(row=0, column=1, sticky="w", padx=(20, 0))

        output_frame = tk.Frame(self, bg=theme.APP_BG)
        output_frame.pack(pady=10, fill="x", padx=10)
        tk.Button(
            output_frame,
            text="选择输出文件",
            command=self.controller.select_output_file,
            **self.button_style,
        ).pack(side=tk.LEFT)
        self.output_label = tk.Label(output_frame, text=strings.DEFAULT_OUTPUT_TEXT, **self.label_style)
        self.output_label.pack(side=tk.LEFT, padx=(10, 0))

        tk.Button(
            self,
            text="统计未翻译字数",
            command=self.controller.process_stats,
            **self.button_style,
        ).pack(pady=20)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def set_output_file_label(self, output_path):
        self.set_output_path_label(self.output_label, output_path)

    # Backward compatibility for existing call sites.
    def update_folder_label(self, folder_path):
        self.set_target_folder_label(folder_path)

    def update_output_label(self, output_path):
        self.set_output_file_label(output_path)

    def get_config(self):
        mode = self.stats_mode_var.get()
        if mode not in ("chinese_chars", "english_words"):
            raise ValidationError("统计模式无效")

        return StatsConfig(
            source_col=parse_column_1_based_to_0_based(self.source_col_var.get(), "原文列"),
            translation_col=parse_column_1_based_to_0_based(self.translation_col_var.get(), "译文列"),
            stats_mode=mode,
        )

