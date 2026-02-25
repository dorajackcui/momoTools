import os
from tkinter import ttk

from ui import strings, theme
from ui.widgets.factory import create_action_button, create_status_label
from ui.widgets.toggle_switch import ToggleSwitch


class BaseFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.button_style = dict(theme.BUTTON_STYLE)
        self.label_style = dict(theme.LABEL_STYLE)

    def create_toggle(self, text, variable, pady=(0, 0), parent=None, command=None):
        toggle_parent = parent or self
        toggle = ToggleSwitch(
            toggle_parent,
            text=text,
            variable=variable,
            bg=theme.TOGGLE_STYLE["bg"],
            font=theme.TOGGLE_STYLE["font"],
            command=command,
        )
        toggle.pack(anchor="w", padx=10, pady=pady)
        return toggle

    def create_picker_with_status(
        self,
        button_text,
        command,
        default_text,
        button_pady=10,
    ):
        create_action_button(self, text=button_text, command=command, button_style=self.button_style, pady=button_pady)
        return create_status_label(self, text=default_text, label_style=self.label_style)

    @staticmethod
    def set_selected_path_label(label_widget, path):
        if path:
            label_widget.config(text=strings.selected_path_text(path))
        else:
            label_widget.config(text=strings.DEFAULT_FOLDER_TEXT)

    @staticmethod
    def set_output_path_label(label_widget, path):
        if path:
            label_widget.config(text=strings.output_path_text(path))
        else:
            label_widget.config(text=strings.DEFAULT_OUTPUT_TEXT)

    @staticmethod
    def set_selected_file_label(label_widget, path):
        if path:
            label_widget.config(text=strings.selected_path_text(path))
        else:
            label_widget.config(text=strings.DEFAULT_FILE_TEXT)

    @staticmethod
    def basename(path):
        return os.path.basename(path) if path else ""
