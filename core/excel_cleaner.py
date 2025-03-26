import os
import win32com.client

class ExcelColumnClearer:
    def __init__(self):
        self.folder_path = ""
        self.column_number = 0
        self.excel = None

    def set_folder_path(self, path):
        self.folder_path = path

    def set_column_number(self, number):
        self.column_number = number

    def _init_excel(self):
        if not self.excel:
            self.excel = win32com.client.Dispatch("Excel.Application")
            self.excel.Visible = False
            self.excel.DisplayAlerts = False

    def _quit_excel(self):
        if self.excel:
            self.excel.Quit()
            self.excel = None

    def clear_column_in_files(self):
        processed_files = 0
        total_files = sum(1 for _, _, files in os.walk(self.folder_path) 
                         for file in files if file.endswith(('.xlsx', '.xls')))

        try:
            self._init_excel()
            
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        try:
                            processed_files += 1
                            print(f"正在处理: {file} ({processed_files}/{total_files})")
                            
                            wb = self.excel.Workbooks.Open(file_path)
                            ws = wb.ActiveSheet
                            
                            # 清空指定列的内容（跳过表头）
                            last_row = ws.UsedRange.Rows.Count
                            column = ws.Columns(self.column_number)
                            
                            # 获取列的范围（从第2行到最后一行）
                            clear_range = ws.Range(
                                ws.Cells(2, self.column_number),
                                ws.Cells(last_row, self.column_number)
                            )
                            
                            # 清空内容
                            clear_range.ClearContents()
                            
                            wb.Save()
                            wb.Close()

                        except Exception as e:
                            print(f"处理文件 {file} 时出错：{str(e)}")
                            continue
        finally:
            self._quit_excel()

        return processed_files

    def insert_column_in_files(self):
        processed_files = 0
        total_files = sum(1 for _, _, files in os.walk(self.folder_path) 
                         for file in files if file.endswith(('.xlsx', '.xls')))

        try:
            self._init_excel()
            
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        try:
                            processed_files += 1
                            print(f"\r正在处理: {file} ({processed_files}/{total_files})", end="")
                            
                            wb = self.excel.Workbooks.Open(file_path)
                            ws = wb.ActiveSheet
                            
                            # 在指定位置插入新列
                            column_range = ws.Columns(self.column_number)
                            column_range.Insert()
                            
                            # 设置新列的标题
                            ws.Cells(1, self.column_number).Value = 'Translation'
                            
                            wb.Save()
                            wb.Close()

                        except Exception as e:
                            print(f"处理文件 {file} 时出错：{str(e)}")
                            continue
        finally:
            self._quit_excel()

        return processed_files

    def delete_column_in_files(self):
        processed_files = 0
        total_files = sum(1 for _, _, files in os.walk(self.folder_path) 
                         for file in files if file.endswith(('.xlsx', '.xls')))

        try:
            self._init_excel()
            
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        try:
                            processed_files += 1
                            print(f"正在处理: {file} ({processed_files}/{total_files})")
                            
                            wb = self.excel.Workbooks.Open(file_path)
                            ws = wb.ActiveSheet
                            
                            # 删除指定列
                            column_range = ws.Columns(self.column_number)
                            column_range.Delete()
                            
                            wb.Save()
                            wb.Close()

                        except Exception as e:
                            print(f"处理文件 {file} 时出错：{str(e)}")
                            continue
        finally:
            self._quit_excel()

        return processed_files
