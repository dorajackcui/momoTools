from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from controllers import (
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
from ui.theme import APP_BG, configure_ttk_style
from ui.views import (
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
        self.root.geometry("540x680")
        self.root.minsize(520, 640)
        self.root.resizable(True, True)
        self.root.configure(bg=APP_BG)

        self.setup_style()
        self.notebook = ttk.Notebook(self.root, takefocus=False)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)

        self.init_processors()
        self.init_components()

    def setup_style(self):
        configure_ttk_style()

    def init_processors(self):
        self.excel_processor = ExcelProcessor(print)
        self.clearer = ExcelColumnClearer()
        self.compatibility_processor = ExcelCompatibilityProcessor()
        self.multi_processor = MultiColumnExcelProcessor(print)
        self.deep_replace_processor = DeepReplaceProcessor(print)
        self.reverse_excel_processor = ReverseExcelProcessor(print)
        self.untranslated_stats_processor = UntranslatedStatsProcessor(print)
        self.terminology_processor = TerminologyProcessor(print)

    def _build_tool_specs(self):
        return [
            ToolSpec(
                group="main",
                tab_text="Master->Target",
                controller_factory=lambda app: UpdaterController(
                    None, app.excel_processor, app.multi_processor
                ),
                frame_cls=UpdaterFrame,
            ),
            ToolSpec(
                group="main",
                tab_text="Target->Master",
                controller_factory=lambda app: ReverseUpdaterController(
                    None, app.reverse_excel_processor
                ),
                frame_cls=ReverseUpdaterFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Column Clear",
                controller_factory=lambda app: ClearerController(None, app.clearer),
                frame_cls=ClearerFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Compatibility",
                controller_factory=lambda app: CompatibilityController(
                    None, app.compatibility_processor
                ),
                frame_cls=CompatibilityFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Deep Replace",
                controller_factory=lambda app: DeepReplaceController(
                    None, app.deep_replace_processor
                ),
                frame_cls=DeepReplaceFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Untranslated Stats",
                controller_factory=lambda app: UntranslatedStatsController(
                    None, app.untranslated_stats_processor
                ),
                frame_cls=UntranslatedStatsFrame,
            ),
            ToolSpec(
                group="utilities",
                tab_text="Term Extractor",
                controller_factory=lambda app: TerminologyExtractorController(
                    None, app.terminology_processor
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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()
