import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class LogWindow:
    def __init__(
        self,
        root,
        *,
        title: str = "Execution Logs",
        on_clear: Optional[Callable[[], None]] = None,
    ):
        self._root = root
        self._title = title
        self._on_clear = on_clear
        self._window = None
        self._text = None

    def is_alive(self) -> bool:
        if self._window is None:
            return False
        try:
            return bool(self._window.winfo_exists())
        except Exception:
            return False

    def show(self) -> None:
        if self.is_alive():
            self._window.deiconify()
            self._window.lift()
            self._window.focus_force()
            return

        self._window = tk.Toplevel(self._root)
        self._window.title(self._title)
        self._window.geometry("860x420")
        self._window.minsize(560, 280)
        self._window.protocol("WM_DELETE_WINDOW", self._close)

        body = ttk.Frame(self._window)
        body.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        scrollbar = ttk.Scrollbar(body, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._text = tk.Text(
            body,
            wrap="word",
            state="disabled",
            yscrollcommand=scrollbar.set,
        )
        self._text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self._text.yview)

        actions = ttk.Frame(self._window)
        actions.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(actions, text="Clear", command=self.clear, takefocus=False).pack(side="left")
        ttk.Button(actions, text="Close", command=self._close, takefocus=False).pack(side="right")

    def set_all(self, lines: list[str]) -> None:
        if not self.is_alive() or self._text is None:
            return
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        if lines:
            self._text.insert("end", "\n".join(lines) + "\n")
            self._text.see("end")
        self._text.configure(state="disabled")

    def append_lines(self, lines: list[str]) -> None:
        if not lines or not self.is_alive() or self._text is None:
            return
        self._text.configure(state="normal")
        self._text.insert("end", "\n".join(lines) + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        if self.is_alive() and self._text is not None:
            self._text.configure(state="normal")
            self._text.delete("1.0", "end")
            self._text.configure(state="disabled")
        if self._on_clear is not None:
            self._on_clear()

    def _close(self) -> None:
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass
        self._window = None
        self._text = None
