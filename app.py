import tkinter as tk
from tkinter import ttk
from ui.views import UpdaterFrame, ClearerFrame, CompatibilityFrame, DeepReplaceFrame, ReverseUpdaterFrame, UntranslatedStatsFrame
from controllers import UpdaterController, ClearerController, CompatibilityController, DeepReplaceController, ReverseUpdaterController, UntranslatedStatsController
from core.excel_processor import ExcelProcessor
from core.excel_cleaner import ExcelColumnClearer
from core.excel_compatibility_processor import ExcelCompatibilityProcessor
from core.multi_column_processor import MultiColumnExcelProcessor
from core.deep_replace_processor import DeepReplaceProcessor
from core.reverse_excel_processor import ReverseExcelProcessor
from core.untranslated_stats_processor import UntranslatedStatsProcessor
from ui.theme import APP_BG, configure_ttk_style

class ExcelUpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Momo——Build your mastersheet")
        self.root.geometry("540x640")
        self.root.minsize(520, 620)
        self.root.resizable(True, True)
        self.root.configure(bg=APP_BG)
        
        # 设置主题和样式
        self.setup_style()
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root, takefocus=False)
        self.notebook.pack(expand=True, fill='both', padx=6, pady=6)
        
        # 初始化处理器
        self.init_processors()
        
        # 初始化控制器和UI组件
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

    def init_components(self):
        # 创建主分类的 Frame
        main_tools_frame = ttk.Frame(self.notebook)
        utilities_frame = ttk.Frame(self.notebook)

        # 将主 Frame 添加为顶级标签页
        self.notebook.add(main_tools_frame, text='填表工具')
        self.notebook.add(utilities_frame, text='辅助工具')

        # --- 创建嵌套的 Notebook ---
        main_notebook = ttk.Notebook(main_tools_frame, takefocus=False)
        main_notebook.pack(expand=True, fill='both', padx=6, pady=6)

        utilities_notebook = ttk.Notebook(utilities_frame, takefocus=False)
        utilities_notebook.pack(expand=True, fill='both', padx=6, pady=6)

        # --- 主要工具 ---
        # 批量更新工具
        updater_controller = UpdaterController(None, self.excel_processor, self.multi_processor)
        updater_frame = UpdaterFrame(main_notebook, updater_controller)
        updater_controller.frame = updater_frame
        main_notebook.add(updater_frame, text='Master到小表')

        # 反向批量更新工具
        reverse_updater_controller = ReverseUpdaterController(None, self.reverse_excel_processor)
        reverse_updater_frame = ReverseUpdaterFrame(main_notebook, reverse_updater_controller)
        reverse_updater_controller.frame = reverse_updater_frame
        main_notebook.add(reverse_updater_frame, text='小表到Master')

        # --- 辅助工具 ---
        # 列清空工具
        clearer_controller = ClearerController(None, self.clearer)
        clearer_frame = ClearerFrame(utilities_notebook, clearer_controller)
        clearer_controller.frame = clearer_frame
        utilities_notebook.add(clearer_frame, text='列清空')

        # 兼容性处理工具
        compatibility_controller = CompatibilityController(None, self.compatibility_processor)
        compatibility_frame = CompatibilityFrame(utilities_notebook, compatibility_controller)
        compatibility_controller.frame = compatibility_frame
        utilities_notebook.add(compatibility_frame, text='兼容性处理')

        # 深度替换工具
        deep_replace_controller = DeepReplaceController(None, self.deep_replace_processor)
        deep_replace_frame = DeepReplaceFrame(utilities_notebook, deep_replace_controller)
        deep_replace_controller.frame = deep_replace_frame
        utilities_notebook.add(deep_replace_frame, text='深度替换')

        # 统计未翻译字数工具
        untranslated_stats_controller = UntranslatedStatsController(None, self.untranslated_stats_processor)
        untranslated_stats_frame = UntranslatedStatsFrame(utilities_notebook, untranslated_stats_controller)
        untranslated_stats_controller.frame = untranslated_stats_frame
        utilities_notebook.add(untranslated_stats_frame, text='字数统计')



    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()
