import tkinter as tk
from tkinter import ttk


class FileListConfirmDialog:
    def __init__(
        self,
        parent,
        *,
        title: str,
        file_paths: list[str],
        summary_lines: list[str],
        warning_message: str | None = None,
    ):
        self._parent = parent
        self._title = title
        self._file_paths = list(file_paths)
        self._summary_lines = [line for line in summary_lines if str(line or "").strip()]
        self._warning_message = str(warning_message or "").strip()
        self._result = False
        self._window = None

    def show(self) -> bool:
        self._build()
        assert self._window is not None
        self._window.wait_window()
        return self._result

    def _build(self) -> None:
        self._window = tk.Toplevel(self._parent)
        self._window.title(self._title)
        self._window.transient(self._parent.winfo_toplevel() if self._parent is not None else None)
        self._window.grab_set()
        self._window.resizable(True, True)
        self._window.minsize(520, 360)
        self._window.protocol("WM_DELETE_WINDOW", self._cancel)

        container = ttk.Frame(self._window, padding=12)
        container.pack(fill="both", expand=True)

        for line in self._summary_lines:
            ttk.Label(container, text=line, justify="left").pack(anchor="w")

        if self._warning_message:
            ttk.Label(
                container,
                text=self._warning_message,
                justify="left",
                foreground="#8A3B12",
            ).pack(anchor="w", pady=(8, 0))

        ttk.Label(container, text="Files to be used:").pack(anchor="w", pady=(10, 4))

        list_container = ttk.Frame(container)
        list_container.pack(fill="both", expand=True)

        listbox = tk.Listbox(
            list_container,
            activestyle="none",
            selectmode=tk.BROWSE,
            exportselection=False,
        )
        listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.configure(yscrollcommand=scrollbar.set)

        for index, path in enumerate(self._file_paths, start=1):
            listbox.insert(tk.END, f"{index}. {path}")

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Cancel", command=self._cancel, takefocus=False).pack(side="right")
        ttk.Button(actions, text="Confirm", command=self._confirm, takefocus=False).pack(
            side="right",
            padx=(0, 8),
        )

    def _confirm(self) -> None:
        self._result = True
        if self._window is not None:
            self._window.destroy()

    def _cancel(self) -> None:
        self._result = False
        if self._window is not None:
            self._window.destroy()
