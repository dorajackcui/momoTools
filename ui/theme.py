import tkinter as tk
from tkinter import ttk

APP_BG = "#F3F3F3"
SURFACE_BG = "#FFFFFF"
SURFACE_ALT = "#F7F7F7"
BORDER = "#D9D9D9"
TEXT_PRIMARY = "#202124"
TEXT_SECONDARY = "#616161"
ACCENT = "#0A66D9"
ACCENT_HOVER = "#0759BF"
PICKER_BG = "#E8F1FF"
PICKER_HOVER = "#D7E7FF"
PICKER_FG = "#1F4FA3"
SECONDARY_BG = "#EEF4FF"
SECONDARY_HOVER = "#E2ECFF"
SECONDARY_FG = "#2E4E8C"
DANGER_BG = "#FCEBEC"
DANGER_HOVER = "#F8DADC"
DANGER_FG = "#A73D3D"

FONT_DEFAULT = ("Microsoft YaHei UI", 10)
FONT_MUTED = ("Microsoft YaHei UI", 8)
FONT_STATUS = ("Microsoft YaHei UI", 8)

SPACING_XXS = 3
SPACING_XS = 6
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 14

TK_BUTTON_STYLE_MAP = {
    "Primary.TButton": {
        "bg": ACCENT,
        "fg": "#FFFFFF",
        "activebackground": ACCENT_HOVER,
        "activeforeground": "#FFFFFF",
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 0,
        "takefocus": 0,
        "font": FONT_DEFAULT,
        "padx": 10,
        "pady": 4,
    },
    "Picker.TButton": {
        "bg": PICKER_BG,
        "fg": PICKER_FG,
        "activebackground": PICKER_HOVER,
        "activeforeground": PICKER_FG,
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 0,
        "takefocus": 0,
        "font": FONT_DEFAULT,
        "padx": 10,
        "pady": 4,
    },
    "Secondary.TButton": {
        "bg": SECONDARY_BG,
        "fg": SECONDARY_FG,
        "activebackground": SECONDARY_HOVER,
        "activeforeground": SECONDARY_FG,
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 0,
        "takefocus": 0,
        "font": FONT_DEFAULT,
        "padx": 10,
        "pady": 4,
    },
    "Danger.TButton": {
        "bg": DANGER_BG,
        "fg": DANGER_FG,
        "activebackground": DANGER_HOVER,
        "activeforeground": DANGER_FG,
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 0,
        "takefocus": 0,
        "font": FONT_DEFAULT,
        "padx": 10,
        "pady": 4,
    },
}


def configure_ttk_style():
    """Apply a native-first ttk style profile."""
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except tk.TclError:
        style.theme_use("default")

    style.configure(".", font=FONT_DEFAULT)
    style.configure("App.TFrame", background=APP_BG)
    style.configure("Surface.TFrame", background=SURFACE_BG)
    style.configure("Surface.TLabel", background=SURFACE_BG, foreground=TEXT_PRIMARY, font=FONT_DEFAULT)
    style.configure("SurfaceMuted.TLabel", background=SURFACE_BG, foreground=TEXT_SECONDARY, font=FONT_MUTED)
    style.configure("Status.TLabel", background=SURFACE_BG, foreground=TEXT_SECONDARY, font=FONT_STATUS)

    # Keep only one branded accent style for primary actions.
    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#FFFFFF",
        borderwidth=1,
        relief="flat",
        padding=(SPACING_MD, SPACING_XS),
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_HOVER), ("disabled", SURFACE_ALT)],
        foreground=[("disabled", TEXT_SECONDARY)],
    )
