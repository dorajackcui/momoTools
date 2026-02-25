from tkinter import ttk

APP_BG = "#f0f0f0"
PRIMARY_BUTTON_BG = "#4a90e2"
PRIMARY_BUTTON_FG = "white"
LABEL_FG = "#333333"

DEFAULT_FONT = ("Arial", 10)
TOGGLE_FONT = ("Arial", 10)

BUTTON_STYLE = {
    "bg": PRIMARY_BUTTON_BG,
    "fg": PRIMARY_BUTTON_FG,
    "font": DEFAULT_FONT,
    "relief": "raised",
    "padx": 20,
}

LABEL_STYLE = {
    "bg": APP_BG,
    "fg": LABEL_FG,
    "font": DEFAULT_FONT,
}

TOGGLE_STYLE = {
    "bg": APP_BG,
    "font": TOGGLE_FONT,
}

TAB_STYLE = {
    "padding": [20, 8],
    "background": "#e0e0e0",
    "foreground": LABEL_FG,
    "borderwidth": 1,
    "font": DEFAULT_FONT,
}


def configure_ttk_style():
    """Apply the current ttk style baseline used by the app."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background=APP_BG, borderwidth=0)
    style.configure("TNotebook.Tab", **TAB_STYLE)
    style.map(
        "TNotebook.Tab",
        padding=[("selected", [20, 8])],
        background=[("selected", PRIMARY_BUTTON_BG), ("active", "#b8d6f5")],
        foreground=[("selected", "white"), ("active", LABEL_FG)],
    )
    style.configure("TFrame", background=APP_BG)

    # Remove focus dash border when tab is selected.
    style.layout(
        "TNotebook.Tab",
        [
            (
                "Notebook.tab",
                {
                    "sticky": "nswe",
                    "children": [
                        (
                            "Notebook.padding",
                            {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [("Notebook.label", {"side": "top", "sticky": ""})],
                            },
                        )
                    ],
                },
            )
        ],
    )

