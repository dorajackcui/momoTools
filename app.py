import tkinter as tk
from tkinter import ttk

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


class ExcelUpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Momo——Build your mastersheet")
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

    def init_components(self):
        main_tools_frame = ttk.Frame(self.notebook)
        utilities_frame = ttk.Frame(self.notebook)

        self.notebook.add(main_tools_frame, text="Main Tools")
        self.notebook.add(utilities_frame, text="Utilities")

        main_notebook = ttk.Notebook(main_tools_frame, takefocus=False)
        main_notebook.pack(expand=True, fill="both", padx=6, pady=6)

        utilities_notebook = ttk.Notebook(utilities_frame, takefocus=False)
        utilities_notebook.pack(expand=True, fill="both", padx=6, pady=6)

        updater_controller = UpdaterController(None, self.excel_processor, self.multi_processor)
        updater_frame = UpdaterFrame(main_notebook, updater_controller)
        updater_controller.frame = updater_frame
        main_notebook.add(updater_frame, text="Master->Target")

        reverse_updater_controller = ReverseUpdaterController(None, self.reverse_excel_processor)
        reverse_updater_frame = ReverseUpdaterFrame(main_notebook, reverse_updater_controller)
        reverse_updater_controller.frame = reverse_updater_frame
        main_notebook.add(reverse_updater_frame, text="Target->Master")

        clearer_controller = ClearerController(None, self.clearer)
        clearer_frame = ClearerFrame(utilities_notebook, clearer_controller)
        clearer_controller.frame = clearer_frame
        utilities_notebook.add(clearer_frame, text="Column Clear")

        compatibility_controller = CompatibilityController(None, self.compatibility_processor)
        compatibility_frame = CompatibilityFrame(utilities_notebook, compatibility_controller)
        compatibility_controller.frame = compatibility_frame
        utilities_notebook.add(compatibility_frame, text="Compatibility")

        deep_replace_controller = DeepReplaceController(None, self.deep_replace_processor)
        deep_replace_frame = DeepReplaceFrame(utilities_notebook, deep_replace_controller)
        deep_replace_controller.frame = deep_replace_frame
        utilities_notebook.add(deep_replace_frame, text="Deep Replace")

        untranslated_stats_controller = UntranslatedStatsController(None, self.untranslated_stats_processor)
        untranslated_stats_frame = UntranslatedStatsFrame(utilities_notebook, untranslated_stats_controller)
        untranslated_stats_controller.frame = untranslated_stats_frame
        utilities_notebook.add(untranslated_stats_frame, text="Untranslated Stats")

        terminology_controller = TerminologyExtractorController(None, self.terminology_processor)
        terminology_frame = TerminologyExtractorFrame(utilities_notebook, terminology_controller)
        terminology_controller.frame = terminology_frame
        terminology_controller.restore_persisted_paths()
        utilities_notebook.add(terminology_frame, text="Term Extractor")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()
