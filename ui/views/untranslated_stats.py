import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import ValidationError, parse_column_1_based_to_0_based
from ui.view_models import StatsConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_action_button, create_labeled_entry, create_path_status_label


class UntranslatedStatsFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("输入文件")
        self.folder_label = self.create_picker_with_status(
            button_text="选择小表文件夹",
            command=self.controller.select_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        column_frame = self.create_section_card("列配置")
        self.source_col_var = tk.StringVar(value="2")
        self.translation_col_var = tk.StringVar(value="3")
        create_labeled_entry(column_frame, row=0, column=0, label_text="原文列:", variable=self.source_col_var, label_padx=(0, 0))
        create_labeled_entry(column_frame, row=0, column=2, label_text="译文列:", variable=self.translation_col_var)

        mode_frame = self.create_section_card("统计模式")
        self.stats_mode_var = tk.StringVar(value="chinese_chars")
        ttk.Radiobutton(
            mode_frame,
            text="中文字符模式",
            variable=self.stats_mode_var,
            value="chinese_chars",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            mode_frame,
            text="英文词模式",
            variable=self.stats_mode_var,
            value="english_words",
        ).grid(row=0, column=1, sticky="w", padx=(20, 0))

        output_wrap = self.create_section_card("输出文件")
        output_frame = ttk.Frame(output_wrap, style="Surface.TFrame")
        output_frame.pack(fill="x", pady=(0, theme.SPACING_XXS))
        create_action_button(
            output_frame,
            text="选择输出文件（可选）",
            command=self.controller.select_output_file,
            button_style="Picker.TButton",
            side=tk.LEFT,
            pady=0,
        )
        self.output_label = create_path_status_label(
            output_frame,
            text=strings.DEFAULT_OUTPUT_TEXT,
            label_style="Status.TLabel",
            pack=False,
        )
        self.output_label.pack(side=tk.LEFT, padx=(10, 0))

        self.create_primary_button(
            text="统计未翻译字数",
            command=self.controller.process_stats,
        )

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
