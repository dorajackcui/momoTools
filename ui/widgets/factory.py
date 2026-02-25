import tkinter as tk
from tkinter import ttk

from ui import theme
from ui.widgets.tooltip import HoverTooltip


def create_action_button(
    parent,
    text,
    command,
    button_style="Picker.TButton",
    pady=theme.SPACING_SM,
    padx=0,
    side=None,
):
    tk_style = theme.TK_BUTTON_STYLE_MAP.get(button_style)
    if tk_style is not None:
        button = tk.Button(parent, text=text, command=command, **tk_style)
    else:
        button = ttk.Button(parent, text=text, command=command, style=button_style, takefocus=False)
    pack_kwargs = {"pady":pady}
    if padx:
        pack_kwargs["padx"] = padx
    if side is not None:
        pack_kwargs["side"] = side
    button.pack(**pack_kwargs)
    return button


def create_status_label(parent, text, label_style="Surface.TLabel", pady=0, pack=True, **pack_kwargs):
    label = ttk.Label(parent, text=text, style=label_style)
    if pack:
        if "pady" not in pack_kwargs:
            pack_kwargs["pady"] = pady
        label.pack(**pack_kwargs)
    return label


def create_path_status_label(parent, text, label_style="Surface.TLabel", pack=True, **pack_kwargs):
    label = create_status_label(parent, text=text, label_style=label_style, pack=pack, **pack_kwargs)
    label._path_tooltip = HoverTooltip(label, text="")
    label._full_path = ""
    return label


def create_labeled_entry(
    parent,
    row,
    column,
    label_text,
    variable,
    width=5,
    label_padx=(theme.SPACING_XS, 0),
):
    ttk.Label(parent, text=label_text).grid(
        row=row,
        column=column,
        sticky="w",
        padx=label_padx,
        pady=(theme.SPACING_XXS, theme.SPACING_XXS),
    )
    entry = ttk.Entry(parent, textvariable=variable, width=width)
    entry.grid(row=row, column=column + 1, pady=(theme.SPACING_XXS, theme.SPACING_XXS))
    return entry

