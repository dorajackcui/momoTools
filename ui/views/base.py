import os
from tkinter import ttk

from ui import strings, theme
from ui.widgets.factory import create_action_button, create_path_status_label
from ui.widgets.toggle_switch import ToggleSwitch


class BaseFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="App.TFrame", padding=(theme.SPACING_XS, theme.SPACING_XS))

    def create_section_card(self, title, parent=None, padx=theme.SPACING_XS, pady=(0, theme.SPACING_SM)):
        card_parent = parent or self
        card = ttk.LabelFrame(card_parent, text=title, padding=(theme.SPACING_SM, theme.SPACING_XS))
        card.pack(fill="x", padx=padx, pady=pady)
        return card

    def create_toggle(self, text, variable, pady=(0, 0), parent=None, command=None):
        toggle_parent = parent or self
        toggle_bg = theme.SURFACE_BG if toggle_parent is not self else theme.APP_BG
        toggle = ToggleSwitch(
            toggle_parent,
            text=text,
            variable=variable,
            bg=toggle_bg,
            font=theme.FONT_DEFAULT,
            command=command,
        )
        toggle.pack(anchor="w", padx=theme.SPACING_XXS, pady=pady)
        return toggle

    def create_picker_with_status(
        self,
        button_text,
        command,
        default_text,
        button_style="Picker.TButton",
        button_pady=theme.SPACING_SM,
        status_pady=(2, 0),
        parent=None,
    ):
        container = parent or self
        create_action_button(
            container,
            text=button_text,
            command=command,
            button_style=button_style,
            pady=button_pady,
        )
        status_label = create_path_status_label(container, text=default_text, label_style="Status.TLabel")
        status_label.pack_configure(pady=status_pady, anchor="w")
        return status_label

    def create_primary_button(self, text, command, parent=None, pady=theme.SPACING_LG):
        return create_action_button(
            parent or self,
            text=text,
            command=command,
            button_style="Primary.TButton",
            pady=pady,
            processing_action=True,
        )

    @staticmethod
    def update_path_label(label_widget, path, default_text, formatter):
        if path:
            label_widget.config(text=formatter(path))
        else:
            label_widget.config(text=default_text)

        full_path = path or ""
        label_widget._full_path = full_path
        tooltip = getattr(label_widget, "_path_tooltip", None)
        if tooltip is not None and hasattr(tooltip, "set_text"):
            tooltip.set_text(full_path)

    @staticmethod
    def set_selected_path_label(label_widget, path):
        BaseFrame.update_path_label(
            label_widget=label_widget,
            path=path,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            formatter=strings.selected_path_text,
        )

    @staticmethod
    def set_output_path_label(label_widget, path):
        BaseFrame.update_path_label(
            label_widget=label_widget,
            path=path,
            default_text=strings.DEFAULT_OUTPUT_TEXT,
            formatter=strings.output_path_text,
        )

    @staticmethod
    def set_selected_file_label(label_widget, path):
        BaseFrame.update_path_label(
            label_widget=label_widget,
            path=path,
            default_text=strings.DEFAULT_FILE_TEXT,
            formatter=strings.selected_path_text,
        )

    @staticmethod
    def basename(path):
        return os.path.basename(path) if path else ""
