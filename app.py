import tkinter as tk
from tkinter import ttk
from ui_components import UpdaterFrame, ClearerFrame, CompatibilityFrame, MultiColumnFrame, DeepReplaceFrame
from controllers import UpdaterController, ClearerController, CompatibilityController, MultiColumnController, DeepReplaceController
from core.excel_processor import ExcelProcessor
from core.excel_cleaner import ExcelColumnClearer
from core.excel_compatibility_processor import ExcelCompatibilityProcessor
from core.multi_column_processor import MultiColumnExcelProcessor
from core.deep_replace_processor import DeepReplaceProcessor

class ExcelUpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Excel 工具集")
        self.root.geometry("400x500")
        self.root.configure(bg='#f0f0f0')
        
        # 设置主题和样式
        self.setup_style()
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # 初始化处理器
        self.init_processors()
        
        # 初始化控制器和UI组件
        self.init_components()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#f0f0f0', borderwidth=0)
        style.configure('TNotebook.Tab', 
            padding=[20, 8], 
            background='#e0e0e0', 
            foreground='#333333', 
            borderwidth=1,
            font=('Arial', 10)
        )
        style.map('TNotebook.Tab',
            padding=[('selected', [20, 8])],
            background=[('selected', '#4a90e2'), ('active', '#b8d6f5')],
            foreground=[('selected', 'white'), ('active', '#333333')]
        )
        style.configure('TFrame', background='#f0f0f0')

    def init_processors(self):
        self.excel_processor = ExcelProcessor(print)
        self.clearer = ExcelColumnClearer()
        self.compatibility_processor = ExcelCompatibilityProcessor()
        self.multi_processor = MultiColumnExcelProcessor(print)
        self.deep_replace_processor = DeepReplaceProcessor(print)

    def init_components(self):
        
        # 列清空工具
        clearer_controller = ClearerController(None, self.clearer)
        clearer_frame = ClearerFrame(self.notebook, clearer_controller)
        clearer_controller.frame = clearer_frame
        self.notebook.add(clearer_frame, text='列清空')

        # 批量更新工具
        updater_controller = UpdaterController(None, self.excel_processor)
        updater_frame = UpdaterFrame(self.notebook, updater_controller)
        updater_controller.frame = updater_frame
        self.notebook.add(updater_frame, text='批量更新')

        # 多列更新工具
        multi_controller = MultiColumnController(None, self.multi_processor)
        multi_frame = MultiColumnFrame(self.notebook, multi_controller)
        multi_controller.frame = multi_frame
        self.notebook.add(multi_frame, text='多列更新')

        # 深度替换工具
        deep_replace_controller = DeepReplaceController(None, self.deep_replace_processor)
        deep_replace_frame = DeepReplaceFrame(self.notebook, deep_replace_controller)
        deep_replace_controller.frame = deep_replace_frame
        self.notebook.add(deep_replace_frame, text='深度替换')

        # 兼容性处理工具
        # compatibility_controller = CompatibilityController(None, self.compatibility_processor)
        # compatibility_frame = CompatibilityFrame(self.notebook, compatibility_controller)
        # compatibility_controller.frame = compatibility_frame
        # self.notebook.add(compatibility_frame, text='兼容性处理')



    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ExcelUpdaterApp()
    app.run()