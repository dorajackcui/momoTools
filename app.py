import collections
import queue
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

from app_shell import registry as app_registry
from ui import strings
from app_shell.services import build_processors
from controller_modules.task_runner import TkSingleTaskRunner
from ui.theme import APP_BG, configure_ttk_style
from ui.widgets.log_window import LogWindow


class ExcelUpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Momo build your mastersheet")
        self.root.geometry("540x700")
        self.root.minsize(520, 640)
        self.root.resizable(True, True)
        self.root.configure(bg=APP_BG)

        self.setup_style()
        self.notebook = ttk.Notebook(self.root, takefocus=False)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)
        self._task_status_text = "Ready"
        self._latest_log_line = ""
        self._log_queue = queue.Queue()
        self._log_buffer = collections.deque(maxlen=2000)
        self._log_window = None
        self._closing = False
        self._app_diagnostic_once_keys = set()

        self.status_var = tk.StringVar(value="Ready")
        self.status_row = ttk.Frame(self.root, style="App.TFrame")
        self.status_row.pack(fill="x", padx=6, pady=(0, 6))
        self.status_label = ttk.Label(self.status_row, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.view_logs_button = ttk.Button(
            self.status_row,
            text=strings.VIEW_LOGS_BUTTON,
            command=self._open_log_window,
            takefocus=False,
        )
        self.view_logs_button.pack(side="right")

        self.init_processors()
        self.task_runner = TkSingleTaskRunner(
            root=self.root,
            set_busy=self._set_processing_busy,
            set_status=self._set_status_text,
            diagnostic_sink=self._emit_log,
        )
        self.root.protocol("WM_DELETE_WINDOW", self._on_root_close)
        self.init_components()
        self.root.after(80, self._drain_log_queue)

    def setup_style(self):
        configure_ttk_style()

    def init_processors(self):
        bundle = build_processors(self._emit_log)
        for attr_name, value in vars(bundle).items():
            setattr(self, attr_name, value)

    def _build_tool_specs(self):
        return list(app_registry.build_tool_specs())

    def init_components(self):
        group_specs = app_registry.build_tool_groups()
        top_group_frames = {}
        for group_spec in group_specs:
            group_frame = ttk.Frame(self.notebook)
            top_group_frames[group_spec.key] = group_frame
            self.notebook.add(group_frame, text=group_spec.title)

        group_notebooks = {}
        for group_spec in group_specs:
            group_notebook = ttk.Notebook(top_group_frames[group_spec.key], takefocus=False)
            group_notebooks[group_spec.key] = group_notebook

        for notebook in group_notebooks.values():
            notebook.pack(expand=True, fill="both", padx=6, pady=6)

        for spec in self._build_tool_specs():
            notebook = group_notebooks[spec.group]
            processor_args = [getattr(self, attr_name) for attr_name in spec.processor_attrs]
            controller = spec.controller_cls(None, *processor_args, task_runner=self.task_runner)
            frame = spec.frame_cls(notebook, controller)
            controller.frame = frame
            for hook_name in spec.after_mount_hooks:
                getattr(controller, hook_name)()
            notebook.add(frame, text=spec.tab_text)

    def _set_status_text(self, text: str):
        self._task_status_text = text or "Ready"
        self._refresh_status_label()
        if self._is_task_status_text(self._task_status_text):
            self._emit_log(self._task_status_text)

    @staticmethod
    def _is_task_status_text(text: str) -> bool:
        return text.startswith("Running:") or text.startswith("Done:") or text.startswith("Failed:")

    def _refresh_status_label(self):
        if self._is_task_status_text(self._task_status_text):
            display_text = self._task_status_text
        elif self._latest_log_line:
            display_text = self._latest_log_line
        else:
            display_text = self._task_status_text or "Ready"
        self.status_var.set(display_text)

    def _emit_log(self, message: str):
        text = str(message).strip()
        if not text:
            return
        timestamp = time.strftime("%H:%M:%S")
        self._log_queue.put(f"[{timestamp}] {text}")

    def _emit_app_diagnostic(self, code: str, detail: str, exc: Optional[BaseException] = None, *, dedupe_key=None):
        once_keys = getattr(self, "_app_diagnostic_once_keys", None)
        if once_keys is None:
            once_keys = set()
            self._app_diagnostic_once_keys = once_keys

        key = code if dedupe_key is None else dedupe_key
        if key in once_keys:
            return
        once_keys.add(key)

        message = f"{code}: {detail}"
        if exc is not None:
            message = f"{message} - {type(exc).__name__}: {exc}"
        self._emit_log(message)

    def _flush_log_queue(self):
        new_lines = []
        while True:
            try:
                line = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self._log_buffer.append(line)
            new_lines.append(line)

        if new_lines:
            self._latest_log_line = new_lines[-1]
            self._refresh_status_label()
            if self._log_window is not None and self._log_window.is_alive():
                self._log_window.append_lines(new_lines)

    def _drain_log_queue(self):
        drain_pending = getattr(getattr(self, "task_runner", None), "drain_pending_completions", None)
        if callable(drain_pending):
            drain_pending()

        self._flush_log_queue()

        try:
            self.root.after(80, self._drain_log_queue)
        except Exception as exc:
            if getattr(self, "_closing", False):
                return
            self._emit_app_diagnostic(
                "APP_LOG_PUMP_SCHEDULE_FAILED",
                "Unable to schedule the next log queue drain",
                exc=exc,
            )
            self._flush_log_queue()

    def _on_root_close(self):
        self._closing = True
        shutdown = getattr(getattr(self, "task_runner", None), "shutdown", None)
        if callable(shutdown):
            shutdown()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _open_log_window(self):
        if self._log_window is None:
            self._log_window = LogWindow(
                self.root,
                title=strings.LOG_WINDOW_TITLE,
                on_clear=self._clear_log_buffer,
            )
        self._log_window.show()
        self._log_window.set_all(list(self._log_buffer))

    def _clear_log_buffer(self):
        self._log_buffer.clear()
        self._latest_log_line = ""
        if self._log_window is not None and self._log_window.is_alive():
            self._log_window.set_all([])
        self._refresh_status_label()

    def _set_processing_busy(self, is_busy: bool):
        target_state = "disabled" if is_busy else "normal"
        for widget in self._iter_descendants(self.root):
            if not getattr(widget, "_processing_action", False):
                continue
            configure_error = None
            try:
                widget.configure(state=target_state)
                continue
            except Exception as exc:
                configure_error = exc
            state_error = None
            try:
                if is_busy:
                    widget.state(["disabled"])
                else:
                    widget.state(["!disabled"])
            except Exception as exc:
                state_error = exc

            if configure_error is not None and state_error is not None:
                widget_name = type(widget).__name__
                detail = (
                    f"widget={widget_name}, target_state={target_state}, "
                    f"configure_error={type(configure_error).__name__}, "
                    f"state_error={type(state_error).__name__}"
                )
                self._emit_app_diagnostic(
                    "APP_WIDGET_BUSY_STATE_FAILED",
                    detail,
                    exc=state_error,
                    dedupe_key=("APP_WIDGET_BUSY_STATE_FAILED", widget_name, target_state),
                )

    def _iter_descendants(self, root_widget):
        for child in root_widget.winfo_children():
            yield child
            yield from self._iter_descendants(child)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()
