# TM_Builder 输入/输出格式要求（基于当前代码）

本文总结项目中对 Excel 读入/输出格式的严格要求与默认列约定，来源于 `core/` 里的处理器实现。

**通用规则**
- 仅处理 Excel 文件：扩展名为 `.xlsx` 或 `.xls`。
- 默认只处理“活动工作表”（`wb.active`），不会遍历多个 sheet。
- 绝大多数处理依赖 `key + match` 的组合键，组合方式为 `f"{key}|{match}"`，两者都会 `strip()` 去前后空格。
- `key` 或 `match` 为空时，该行会被跳过。
- 多数读入将数据当作字符串处理（`dtype=str` 或显式 `str()`）。
- 列索引默认是 **0-based**（第 1 列索引=0），除非特别说明。
- 文件夹扫描是递归的，包含子目录。

**UI 入口统一说明（Master -> 小表）**
- UI 仅保留一个入口：`Master到小表`。
- `更新列数 = 1` 时：按单列处理（`ExcelProcessor`）。
- `更新列数 > 1` 时：按多列处理（`MultiColumnExcelProcessor`）。
- 统一字段模型为“更新开始列 + 更新列数”；默认列使用单列默认值。

**模式一：Master → 小表（单列更新）**
- 代码位置：`core/excel_processor.py`
- 目标：用 Master 表的“默认译文列”去更新目标小表的“译文列”。
- Master 表列默认（0-based）：
  - `key` 列：1
  - `match`（原文）列：2
  - `content`（默认译文）列：3
- 目标小表列默认（0-based）：
  - `key` 列：0
  - `match`（原文）列：1
  - `update`（译文）列：2
- 读取 Master 时只读指定列，且 `keep_default_na=False`，空字符串不会被转成 NA。
- 读取/更新小表：
  - 读取时使用 `openpyxl` 只读模式，遍历所有行（不跳过表头）。
  - 写入时用 `openpyxl` 普通模式，写回同一个文件。
  - 写入列索引为 `target_update_col + 1`（openpyxl 写入是 1-based）。
  - 写入模式支持“覆盖/填空”：
    - 覆盖（默认）：命中后直接写入译文列（保持历史行为）。
    - 填空：仅当目标译文列为空时写入。
  - 后处理（Excel COM 打开并保存）为可选项，默认开启，可在 UI 里关闭。
  - 关闭后处理仅跳过兼容性保存步骤，不影响前置填表写入逻辑。

**模式二：Master → 小表（多列更新）**
- 代码位置：`core/multi_column_processor.py`
- 目标：从 Master 读取多个内容列，按 `key+match` 批量更新小表多个目标列。
- Master 表默认列（0-based）：
  - `key` 列：1
  - `match` 列：2
  - 内容起始列：4（从第 5 列开始）
  - 更新列数：7
- 目标小表默认列（0-based）：
  - `key` 列：1（第 2 列）
  - `match` 列：2（第 3 列）
  - 更新起始列：4（第 5 列）
- 读取 Master 时会动态计算 `usecols`，若失败会读取全部列。
- 小表更新列索引 = `update_start_column_index + i + 1`（openpyxl 写入 1-based）。
- 同样遍历所有行（不跳过表头）。
- 写入模式支持“覆盖/填空”：
  - 覆盖（默认）：命中后按配置列批量写入。
  - 填空：按单元格判断，仅空白目标单元格写入，非空保持不变。
- 后处理（Excel COM 打开并保存）为可选项，默认开启，可在 UI 里关闭。
- 关闭后处理仅跳过兼容性保存步骤，不影响前置填表写入逻辑。

**模式三：小表 → Master（反向更新）**
- 代码位置：`core/reverse_excel_processor.py`
- 目标：从小表读取译文，回填 Master。
- 小表默认列（0-based）：
  - `key` 列：0
  - `match` 列：1
  - `content`（译文）列：2
- Master 默认列（0-based）：
  - `key` 列：1
  - `match` 列：2
  - `update`（要写入）列：3
- 小表读取从第 2 行开始（`min_row=2`），默认跳过表头。
- Master 更新遍历所有行（不跳过表头）。
- 写入模式支持“覆盖/填空”：
  - 覆盖（默认）：命中后直接覆盖 Master 译文列。
  - 填空：仅当 Master 译文列为空时才写入。

**未翻译统计（读入+输出）**
- 代码位置：`core/untranslated_stats_processor.py`
- 读入要求：
  - 仅统计活动工作表。
  - 默认跳过第一行（认为是表头）。
  - 默认列（0-based）：原文列=1，译文列=2。
  - 原文为空时整行跳过。
- 输出要求：
  - 导出为 Excel（`openpyxl`），sheet 名称为 `未翻译统计`。
  - 列标题会根据统计模式设置（中文字符/英文单词）。
  - 统计结果包含汇总行，并设置列宽。

**列清理/插入/删除（兼容性要求严格）**
- 代码位置：`core/excel_cleaner.py`
- 依赖 `win32com` 调用本机 Excel。
- `column_number` 是 Excel 的 **1-based** 列号（与 openpyxl 的 0-based 不同）。
- `clear_column_in_files`：清空指定列的内容（从第 2 行开始，保留表头）。
- `insert_column_in_files`：在指定列位置插入新列，并写入表头 `Translation`。
- `delete_column_in_files`：删除指定列。

**兼容性修复（强制用 Excel 重新保存）**
- 代码位置：`core/excel_compatibility_processor.py`
- 用 `win32com` 打开并保存所有 `.xlsx/.xls` 文件以确保兼容性。
- 需要本机安装 Excel。

**深度替换（文件级别）**
- 代码位置：`core/deep_replace_processor.py`
- 以文件名为匹配条件：
  - 源文件夹 A 的 Excel 文件会在目标文件夹 B 中寻找同名文件并替换。
  - 仅处理 `.xlsx/.xls`，并忽略以 `~$` 开头的临时文件。
- 会先生成 `.bak` 备份，成功后删除备份，失败时回滚。

**注意事项（容易踩坑）**
- 表头行是否会被处理因模式不同：
  - `excel_processor` / `multi_column_processor` 默认不跳过表头。
  - `reverse_excel_processor` / `untranslated_stats_processor` 默认跳过表头。
- 目标文件夹中若存在临时文件（`~$`）会在部分功能被忽略，但在部分功能仍会被处理。
- 如果列索引配置错误，可能出现“列越界”导致行被跳过或更新失败。

如需把这些默认列配置同步到 UI 或配置文件，请告诉我当前 UI 的列设置入口位置。
