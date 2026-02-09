import pandas as pd
import os
import openpyxl
import re
from collections import defaultdict

class UntranslatedStatsProcessor:
    def __init__(self, log_callback=None):
        self.target_folder = ""
        self.source_text_col = 1  # 默认第2列（0索引）
        self.translation_col = 2  # 默认第3列（0索引）
        self.stats_mode = "chinese_chars"  # 默认中文字符模式
        self.stats_results = []
        self.log_callback = log_callback

    def set_target_folder(self, folder_path):
        """设置目标文件夹"""
        self.target_folder = folder_path

    def set_columns(self, source_col, translation_col):
        """设置原文和译文列索引"""
        self.source_text_col = source_col
        self.translation_col = translation_col

    def set_stats_mode(self, mode):
        """设置统计模式"""
        self.stats_mode = mode

    def log(self, message):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def count_characters(self, text):
        """
        根据统计模式计算文本字数/词数
        """
        if not text or pd.isna(text):
            return 0
        
        # 转换为字符串并去除前后空格
        text = str(text).strip()
        if not text:
            return 0
        
        if self.stats_mode == "chinese_chars":
            # 中文字符模式：只统计中文字符
            chinese_characters = re.findall(r'[\u4e00-\u9fa5]', text)
            return len(chinese_characters)
        elif self.stats_mode == "english_words":
            # 英文词模式：统计英文单词数
            # 改良的正则表达式，支持撇号和连字符
            english_words = re.findall(r'\b[a-zA-Z]+(?:[\'\-][a-zA-Z]+)*\b', text)
            return len(english_words)
        else:
            return 0

    def is_translation_empty(self, translation):
        """
        判断译文是否为空
        """
        if pd.isna(translation) or translation is None:
            return True
        
        # 转换为字符串并去除空格
        translation_str = str(translation).strip()
        return translation_str == '' or translation_str.lower() == 'nan'

    def process_single_file(self, file_path):
        """
        处理单个Excel文件，统计未翻译字数
        返回: (文件名, 未翻译字数, 未翻译行数)
        """
        try:
            # 使用openpyxl读取文件
            wb = openpyxl.load_workbook(filename=file_path, read_only=True, data_only=True)
            ws = wb.active
            
            untranslated_chars = 0
            untranslated_rows = 0
            total_chars = 0
            total_rows = 0
            
            # 遍历所有行
            for row_idx, row in enumerate(ws.rows, start=1):
                try:
                    # 跳过第一行（表头）
                    if row_idx == 1:
                        continue
                        
                    # 确保行有足够的列
                    if len(row) <= max(self.source_text_col, self.translation_col):
                        continue
                    
                    # 获取原文和译文单元格
                    source_cell = row[self.source_text_col]
                    translation_cell = row[self.translation_col]
                    
                    source_text = source_cell.value if source_cell else None
                    translation_text = translation_cell.value if translation_cell else None
                    
                    # 跳过原文为空的行
                    if not source_text or pd.isna(source_text) or str(source_text).strip() == '':
                        continue

                    # 统计总字数和总行数
                    total_rows += 1
                    total_chars += self.count_characters(source_text)
                    
                    # 检查译文是否为空
                    if self.is_translation_empty(translation_text):
                        # 统计原文字数
                        char_count = self.count_characters(source_text)
                        untranslated_chars += char_count
                        untranslated_rows += 1
                        
                except Exception as e:
                    # 跳过有问题的行
                    continue
            
            wb.close()
            
            # 获取文件名（不包含路径）
            file_name = os.path.basename(file_path)
            
            return file_name, untranslated_chars, untranslated_rows, total_chars, total_rows
            
        except Exception as e:
            self.log(f"处理文件 {os.path.basename(file_path)} 时出错：{str(e)}")
            return os.path.basename(file_path), 0, 0, 0, 0

    def collect_excel_files(self):
        """
        收集目标文件夹中的所有Excel文件
        """
        if not self.target_folder or not os.path.exists(self.target_folder):
            raise ValueError("目标文件夹不存在或未设置！")
        
        file_paths = []
        for root, _, files in os.walk(self.target_folder):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                    file_paths.append(os.path.join(root, file))
        
        return file_paths

    def process_files(self):
        """
        处理所有Excel文件，统计未翻译字数
        返回统计结果列表
        """
        if not self.target_folder:
            raise ValueError("请先选择目标文件夹！")

        self.log("开始统计未翻译字数...")
        
        # 收集所有Excel文件
        file_paths = self.collect_excel_files()
        self.log(f"找到 {len(file_paths)} 个Excel文件")
        
        if not file_paths:
            self.log("未找到任何Excel文件")
            return []
        
        # 处理每个文件
        self.stats_results = []
        total_untranslated_chars = 0
        total_untranslated_rows = 0
        
        for i, file_path in enumerate(file_paths, 1):
            self.log(f"正在处理文件 ({i}/{len(file_paths)}): {os.path.basename(file_path)}")
            
            file_name, untranslated_chars, untranslated_rows, total_chars, total_rows = self.process_single_file(file_path)
            
            # 添加到结果列表
            self.stats_results.append({
                'file_name': file_name,
                'untranslated_chars': untranslated_chars,
                'untranslated_rows': untranslated_rows,
                'total_chars': total_chars,
                'total_rows': total_rows
            })
            
            total_untranslated_chars += untranslated_chars
            total_untranslated_rows += untranslated_rows
        
        self.log(f"统计完成！")
        if self.stats_mode == "chinese_chars":
            self.log(f"总计：{total_untranslated_chars} 个未翻译字符，{total_untranslated_rows} 行未翻译内容")
        elif self.stats_mode == "english_words":
            self.log(f"总计：{total_untranslated_chars} 个未翻译词，{total_untranslated_rows} 行未翻译内容")
        else:
            self.log(f"总计：{total_untranslated_chars} 个未翻译字符，{total_untranslated_rows} 行未翻译内容")
        
        return self.stats_results

    def export_to_excel(self, output_path):
        """
        将统计结果导出到Excel文件
        """
        if not self.stats_results:
            raise ValueError("没有统计结果可导出，请先运行统计功能！")
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(self.stats_results)
            
            # 根据统计模式设置列标题
            if self.stats_mode == "chinese_chars":
                df.columns = ['文件名', '未翻译字数', '未翻译行数', '总字数', '总行数']
                untranslated_col_name = '未翻译字数'
                total_col_name = '总字数'
            elif self.stats_mode == "english_words":
                df.columns = ['文件名', '未翻译词数', '未翻译行数', '总词数', '总行数']
                untranslated_col_name = '未翻译词数'
                total_col_name = '总词数'
            else:
                df.columns = ['文件名', '未翻译字数', '未翻译行数', '总字数', '总行数']
                untranslated_col_name = '未翻译字数'
                total_col_name = '总字数'
            
            # 添加汇总行
            total_untranslated_chars = df[untranslated_col_name].sum()
            total_untranslated_rows = df['未翻译行数'].sum()
            total_chars = df[total_col_name].sum()
            total_rows = df['总行数'].sum()
            
            # 创建汇总行
            summary_row = pd.DataFrame({
                '文件名': ['总计'],
                untranslated_col_name: [total_untranslated_chars],
                '未翻译行数': [total_untranslated_rows],
                total_col_name: [total_chars],
                '总行数': [total_rows]
            })
            
            # 合并数据和汇总行
            df_with_summary = pd.concat([df, summary_row], ignore_index=True)
            
            # 导出到Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_with_summary.to_excel(writer, sheet_name='未翻译统计', index=False)
                
                # 获取工作表并设置格式
                worksheet = writer.sheets['未翻译统计']
                
                # 设置列宽
                worksheet.column_dimensions['A'].width = 30  # 文件名列
                worksheet.column_dimensions['B'].width = 15  # 未翻译字数/词数列
                worksheet.column_dimensions['C'].width = 15  # 未翻译行数列
                worksheet.column_dimensions['D'].width = 15  # 总字数/词数列
                worksheet.column_dimensions['E'].width = 15  # 总行数列
                
                # 设置汇总行的样式（加粗）
                from openpyxl.styles import Font
                summary_row_idx = len(df) + 2  # +2 因为有表头和从1开始计数
                for col in ['A', 'B', 'C', 'D', 'E']:
                    cell = worksheet[f'{col}{summary_row_idx}']
                    cell.font = Font(bold=True)
            
            self.log(f"统计结果已导出到：{output_path}")
            return True
            
        except Exception as e:
            self.log(f"导出Excel文件失败：{str(e)}")
            return False

    def get_summary(self):
        """
        获取统计摘要信息
        """
        if not self.stats_results:
            return "暂无统计结果"
        
        total_files = len(self.stats_results)
        total_chars = sum(result['untranslated_chars'] for result in self.stats_results)
        total_rows = sum(result['untranslated_rows'] for result in self.stats_results)
        
        if self.stats_mode == "chinese_chars":
            return f"共处理 {total_files} 个文件，未翻译字数：{total_chars}，未翻译行数：{total_rows}"
        elif self.stats_mode == "english_words":
            return f"共处理 {total_files} 个文件，未翻译词数：{total_chars}，未翻译行数：{total_rows}"
        else:
            return f"共处理 {total_files} 个文件，未翻译字数：{total_chars}，未翻译行数：{total_rows}"