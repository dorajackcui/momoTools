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
            match_column = int(self.frame.match_column_var.get()) - 1
            content_column = int(self.frame.content_column_var.get()) - 1
            update_column = int(self.frame.update_column_var.get()) - 1
            if match_column < 0 or content_column < 0 or update_column < 0:
                raise ValueError("列索引必须大于0")
            self.processor.set_match_column(match_column)
            self.processor.set_content_column(content_column)
            self.processor.set_update_column(update_column)
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
            match_column = int(self.frame.match_column_var.get()) - 1
            start_column = int(self.frame.start_column_var.get()) - 1
            update_start_column = int(self.frame.update_start_column_var.get()) - 1
            column_count = int(self.frame.column_count_var.get())
            
            if match_column < 0 or start_column < 0 or update_start_column < 0 or column_count <= 0:
                raise ValueError("列索引必须大于0，列数必须大于0")
                
            self.processor.set_match_column(match_column)
            self.processor.set_start_column(start_column)
            self.processor.set_update_start_column(update_start_column)
            self.processor.set_column_count(column_count)
            
            updated_count = self.processor.process_files()
            messagebox.showinfo("完成", f"共更新 {updated_count} 处数据。")
        except Exception as e:
            messagebox.showerror("错误", str(e))