# TM_builder 输入/输出判定规范（当前实现）

更新时间：2026-02-28  
范围：只描述当前代码行为，不代表“理想行为”。

## 1. 适用场景

本文聚焦你关心的 3 个核心流程：

1. `Master -> 小表（单列）`：`core/excel_processor.py`
2. `Master -> 小表（多列）`：`core/multi_column_processor.py`
3. `小表 -> Master（反向）`：`core/reverse_excel_processor.py`

不覆盖 UI 展示细节，只覆盖读写判定与特殊值处理。

## 2. 判定基础（统一规则）

来源：`core/kernel/excel_io.py`

### 2.1 组合键构造

- 函数：`build_combined_key(key_value, match_value, separator='|')`
- 内部先对 `key_value` / `match_value` 调用 `safe_to_str(..., strip=True)`
- 规则：
  - `None -> ""`
  - 字符串会 `strip()`
  - 非字符串（如 `0`、`0.0`、`float('nan')`）会转成字符串后再判定
- 只要 `key` 或 `match` 任一最终为空字符串，就返回 `None`（该行跳过）

### 2.2 “空白单元格”判定（仅用于 fill_blank_only）

- 函数：`is_blank_value(value)`
- 仅以下两类算“空白”：
  - `value is None`
  - `value` 是字符串且 `value.strip() == ""`
- 这意味着：
  - `0` / `0.0` 不是空白
  - `float('nan')` 不是空白
  - 字符串 `"nan"` 不是空白

## 3. Master -> 小表（单列）

文件：`core/excel_processor.py`

### 3.1 读取 Master

- 使用 `pandas.read_excel(..., keep_default_na=False, na_filter=False, usecols=...)`
- 构建 `master_dict` 时：
  - 键：`build_combined_key(master_key, master_match)`
  - 值：`safe_to_str(master_content, strip=False)`
- 值列结果：
  - `None -> ""`
  - `0 -> "0"`
  - `float('nan') -> "nan"`（字符串）
  - `"  abc  "` 保留原空格（不 strip）

### 3.2 扫描小表并写回

- 逐行读取目标小表（active sheet）
- 用小表 `key+match` 构造组合键并匹配 `master_dict`
- 命中后写入更新列
- `fill_blank_only=True` 时，仅当当前单元格满足 `is_blank_value` 才写入

### 3.3 特殊值结论（单列）

1. 小表更新列当前值为 `None` / `""` / `"   "`：可写入（填空模式）
2. 小表更新列当前值为 `0` / `0.0` / `"nan"`：视为非空，不写入（填空模式）
3. 覆盖模式下（`fill_blank_only=False`）：始终写入

## 4. Master -> 小表（多列）

文件：`core/multi_column_processor.py`

### 4.1 读取 Master

- 逻辑与单列一致，区别是一次读取多列内容
- 每个内容值都走 `safe_to_str(..., strip=False)`
- 缺失列会补空字符串 `""`

### 4.2 写回小表

- 对每个命中的组合键，逐列更新目标区间
- 每个目标单元格独立做 `fill_blank_only` 判定（仍使用 `is_blank_value`）

### 4.3 特殊值结论（多列）

与单列完全一致，只是按列逐格执行。

## 5. 小表 -> Master（反向）

文件：`core/reverse_excel_processor.py`

### 5.1 读取小表

- 小表从第 2 行开始读取（`min_row=2`）
- 组合键规则仍为 `build_combined_key`
- 小表内容列写入内存前：`safe_to_str(content, strip=False)`
  - `None -> ""`
  - `0 -> "0"`
  - `float('nan') -> "nan"`

### 5.2 更新 Master

- 遍历 Master，按 `master key+match` 匹配小表字典
- 命中后写 `master_update_col`
- `fill_blank_only=True` 时，仅当 Master 当前值满足 `is_blank_value` 才写入

### 5.3 反向合并顺序

- 目标小表文件路径先按 `lower()` 排序
- 并发结果按输入顺序回收
- 若多个小表提供同一组合键，后出现文件会覆盖先出现文件（稳定且可预测）

## 6. 特殊值总表（你最关心）

| 值 | 作为 key/match | 作为“待写入内容” | 在 fill_blank_only 下是否算“目标空白” |
| --- | --- | --- | --- |
| `None` | 转 `""`，导致组合键无效（行跳过） | 写成 `""` | 是 |
| `""` | 空，组合键无效（行跳过） | 写成 `""` | 是 |
| `"   "` | `strip` 后为空，组合键无效 | 原样写入（保留空格） | 是（因 `strip` 后空） |
| `0` / `0.0` | 转 `"0"` / `"0.0"`，可参与匹配 | 写成字符串 `"0"` / `"0.0"` | 否 |
| `float('nan')` | 转 `"nan"`，可参与匹配 | 写成字符串 `"nan"` | 否 |
| `"nan"` | 非空，可参与匹配 | 写成 `"nan"` | 否 |

## 7. 关键提醒

1. 当前实现里，`NaN` 不等于“空白”；只有 `None` 和“去空格后为空字符串”才是空白。  
2. `0` 始终视为有效非空值，不会在填空模式下被覆盖。  
3. 内容写入前普遍会走字符串化（`safe_to_str`），因此数值可能落盘为文本形式。  
