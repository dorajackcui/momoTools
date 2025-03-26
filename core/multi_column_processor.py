import pandas as pd
import os
import concurrent.futures
import openpyxl
import time
from win32com.client import Dispatch

class MultiColumnExcelProcessor:
    def __init__(self, log_callback=None):
        self.master_file_path = ""
        self.target_folder = ""
        self.log_callback = log_callback or (lambda msg: None)
        self.match_column_index = 1  # 默认使用第二列作为匹配列
        self.start_column_index = 3  # 默认从第四列开始读取内容（来自master表）
        self.update_start_column_index = 2  # 默认从第三列开始更新（目标文件的列）
        self.column_count = 1  # 默认更新1列
        self.debug_keys = [
            "LDLG_Text_ZH_q101102_1_d1_cd_Line_14",
            "clothesdes_10208"
        ]

    def set_match_column(self, column_index):
        """设置用于匹配的列索引"""
        self.match_column_index = column_index
        
    def set_start_column(self, column_index):
        """设置开始内容列索引（master表中的起始列）"""
        self.start_column_index = column_index
        
    def set_update_start_column(self, column_index):
        """设置要开始更新的列索引（目标文件的起始列）"""
        self.update_start_column_index = column_index
        
    def set_column_count(self, count):
        """设置要更新的列数"""
        self.column_count = count

    def set_master_file(self, file_path):
        self.master_file_path = file_path

    def set_target_folder(self, folder_path):
        self.target_folder = folder_path

    def log(self, message):
        self.log_callback(message)

    def debug_key_info(self, master_dict, keys_to_check):
        """调试特定key的信息
        Args:
            master_dict: 主数据字典
            keys_to_check: 要检查的key列表
        """
        for key in keys_to_check:
            found = False
            # 由于使用combined key，需要查找所有以该key开头的组合键
            for combined_key, value in master_dict.items():
                if combined_key.startswith(f"{key}|"):
                    self.log(f"Debug - Key '{key}' 的组合键 '{combined_key}' 内容: {value}")
                    found = True
            if not found:
                self.log(f"Debug - 未找到Key: {key}")

    def process_files(self):
        if not self.master_file_path or not self.target_folder:
            raise ValueError("请先选择 Master 文件和目标文件夹！")

        # 记录开始时间
        start_time = time.time()

        try:
            self.log("正在读取 Master 文件...")
            master_start_time = time.time()
            
            # 计算需要读取的列，确保索引有效
            usecols = [1]  # 1是Key列(B列)
            
            # 确保匹配列索引有效
            match_col = max(1, self.match_column_index)  # 确保至少是第2列
            if match_col not in usecols:  # 避免重复添加
                usecols.append(match_col)
            
            # 添加所有需要的内容列，确保索引有效
            for i in range(self.column_count):
                content_col = max(2, self.start_column_index + i)  # 确保至少是第3列
                if content_col not in usecols:  # 避免重复添加
                    usecols.append(content_col)
            
            # 排序列索引，确保顺序一致
            usecols.sort()
            
            self.log(f"将读取以下列: {usecols}")
                
            # 读取Excel文件
            try:
                master_df = pd.read_excel(
                    self.master_file_path,
                    engine='openpyxl',
                    dtype={col: str for col in range(len(usecols))},  # 直接指定所有列为字符串类型
                    keep_default_na=False,
                    na_values=[],  # 只将空字符串视为NA
                    na_filter=False,  # 禁用NA过滤，保持原始值
                    usecols=usecols
                )
            except Exception as excel_err:
                # 尝试不指定usecols参数读取
                self.log(f"使用指定列读取失败，尝试读取所有列: {str(excel_err)}")
                master_df = pd.read_excel(
                    self.master_file_path,
                    engine='openpyxl',
                    dtype=str,  # 所有列都作为字符串
                    keep_default_na=False,
                    na_values=[],
                    na_filter=False
                )
                
            master_end_time = time.time()
            self.log(f"Master文件读取耗时: {master_end_time - master_start_time:.2f}秒")
            self.log(f"成功读取，共 {len(master_df)} 行数据")
        except Exception as e:
            raise Exception(f"读取 Master 文件失败：{e}")

        # 创建多列数据字典
        master_dict = {}
        master_data = master_df.values
        for row in master_data:
            try:
                # 确保行至少有一个元素
                if len(row) == 0:
                    continue
                    
                # 安全获取key值
                key = row[0].strip() if row[0] else ''
                if not key:  # 跳过空key
                    continue
                    
                # 安全获取匹配值
                match_val = ''
                if len(row) > 1:
                    match_val = str(row[1]) if row[1] else ''
                if not match_val:  # 跳过空匹配值
                    continue
                    
                # 使用key+匹配列内容作为combined key
                combined_key = f"{key}|{match_val}"
                
                # 存储多列内容
                content_values = []
                for i in range(self.column_count):
                    col_idx = 2 + i  # 从第三列开始是内容列
                    if col_idx < len(row):
                        content_values.append(str(row[col_idx]) if row[col_idx] else '')
                    else:
                        content_values.append('')  # 如果列不存在，添加空字符串
                
                master_dict[combined_key] = content_values
            except Exception as row_err:
                self.log(f"处理数据行时出错，跳过此行: {str(row_err)}")
                continue

        self.log(f"Master 中共找到 {len(master_dict)} 个有效 Key")
        # 添加调试日志，打印特定key的内容
        self.debug_key_info(master_dict, self.debug_keys)

        # 收集目标文件
        file_paths = []
        for root, _, files in os.walk(self.target_folder):
            file_paths.extend(
                os.path.join(root, file)
                for file in files
                if file.lower().endswith(('.xlsx', '.xls'))
            )

        self.log(f"找到 {len(file_paths)} 个目标文件")

        # 优化：调整线程池大小以获得更好的性能
        process_start_time = time.time()
        max_workers = min(32, len(file_paths))  # 限制最大线程数
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._process_single_file, fp, master_dict) for fp in file_paths]
            updated_count = sum(future.result() for future in concurrent.futures.as_completed(futures))
        process_end_time = time.time()

        self.log(f"文件处理耗时: {process_end_time - process_start_time:.2f}秒")
        self.log(f"处理完成，共更新 {updated_count} 处数据")

        # 添加后处理步骤
        self.log("开始后处理步骤...")
        self._post_process(file_paths)
        self.log("后处理步骤完成")

        total_time = time.time() - start_time
        self.log(f"总耗时: {total_time:.2f}秒")

        return updated_count

    def _process_single_file(self, file_path, master_dict):
        updates = {}
        updated = 0
        
        try:
            # 使用openpyxl的只读模式读取文件
            wb = openpyxl.load_workbook(filename=file_path, read_only=True)
            ws = wb.active
            
            # 获取目标列的索引
            key_col = 'B'  # 第2列
            match_col = chr(ord('B') + self.match_column_index)  # 匹配列
            for idx, row in enumerate(ws.rows, start=1):
                try:
                    # 安全获取单元格值
                    key_cell = None
                    match_cell = None
                    
                    # 确保索引有效，key在B列
                    if len(row) > 0:
                        key_cell = row[1]
                    
                    if len(row) > self.match_column_index:
                        match_cell = row[self.match_column_index]
                    else:
                        continue  # 跳过没有匹配列的行
                    
                    # 确保单元格值转换为字符串
                    target_key = str(key_cell.value).strip() if key_cell and key_cell.value else ''
                    target_match_value = str(match_cell.value) if match_cell and match_cell.value else ''

                    if not target_key or not target_match_value:
                        continue

                    # 创建与master_dict相同格式的combined key
                    combined_key = f"{target_key}|{target_match_value}"
                    
                    # 使用combined key进行查找
                    if combined_key in master_dict:
                        # 获取多列内容并更新
                        content_values = master_dict[combined_key]
                        for i, content_value in enumerate(content_values):
                            try:
                                update_col = self.update_start_column_index + i + 1  # +1是因为openpyxl的列索引从1开始
                                updates[(idx, update_col)] = content_value
                                updated += 1
                            except Exception as col_err:
                                self.log(f"更新第{idx}行第{update_col}列时出错: {str(col_err)}")
                                continue

                except Exception:
                    continue
            
            # 关闭只读工作簿
            wb.close()
            
            # 如果有更新，重新打开文件进行写入
            if updates:
                try:
                    wb = openpyxl.load_workbook(file_path)
                    ws = wb.active
                    
                    # 批量更新单元格
                    for (row, col), value in updates.items():
                        # 使用正确的方法获取和设置单元格值
                        cell = ws._get_cell(row, col)
                        if cell is None:
                            cell = ws._cell(row, col)
                        cell.value = value
                        
                    wb.save(file_path)
                except Exception:
                    return 0
                finally:
                    if wb:
                        wb.close()
                    
        except Exception as e:
            return 0
            
        return updated
        
    def _post_process(self, file_paths):
        """使用win32com.client处理Excel文件以确保兼容性，采用最简单的单线程处理方式"""
        try:
            post_process_start_time = time.time()
            total_files = len(file_paths)
            
            # 创建一个Excel实例供所有文件使用
            excel_app = Dispatch('Excel.Application')
            excel_app.Visible = False
            excel_app.DisplayAlerts = False
            
            try:
                # 简单循环处理每个文件
                for index, file_path in enumerate(file_paths, 1):
                    print(f"\r正在后处理文件 ({index}/{total_files}): {os.path.basename(file_path)}", end="")
                    self._process_single_file_post(file_path, excel_app)

            finally:
                # 确保Excel实例被正确关闭和释放
                if excel_app is not None:
                    try:
                        excel_app.Quit()
                    except:
                        pass
                    excel_app = None
            
            post_process_end_time = time.time()
            self.log(f"后处理步骤耗时: {post_process_end_time - post_process_start_time:.2f}秒")
                    
        except Exception as e:
            self.log(f"后处理步骤失败：{str(e)}")
    
    def _process_single_file_post(self, file_path, excel_app):
        """处理单个文件的后处理逻辑，使用共享的Excel实例"""
        try:
            # 打开工作簿
            wb = excel_app.Workbooks.Open(file_path)
            if wb is not None:
                wb.Save()
                wb.Close(True)
                wb = None  # 显式释放工作簿对象
        except Exception as e:
            self.log(f"后处理文件 {os.path.basename(file_path)} 时出错：{str(e)}")