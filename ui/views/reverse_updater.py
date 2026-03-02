import tkinter as tk

from ui import strings, theme
from ui.validators import parse_column_1_based_to_0_based
from ui.view_models import ReverseConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_labeled_entry


class ReverseUpdaterFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("输入文件")
        self.master_label = self.create_picker_with_status(
            button_text="选择 Master 总表",
            command=self.controller.select_master_file,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )
        self.folder_label = self.create_picker_with_status(
            button_text="选择小表文件夹",
            command=self.controller.select_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=theme.SPACING_SM,
        )

        target_frame = self.create_section_card("小表列配置")
        self.target_key_col_var = tk.StringVar(value="1")
        self.target_match_col_var = tk.StringVar(value="2")
        self.target_content_col_var = tk.StringVar(value="3")
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
            variable=self.target_match_col_var,
        )
        create_labeled_entry(
            target_frame,
            row=0,
            column=4,
            label_text="译文列:",
            variable=self.target_content_col_var,
        )

        master_frame = self.create_section_card("Master 表列配置")
        self.master_key_col_var = tk.StringVar(value="2")
        self.master_match_col_var = tk.StringVar(value="3")
        self.master_update_col_var = tk.StringVar(value="4")
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
            label_text="译文列:",
            variable=self.master_update_col_var,
        )

        option_frame = self.create_section_card("更新选项")
        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            parent=option_frame,
            pady=(0, theme.SPACING_XS),
        )
        self.allow_blank_write_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="允许写入空白值（谨慎）",
            variable=self.allow_blank_write_var,
            parent=option_frame,
            pady=(0, theme.SPACING_XS),
        )

        self.create_primary_button(
            text="填充 Master 表",
            command=self.controller.process_files,
        )

    def set_master_file_label(self, file_path):
        self.set_selected_file_label(self.master_label, file_path)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def get_config(self):
        return ReverseConfig(
            target_key_col=parse_column_1_based_to_0_based(self.target_key_col_var.get(), "小表 Key 列"),
            target_match_col=parse_column_1_based_to_0_based(self.target_match_col_var.get(), "小表原文列"),
            target_content_col=parse_column_1_based_to_0_based(self.target_content_col_var.get(), "小表译文列"),
            master_key_col=parse_column_1_based_to_0_based(self.master_key_col_var.get(), "Master Key 列"),
            master_match_col=parse_column_1_based_to_0_based(self.master_match_col_var.get(), "Master 原文列"),
            master_update_col=parse_column_1_based_to_0_based(self.master_update_col_var.get(), "Master 译文列"),
            fill_blank_only=bool(self.fill_blank_var.get()),
            allow_blank_write=bool(self.allow_blank_write_var.get()),
        )
