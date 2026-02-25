import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os


class ToggleSwitch(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        variable,
        on_color="#0078D4",
        off_color="#E5E5E5",
        bg="#f0f0f0",
        font=("Segoe UI", 9),
        command=None,
    ):
        super().__init__(parent, bg=bg)
        self.variable = variable
        self.on_color = on_color
        self.off_color = off_color
        self.track_border_on = "#0063B1"
        self.track_border_off = "#A6A6A6"
        self.knob_fill = "#FFFFFF"
        self.knob_border = "#9B9B9B"
        self.track_width = 40
        self.track_height = 20
        self.knob_padding = 2
        self.command = command

        self.canvas = tk.Canvas(
            self,
            width=self.track_width,
            height=self.track_height,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(side=tk.LEFT)

        self.label = tk.Label(self, text=text, bg=bg, fg="#333333", font=font)
        self.label.pack(side=tk.LEFT, padx=(8, 0))

        self.canvas.bind("<Button-1>", self._toggle)
        self.label.bind("<Button-1>", self._toggle)
        self.bind("<Button-1>", self._toggle)

        self._trace_id = self.variable.trace_add("write", self._on_var_changed)
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        w, h = self.track_width, self.track_height
        padding = self.knob_padding
        r = h // 2
        track_color = self.on_color if self.variable.get() else self.off_color
        border_color = self.track_border_on if self.variable.get() else self.track_border_off

        self.canvas.create_oval(
            0,
            0,
            h,
            h,
            fill=track_color,
            outline=border_color,
            width=1,
        )
        self.canvas.create_rectangle(
            r,
            0,
            w - r,
            h,
            fill=track_color,
            outline=border_color,
            width=1,
        )
        self.canvas.create_oval(
            w - h,
            0,
            w,
            h,
            fill=track_color,
            outline=border_color,
            width=1,
        )

        knob_size = h - padding * 2
        knob_x = (w - padding - knob_size) if self.variable.get() else padding
        self.canvas.create_oval(
            knob_x,
            padding,
            knob_x + knob_size,
            padding + knob_size,
            fill=self.knob_fill,
            outline=self.knob_border,
            width=1,
        )

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command is not None:
            self.command()

    def _on_var_changed(self, *_args):
        self._draw()

    def destroy(self):
        if hasattr(self, "_trace_id"):
            try:
                self.variable.trace_remove("write", self._trace_id)
            except Exception:
                pass
        super().destroy()


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

    def create_toggle(self, text, variable, pady=(0, 0), parent=None, command=None):
        toggle_parent = parent or self
        toggle = ToggleSwitch(
            toggle_parent,
            text=text,
            variable=variable,
            bg='#f0f0f0',
            font=('Arial', 10),
            command=command,
        )
        toggle.pack(anchor="w", padx=10, pady=pady)
        return toggle

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

        self.post_process_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="启用后处理（兼容性保存）",
            variable=self.post_process_var,
            pady=(5, 5),
        )

        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            pady=(0, 5),
        )


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

        # --- 目标文件列配置 ---
        target_frame = ttk.LabelFrame(self, text="目标文件列配置", padding=(10, 5))
        target_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(target_frame, text="Key 列:").grid(row=0, column=0, sticky="w")
        self.target_key_col_var = tk.StringVar(value="2")
        tk.Entry(target_frame, textvariable=self.target_key_col_var, width=5).grid(row=0, column=1)

        tk.Label(target_frame, text="原文列:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.match_column_var = tk.StringVar(value="3")
        tk.Entry(target_frame, textvariable=self.match_column_var, width=5).grid(row=0, column=3)

        tk.Label(target_frame, text="更新开始列:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.update_start_column_var = tk.StringVar(value="5")
        tk.Entry(target_frame, textvariable=self.update_start_column_var, width=5).grid(row=0, column=5)

        # --- Master 表列配置 ---
        master_config_frame = ttk.LabelFrame(self, text="Master表列配置", padding=(10, 5))
        master_config_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(master_config_frame, text="Key 列:").grid(row=0, column=0, sticky="w")
        self.master_key_col_var = tk.StringVar(value="2")
        tk.Entry(master_config_frame, textvariable=self.master_key_col_var, width=5).grid(row=0, column=1)

        tk.Label(master_config_frame, text="原文列:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.master_match_col_var = tk.StringVar(value="3")
        tk.Entry(master_config_frame, textvariable=self.master_match_col_var, width=5).grid(row=0, column=3)

        tk.Label(master_config_frame, text="内容开始列:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.start_column_var = tk.StringVar(value="5")
        tk.Entry(master_config_frame, textvariable=self.start_column_var, width=5).grid(row=0, column=5)

        # --- 处理参数配置 ---
        params_frame = ttk.LabelFrame(self, text="处理参数", padding=(10, 5))
        params_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(params_frame, text="更新列数:").grid(row=0, column=0, sticky="w")
        self.column_count_var = tk.StringVar(value="7")
        tk.Entry(params_frame, textvariable=self.column_count_var, width=5).grid(row=0, column=1)

        self.post_process_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="启用后处理（兼容性保存）",
            variable=self.post_process_var,
            pady=(5, 5),
        )

        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            pady=(0, 5),
        )

        # 执行按钮
        btn_start = tk.Button(self, text="开始处理", **self.button_style, command=self.controller.process_multi_column)
        btn_start.pack(pady=20)

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

        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="仅填空（关闭=覆盖）",
            variable=self.fill_blank_var,
            pady=(5, 5),
        )

        # 执行按钮
        btn_start = tk.Button(self, text="填充master表", **self.button_style, command=self.controller.process_files)
        btn_start.pack(pady=20)
