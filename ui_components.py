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

        btn_folder = tk.Button(self, text="选择小表文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # --- 小表列配置 ---
        target_frame = ttk.LabelFrame(self, text="小表列配置", padding=(10, 5))
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
        master_config_frame = ttk.LabelFrame(self, text="Master表列配置", padding=(10, 5))
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
        btn_start = tk.Button(self, text="填充小表", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=20)

class UntranslatedStatsFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        # 文件夹选择按钮
        btn_folder = tk.Button(self, text="选择小表文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # --- 列配置 ---
        column_frame = ttk.LabelFrame(self, text="列配置", padding=(10, 5))
        column_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(column_frame, text="原文列:").grid(row=0, column=0, sticky="w")
        self.source_col_var = tk.StringVar(value="2")
        tk.Entry(column_frame, textvariable=self.source_col_var, width=5).grid(row=0, column=1)

        tk.Label(column_frame, text="译文列:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.translation_col_var = tk.StringVar(value="3")
        tk.Entry(column_frame, textvariable=self.translation_col_var, width=5).grid(row=0, column=3)

        # --- 统计模式选择 ---
        mode_frame = ttk.LabelFrame(self, text="统计模式", padding=(10, 5))
        mode_frame.pack(pady=10, padx=10, fill="x")

        self.stats_mode_var = tk.StringVar(value="chinese_chars")
        
        tk.Radiobutton(mode_frame, text="中文字符模式", variable=self.stats_mode_var, 
                      value="chinese_chars").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(mode_frame, text="英文词模式", variable=self.stats_mode_var, 
                      value="english_words").grid(row=0, column=1, sticky="w", padx=(20, 0))

        # 输出文件选择
        output_frame = tk.Frame(self, bg='#f0f0f0')
        output_frame.pack(pady=10, fill="x", padx=10)
        
        btn_output = tk.Button(output_frame, text="选择输出文件", **self.button_style, command=self.controller.select_output_file)
        btn_output.pack(side=tk.LEFT)
        
        self.output_label = tk.Label(output_frame, text="未选择输出文件", **self.label_style)
        self.output_label.pack(side=tk.LEFT, padx=(10, 0))

        # 执行按钮
        btn_start = tk.Button(self, text="统计未翻译字数", **self.button_style, command=self.controller.process_stats)
        btn_start.pack(pady=20)

    def update_folder_label(self, folder_path):
        """更新文件夹标签"""
        if folder_path:
            self.folder_label.config(text=f"已选择: {os.path.basename(folder_path)}")
        else:
            self.folder_label.config(text="未选择文件夹")

    def update_output_label(self, output_path):
        """更新输出文件标签"""
        if output_path:
            self.output_label.config(text=f"输出: {os.path.basename(output_path)}")
        else:
            self.output_label.config(text="未选择输出文件")

    def get_column_config(self):
        """获取列配置和统计模式"""
        try:
            source_col = int(self.source_col_var.get()) - 1  # 转换为0索引
            translation_col = int(self.translation_col_var.get()) - 1  # 转换为0索引
            stats_mode = self.stats_mode_var.get()
            return source_col, translation_col, stats_mode
        except ValueError:
            messagebox.showerror("错误", "请输入有效的列号")
            return None, None, None

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
        btn_source = tk.Button(self, text="源文件夹（替换文件）", **self.button_style, command=self.controller.select_source_folder)
        btn_source.pack(pady=10)
        self.source_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.source_label.pack()

        # 目标文件夹选择按钮
        btn_target = tk.Button(self, text="目标文件夹（被替换文件）", **self.button_style, command=self.controller.select_target_folder)
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
        btn_master.pack(pady=10)
        self.master_label = tk.Label(self, text="未选择文件", **self.label_style)
        self.master_label.pack()

        # 目标文件夹选择
        btn_folder = tk.Button(self, text="选择小表文件夹", **self.button_style, command=self.controller.select_target_folder)
        btn_folder.pack(pady=10)
        self.folder_label = tk.Label(self, text="未选择文件夹", **self.label_style)
        self.folder_label.pack()

        # --- 小表列配置 ---
        target_frame = ttk.LabelFrame(self, text="小表列配置", padding=(10, 5))
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
        master_config_frame = ttk.LabelFrame(self, text="Master表列配置", padding=(10, 5))
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
        btn_start = tk.Button(self, text="填充master表", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=20)