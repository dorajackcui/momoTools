import collections
from dataclasses import dataclass
import queue
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ui import strings
from controllers import (
    BatchController,
    ClearerController,
    CompatibilityController,
    DeepReplaceController,
    ReverseUpdaterController,
    TerminologyExtractorController,
    UntranslatedStatsController,
    UpdaterController,
)
from core.deep_replace_processor import DeepReplaceProcessor
from core.excel_cleaner import ExcelColumnClearer
from core.excel_compatibility_processor import ExcelCompatibilityProcessor
from core.excel_processor import ExcelProcessor
from core.multi_column_processor import MultiColumnExcelProcessor
from core.reverse_excel_processor import ReverseExcelProcessor
from core.terminology import TerminologyProcessor
from core.untranslated_stats_processor import UntranslatedStatsProcessor
from controller_modules.task_runner import TkSingleTaskRunner
from ui.theme import APP_BG, configure_ttk_style
from ui.widgets.log_window import LogWindow
from ui.views import (
    BatchFrame,
    ClearerFrame,
    CompatibilityFrame,
    DeepReplaceFrame,
    ReverseUpdaterFrame,
    TerminologyExtractorFrame,
    UntranslatedStatsFrame,
    UpdaterFrame,
)


@dataclass(frozen=True)
class ToolSpec:
    group: str
    tab_text: str
    controller_factory: Callable[["ExcelUpdaterApp"], object]
    frame_cls: type
    after_mount: Optional[Callable[[object], None]] = None


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
        )
        self.init_components()
        self.root.after(80, self._drain_log_queue)

    def setup_style(self):
        configure_ttk_style()

    def init_processors(self):
        self.excel_processor = ExcelProcessor(self._emit_log)
        self.clearer = ExcelColumnClearer()
        self.clearer.set_log_callback(self._emit_log)
        self.compatibility_processor = ExcelCompatibilityProcessor()
        self.compatibility_processor.set_log_callback(self._emit_log)
        self.multi_processor = MultiColumnExcelProcessor(self._emit_log)
        self.deep_replace_processor = DeepReplaceProcessor(self._emit_log)
        self.reverse_excel_processor = ReverseExcelProcessor(self._emit_log)
        self.untranslated_stats_processor = UntranslatedStatsProcessor(self._emit_log)
        self.terminology_processor = TerminologyProcessor(self._emit_log)

    def _build_tool_specs(self):
        return [
            ToolSpec(
                group="main",
                tab_text="Master->Target",
                controller_factory=lambda app: UpdaterController(
                    None, app.excel_processor, app.multi_processor, task_runner=app.task_runner
                ),
                frame_cls=UpdaterFrame,
            ),
            ToolSpec(
                group="main",
                tab_text="Target->Master",
                controller_factory=lambda app: ReverseUpdaterController(
                    None, app.reverse_excel_processor, task_runner=app.task_runner
                ),
                frame_cls=ReverseUpdaterFrame,
            ),
            ToolSpec(
                group="main",
                tab_text="Batch",
                controller_factory=lambda app: BatchController(
                    None,
                    app.excel_processor,
                    app.reverse_excel_processor,
                    task_runner=app.task_runner,
                ),
                frame_cls=BatchFrame,
                after_mount=lambda controller: controller.restore_persisted_paths(),
            ),
            ToolSpec(
                group="utilities",
                tab_text="Column Clear",
                controller_factory=lambda app: ClearerController(
                    None,
                    app.clearer,
                    task_runner=app.task_runner,
                ),
                frame_cls=ClearerFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Compatibility",
                controller_factory=lambda app: CompatibilityController(
                    None, app.compatibility_processor, task_runner=app.task_runner
                ),
                frame_cls=CompatibilityFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Deep Replace",
                controller_factory=lambda app: DeepReplaceController(
                    None, app.deep_replace_processor, task_runner=app.task_runner
                ),
                frame_cls=DeepReplaceFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Untranslated Stats",
                controller_factory=lambda app: UntranslatedStatsController(
                    None, app.untranslated_stats_processor, task_runner=app.task_runner
                ),
                frame_cls=UntranslatedStatsFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Term Extractor",
                controller_factory=lambda app: TerminologyExtractorController(
                    None, app.terminology_processor, task_runner=app.task_runner
                ),
                frame_cls=TerminologyExtractorFrame,
                after_mount=lambda controller: controller.restore_persisted_paths(),
            ),
        ]

    def init_components(self):
        top_group_frames = {
            "main": ttk.Frame(self.notebook),
            "utilities": ttk.Frame(self.notebook),
        }
        self.notebook.add(top_group_frames["main"], text="Main Tools")
        self.notebook.add(top_group_frames["utilities"], text="Utilities")

        group_notebooks = {
            "main": ttk.Notebook(top_group_frames["main"], takefocus=False),
            "utilities": ttk.Notebook(top_group_frames["utilities"], takefocus=False),
        }
        for notebook in group_notebooks.values():
            notebook.pack(expand=True, fill="both", padx=6, pady=6)

        for spec in self._build_tool_specs():
            notebook = group_notebooks[spec.group]
            controller = spec.controller_factory(self)
            frame = spec.frame_cls(notebook, controller)
            controller.frame = frame
            if spec.after_mount is not None:
                spec.after_mount(controller)
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

    def _drain_log_queue(self):
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

        try:
            self.root.after(80, self._drain_log_queue)
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
            try:
                widget.configure(state=target_state)
                continue
            except Exception:
                pass
            try:
                if is_busy:
                    widget.state(["disabled"])
                else:
                    widget.state(["!disabled"])
            except Exception:
                pass

    def _iter_descendants(self, root_widget):
        for child in root_widget.winfo_children():
            yield child
            yield from self._iter_descendants(child)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()
