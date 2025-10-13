import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class BaseFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.button_style = {
            'bg': '#4a90e2',
            'fg': 'white',
            'font': ('Arial', 10),
            'relief': 'raised',
            'padx': 20
        }
        self.label_style = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'font': ('Arial', 10)
        }

class UpdaterFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 文件选择按钮
        btn_master = tk.Button(self, text="选择 Master 总表", **self.button_style, command=self.controller.select_master_file)
        btn_master.pack(pady=10)
        self.master_label = tk.Label(self, text="未选择文件", **self.label_style)
        self.master_label.pack()

        btn_folder = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # 匹配列选择
        match_frame = tk.Frame(self, bg='#f0f0f0')
        match_frame.pack(pady=10)
        tk.Label(match_frame, text="原文列：", **self.label_style).pack(side=tk.LEFT)
        self.match_column_var = tk.StringVar(value="2")
        match_dropdown = tk.OptionMenu(match_frame, self.match_column_var, *["2", "3"])
        match_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        match_dropdown["menu"].config(bg='white', fg='#333333')
        match_dropdown.pack(side=tk.LEFT)
        tk.Label(match_frame, text="列（小表）", **self.label_style).pack(side=tk.LEFT)

        # 内容列选择
        content_frame = tk.Frame(self, bg='#f0f0f0')
        content_frame.pack(pady=10)
        tk.Label(content_frame, text="内容列：", **self.label_style).pack(side=tk.LEFT)
        self.content_column_var = tk.StringVar(value="4")
        content_dropdown = tk.OptionMenu(content_frame, self.content_column_var, *["4","5","6","7","8","9","10","11"])
        content_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        content_dropdown["menu"].config(bg='white', fg='#333333')
        content_dropdown.pack(side=tk.LEFT)
        tk.Label(content_frame, text="列（Master表）", **self.label_style).pack(side=tk.LEFT)

        # 更新列选择
        update_frame = tk.Frame(self, bg='#f0f0f0')
        update_frame.pack(pady=10)
        tk.Label(update_frame, text="更新列：", **self.label_style).pack(side=tk.LEFT)
        self.update_column_var = tk.StringVar(value="3")
        update_dropdown = tk.OptionMenu(update_frame, self.update_column_var, *["3", "4"])
        update_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        update_dropdown["menu"].config(bg='white', fg='#333333')
        update_dropdown.pack(side=tk.LEFT)
        tk.Label(update_frame, text="列（小表）", **self.label_style).pack(side=tk.LEFT)

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=10)

class ClearerFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 文件夹选择按钮
        btn_folder = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_clearer_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # 列号输入框
        column_frame = tk.Frame(self, bg='#f0f0f0')
        column_frame.pack(pady=10)
        tk.Label(column_frame, text="列号：", **self.label_style).pack(side=tk.LEFT)
        self.column_var = tk.StringVar(value="")
        column_entry = tk.Entry(column_frame, textvariable=self.column_var, width=5)
        column_entry.pack(side=tk.LEFT)
        tk.Label(column_frame, text="列", **self.label_style).pack(side=tk.LEFT)

        # 功能按钮
        btn_clear = tk.Button(self, text="清空列", **self.button_style, command=self.controller.clear_column)
        btn_clear.pack(pady=5)
        
        btn_insert = tk.Button(self, text="插入列", **self.button_style, command=self.controller.insert_column)
        btn_insert.pack(pady=5)
        
        btn_delete = tk.Button(self, text="删除列", **self.button_style, command=self.controller.delete_column)
        btn_delete.pack(pady=5)

class CompatibilityFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 文件夹选择按钮
        btn_folder = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_compatibility_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_compatibility)
        btn_start.pack(pady=10)

class DeepReplaceFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 源文件夹选择按钮
        btn_source = tk.Button(self, text="选择源文件夹", **self.button_style, command=self.controller.select_source_folder)
        btn_source.pack(pady=10)
        self.source_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.source_label.pack()

        # 目标文件夹选择按钮
        btn_target = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_target.pack(pady=10)
        self.target_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.target_label.pack()

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=10)

class MultiColumnFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 文件选择按钮
        btn_master = tk.Button(self, text="选择 Master 总表", **self.button_style, command=self.controller.select_multi_master_file)
        btn_master.pack(pady=10)
        self.master_label = tk.Label(self, text="未选择文件", **self.label_style)
        self.master_label.pack()

        btn_folder = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_multi_target_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # 匹配列选择
        match_frame = tk.Frame(self, bg='#f0f0f0')
        match_frame.pack(pady=10)
        tk.Label(match_frame, text="原文列：", **self.label_style).pack(side=tk.LEFT)
        self.match_column_var = tk.StringVar(value="3")
        match_dropdown = tk.OptionMenu(match_frame, self.match_column_var, *["4", "3"])
        match_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        match_dropdown["menu"].config(bg='white', fg='#333333')
        match_dropdown.pack(side=tk.LEFT)
        tk.Label(match_frame, text="列（目标文件）", **self.label_style).pack(side=tk.LEFT)

        # 开始内容列选择
        start_frame = tk.Frame(self, bg='#f0f0f0')
        start_frame.pack(pady=10)
        tk.Label(start_frame, text="开始内容列：", **self.label_style).pack(side=tk.LEFT)
        self.start_column_var = tk.StringVar(value="5")
        start_dropdown = tk.OptionMenu(start_frame, self.start_column_var, *["4","5"])
        start_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        start_dropdown["menu"].config(bg='white', fg='#333333')
        start_dropdown.pack(side=tk.LEFT)
        tk.Label(start_frame, text="列（Master表）", **self.label_style).pack(side=tk.LEFT)

        # 更新开始列选择
        update_frame = tk.Frame(self, bg='#f0f0f0')
        update_frame.pack(pady=10)
        tk.Label(update_frame, text="更新开始列：", **self.label_style).pack(side=tk.LEFT)
        self.update_start_column_var = tk.StringVar(value="5")
        update_dropdown = tk.OptionMenu(update_frame, self.update_start_column_var, *["4","5","6","7","8","9","10","11"])
        update_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        update_dropdown["menu"].config(bg='white', fg='#333333')
        update_dropdown.pack(side=tk.LEFT)
        tk.Label(update_frame, text="列（目标文件）", **self.label_style).pack(side=tk.LEFT)
        
        # 列数选择
        count_frame = tk.Frame(self, bg='#f0f0f0')
        count_frame.pack(pady=10)
        tk.Label(count_frame, text="更新列数：", **self.label_style).pack(side=tk.LEFT)
        self.column_count_var = tk.StringVar(value="7")
        count_dropdown = tk.OptionMenu(count_frame, self.column_count_var, *["8", "7", "1"])
        count_dropdown.config(bg='#4a90e2', fg='white', font=('Arial', 10), width=5)
        count_dropdown["menu"].config(bg='white', fg='#333333')
        count_dropdown.pack(side=tk.LEFT)
        tk.Label(count_frame, text="列", **self.label_style).pack(side=tk.LEFT)

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_multi_column)
        btn_start.pack(pady=10)

class ReverseUpdaterFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # Master 文件选择
        btn_master = tk.Button(self, text="选择 Master 总表", **self.button_style, command=self.controller.select_master_file)
        btn_master.pack(pady=5)
        self.master_label = tk.Label(self, text="未选择文件", **self.label_style)
        self.master_label.pack()

        # 目标文件夹选择
        btn_folder = tk.Button(self, text="选择目标文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_folder.pack(pady=5)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # --- 小表列配置 ---
        target_frame = ttk.LabelFrame(self, text="小表（源）列配置", padding=(10, 5))
        target_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(target_frame, text="Key 列:").grid(row=0, column=0, sticky="w")
        self.target_key_col_var = tk.StringVar(value="1")
        tk.Entry(target_frame, textvariable=self.target_key_col_var, width=5).grid(row=0, column=1)

        tk.Label(target_frame, text="原文列:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.target_match_col_var = tk.StringVar(value="2")
        tk.Entry(target_frame, textvariable=self.target_match_col_var, width=5).grid(row=0, column=3)

        tk.Label(target_frame, text="译文列:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.target_content_col_var = tk.StringVar(value="3")
        tk.Entry(target_frame, textvariable=self.target_content_col_var, width=5).grid(row=0, column=5)

        # --- Master 表列配置 ---
        master_config_frame = ttk.LabelFrame(self, text="Master 表（目标）列配置", padding=(10, 5))
        master_config_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(master_config_frame, text="Key 列:").grid(row=0, column=0, sticky="w")
        self.master_key_col_var = tk.StringVar(value="2")
        tk.Entry(master_config_frame, textvariable=self.master_key_col_var, width=5).grid(row=0, column=1)

        tk.Label(master_config_frame, text="原文列:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.master_match_col_var = tk.StringVar(value="3")
        tk.Entry(master_config_frame, textvariable=self.master_match_col_var, width=5).grid(row=0, column=3)

        tk.Label(master_config_frame, text="译文列:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.master_update_col_var = tk.StringVar(value="4")
        tk.Entry(master_config_frame, textvariable=self.master_update_col_var, width=5).grid(row=0, column=5)

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=20)