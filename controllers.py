from tkinter import filedialog, messagebox
import os

class BaseController:
    def __init__(self, frame):
        self.frame = frame

class UpdaterController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor
        self.master_file_path = ""
        self.target_folder = ""

    def select_master_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 Master 总表",
            filetypes=[("Excel 文件", "*.xlsx *.xls")]
        )
        if file_path:
            self.master_file_path = file_path
            self.frame.master_label.config(text=f"已选择：{os.path.basename(file_path)}")
            self.processor.set_master_file(file_path)

    def select_target_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.target_folder = folder_path
            self.frame.folder_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_target_folder(folder_path)

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            messagebox.showerror("错误", "请先选择 Master 文件和目标文件夹！")
            return

        try:
            # 获取小表列配置
            target_key_col = int(self.frame.target_key_col_var.get()) - 1
            target_match_col = int(self.frame.target_match_col_var.get()) - 1
            target_content_col = int(self.frame.target_content_col_var.get()) - 1

            # 获取 Master 表列配置
            master_key_col = int(self.frame.master_key_col_var.get()) - 1
            master_match_col = int(self.frame.master_match_col_var.get()) - 1
            master_update_col = int(self.frame.master_update_col_var.get()) - 1

            # 验证列索引
            if any(c < 0 for c in [target_key_col, target_match_col, target_content_col, 
                                     master_key_col, master_match_col, master_update_col]):
                raise ValueError("列索引必须大于0")

            self.processor.set_target_column(target_key_col, target_match_col, target_content_col)
            self.processor.set_master_column(master_key_col, master_match_col, master_update_col)
        except ValueError as e:
            messagebox.showerror("错误", f"匹配列设置错误：{str(e)}")
            return

        try:
            updated_count = self.processor.process_files()
            messagebox.showinfo("完成", f"共更新 {updated_count} 行。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

class ClearerController(BaseController):
    def __init__(self, frame, clearer):
        super().__init__(frame)
        self.clearer = clearer

    def select_clearer_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.frame.folder_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.clearer.set_folder_path(folder_path)

    def clear_column(self):
        try:
            column_number = int(self.frame.column_var.get())
            if column_number <= 0:
                raise ValueError("列号必须大于0")
            self.clearer.set_column_number(column_number)
            processed_files = self.clearer.clear_column_in_files()
            messagebox.showinfo("完成", f"共处理 {processed_files} 个文件。")
        except ValueError as e:
            messagebox.showerror("错误", f"列号设置错误：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def insert_column(self):
        try:
            column_number = int(self.frame.column_var.get())
            if column_number <= 0:
                raise ValueError("列号必须大于0")
            self.clearer.set_column_number(column_number)
            processed_files = self.clearer.insert_column_in_files()
            messagebox.showinfo("完成", f"共处理 {processed_files} 个文件。")
        except ValueError as e:
            messagebox.showerror("错误", f"列号设置错误：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_column(self):
        try:
            column_number = int(self.frame.column_var.get())
            if column_number <= 0:
                raise ValueError("列号必须大于0")
            self.clearer.set_column_number(column_number)

            confirm = messagebox.askyesno("确认操作", f"确定要删除所有Excel文件的第{column_number}列吗？\n此操作不可撤销！")
            if not confirm:
                return

            processed_files = self.clearer.delete_column_in_files()
            messagebox.showinfo("完成", f"共处理 {processed_files} 个文件。")
        except ValueError as e:
            messagebox.showerror("错误", f"列号设置错误：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

class CompatibilityController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor

    def select_compatibility_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.frame.folder_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_folder_path(folder_path)

    def process_compatibility(self):
        try:
            processed_files = self.processor.process_files()
            messagebox.showinfo("完成", f"共处理 {processed_files} 个文件。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

class DeepReplaceController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor
        self.source_folder = ""
        self.target_folder = ""

    def select_source_folder(self):
        folder_path = filedialog.askdirectory(title="选择源文件夹")
        if folder_path:
            self.source_folder = folder_path
            self.frame.source_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_source_folder(folder_path)

    def select_target_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.target_folder = folder_path
            self.frame.target_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_target_folder(folder_path)

    def process_files(self):
        if not self.source_folder or not self.target_folder:
            messagebox.showerror("错误", "请先选择源文件夹和目标文件夹！")
            return

        try:
            processed_files = self.processor.process_files()
            messagebox.showinfo("完成", f"共处理 {processed_files} 个文件。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

class MultiColumnController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor

    def select_multi_master_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 Master 总表",
            filetypes=[("Excel 文件", "*.xlsx *.xls")]
        )
        if file_path:
            self.frame.master_label.config(text=f"已选择：{os.path.basename(file_path)}")
            self.processor.set_master_file(file_path)

    def select_multi_target_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.frame.folder_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_target_folder(folder_path)

    def process_multi_column(self):
        try:
            # 获取目标文件列配置
            target_key_col = int(self.frame.target_key_col_var.get()) - 1
            target_match_col = int(self.frame.match_column_var.get()) - 1
            target_update_start_col = int(self.frame.update_start_column_var.get()) - 1
            
            # 获取Master文件列配置
            master_key_col = int(self.frame.master_key_col_var.get()) - 1
            master_match_col = int(self.frame.master_match_col_var.get()) - 1
            master_start_col = int(self.frame.start_column_var.get()) - 1
            
            # 获取处理参数
            column_count = int(self.frame.column_count_var.get())
            
            # 验证列索引
            if any(c < 0 for c in [target_key_col, target_match_col, target_update_start_col, 
                                   master_key_col, master_match_col, master_start_col]) or column_count <= 0:
                raise ValueError("列索引必须大于0，列数必须大于0")
            
            # 配置处理器
            self.processor.set_target_key_column(target_key_col)
            self.processor.set_match_column(target_match_col)
            self.processor.set_update_start_column(target_update_start_col)
            self.processor.set_master_key_column(master_key_col)
            self.processor.set_master_match_column(master_match_col)
            self.processor.set_start_column(master_start_col)
            self.processor.set_column_count(column_count)
            
            updated_count = self.processor.process_files()
            messagebox.showinfo("完成", f"共更新 {updated_count} 处数据。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

class ReverseUpdaterController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor
        self.master_file_path = ""
        self.target_folder = ""

    def select_master_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 Master 总表",
            filetypes=[("Excel 文件", "*.xlsx *.xls")]
        )
        if file_path:
            self.master_file_path = file_path
            self.frame.master_label.config(text=f"已选择：{os.path.basename(file_path)}")
            self.processor.set_master_file(file_path)

    def select_target_folder(self):
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.target_folder = folder_path
            self.frame.folder_label.config(text=f"已选择：{os.path.basename(folder_path)}")
            self.processor.set_target_folder(folder_path)

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            messagebox.showerror("错误", "请先选择 Master 文件和目标文件夹！")
            return

        try:
            # 获取小表列配置
            target_key_col = int(self.frame.target_key_col_var.get()) - 1
            target_match_col = int(self.frame.target_match_col_var.get()) - 1
            target_content_col = int(self.frame.target_content_col_var.get()) - 1

            # 获取 Master 表列配置
            master_key_col = int(self.frame.master_key_col_var.get()) - 1
            master_match_col = int(self.frame.master_match_col_var.get()) - 1
            master_update_col = int(self.frame.master_update_col_var.get()) - 1

            # 验证列索引
            if any(c < 0 for c in [target_key_col, target_match_col, target_content_col, 
                                     master_key_col, master_match_col, master_update_col]):
                raise ValueError("列索引必须大于0")

            # 配置处理器
            self.processor.set_target_columns(target_key_col, target_match_col, target_content_col)
            self.processor.set_master_columns(master_key_col, master_match_col, master_update_col)

        except ValueError as e:
            messagebox.showerror("错误", f"列配置错误：{str(e)}")
            return

        try:
            updated_count = self.processor.process_files()
            messagebox.showinfo("完成", f"共更新 {updated_count} 行。")
        except Exception as e:
            messagebox.showerror("处理失败", str(e))

class UntranslatedStatsController(BaseController):
    def __init__(self, frame, processor):
        super().__init__(frame)
        self.processor = processor
        self.target_folder = ""
        self.output_file = ""

    def select_target_folder(self):
        folder_path = filedialog.askdirectory(title="选择小表文件夹")
        if folder_path:
            self.target_folder = folder_path
            self.frame.update_folder_label(folder_path)
            self.processor.set_target_folder(folder_path)

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        if file_path:
            self.output_file = file_path
            self.frame.update_output_label(file_path)

    def process_stats(self):
        if not self.target_folder:
            messagebox.showerror("错误", "请先选择小表文件夹！")
            return

        if not self.output_file:
            messagebox.showerror("错误", "请先选择输出文件！")
            return

        # 获取列配置和统计模式
        source_col, translation_col, stats_mode = self.frame.get_column_config()
        if source_col is None or translation_col is None:
            return

        try:
            # 设置列配置和统计模式
            self.processor.set_columns(source_col, translation_col)
            self.processor.set_stats_mode(stats_mode)
            
            # 处理统计
            stats_results = self.processor.process_files()
            
            if not stats_results:
                messagebox.showwarning("警告", "未找到任何Excel文件或所有文件都没有未翻译内容")
                return
            
            # 导出结果
            self.processor.export_to_excel(self.output_file)
            
            messagebox.showinfo("完成", f"统计完成！\n共处理 {len(stats_results)} 个文件\n结果已保存到: {self.output_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"处理过程中发生错误：{str(e)}")