import os
import pandas as pd
from openpyxl import load_workbook
import shutil

class DeepReplaceProcessor:
    def __init__(self, log_callback=None):
        self.source_folder = ""  # 源文件夹A（包含要用于替换的文件）
        self.target_folder = ""  # 目标文件夹B（需要被替换的文件所在的文件夹）
        self.log_callback = log_callback or (lambda msg: None)
        self.processed_files = 0

    def set_source_folder(self, folder_path):
        """设置源文件夹路径"""
        self.source_folder = folder_path

    def set_target_folder(self, folder_path):
        """设置目标文件夹路径"""
        self.target_folder = folder_path

    def log(self, message):
        """输出日志信息"""
        self.log_callback(message)

    def find_file_in_directory(self, filename, search_path):
        """递归搜索目标文件夹中的同名文件
        Args:
            filename: 要搜索的文件名
            search_path: 搜索的起始路径
        Returns:
            找到的文件的完整路径，如果未找到则返回None
        """
        for root, _, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def process_files(self):
        """处理文件替换
        Returns:
            替换的文件数量
        """
        if not self.source_folder or not self.target_folder:
            raise ValueError("请先选择源文件夹和目标文件夹！")

        if not os.path.exists(self.source_folder) or not os.path.exists(self.target_folder):
            raise ValueError("源文件夹或目标文件夹不存在！")

        self.processed_files = 0
        source_files = []
        
        # 递归遍历源文件夹中的所有 Excel 文件
        for root, _, files in os.walk(self.source_folder):
            for file in files:
                if file.endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                    source_files.append((file, os.path.join(root, file)))

        for source_file, source_path in source_files:
            self.log(f"正在处理文件：{source_file}")
            target_file_path = self.find_file_in_directory(source_file, self.target_folder)
            
            if target_file_path:
                try:
                    # 创建备份文件
                    backup_path = target_file_path + '.bak'
                    shutil.copy2(target_file_path, backup_path)
                    
                    # 复制新文件
                    shutil.copy2(source_path, target_file_path)
                    
                    self.processed_files += 1
                    self.log(f"成功替换文件：{target_file_path}")
                    
                    # 删除备份文件
                    os.remove(backup_path)
                except Exception as e:
                    self.log(f"替换文件 {source_file} 时发生错误：{str(e)}")
                    # 如果发生错误，尝试恢复备份
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, target_file_path)
                        os.remove(backup_path)
            else:
                self.log(f"未找到匹配的目标文件：{source_file}")

        return self.processed_files