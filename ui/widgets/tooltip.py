import tkinter as tk

from ui import theme


class HoverTooltip:
    """Simple hover tooltip with delayed show."""

    def __init__(self, widget, text="", delay_ms=150):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip_window = None

        self.widget.bind("<Enter>", self._schedule_show, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<ButtonPress>", self._hide, add="+")
        self.widget.bind("<Destroy>", self._on_destroy, add="+")

    def set_text(self, text):
        self.text = text
        if not text:
            self._hide()

    def _schedule_show(self, _event=None):
        if not self.text:
            return
        self._cancel_schedule()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel_schedule(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        if self._tip_window is not None or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except tk.TclError:
            return

        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        self._tip_window.configure(bg=theme.BORDER)

        label = tk.Label(
            self._tip_window,
            text=self.text,
            justify=tk.LEFT,
            bg=theme.SURFACE_BG,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_MUTED,
            relief=tk.SOLID,
            borderwidth=1,
            padx=theme.SPACING_XS,
            pady=theme.SPACING_XXS,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel_schedule()
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except tk.TclError:
                pass
            self._tip_window = None

    def _on_destroy(self, _event=None):
        self._hide()
