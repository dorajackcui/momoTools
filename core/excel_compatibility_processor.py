import os
from win32com.client import Dispatch

class ExcelCompatibilityProcessor:
    def __init__(self):
        self.folder_path = ""

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def process_files(self):
        if not self.folder_path:
            raise ValueError("请先设置有效的文件夹路径")

        processed_files = 0
        excel_app = None

        try:
            # 创建Excel应用实例
            excel_app = Dispatch('Excel.Application')
            excel_app.Visible = False
            excel_app.DisplayAlerts = False

            # 遍历目标文件夹中的所有Excel文件
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        try:
                            # 使用COM接口打开工作簿
                            wb = excel_app.Workbooks.Open(file_path)
                            if wb is not None:
                                # 保存并关闭工作簿
                                wb.Save()
                                wb.Close()
                                wb = None  # 显式释放工作簿对象
                                processed_files += 1

                        except Exception as e:
                            print(f"处理文件 {file} 时出错：{str(e)}")
                            if 'wb' in locals():
                                try:
                                    wb.Close(False)
                                except:
                                    pass
                            continue

        finally:
            # 确保Excel实例被正确关闭
            if excel_app is not None:
                try:
                    excel_app.Quit()
                except:
                    pass

        return processed_files