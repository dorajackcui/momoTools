# UI Refactor Guide

## 1. 目标

本次 UI 重构目标：

1. 保持 `app.py`、`controllers.py`、`ui_components.py` 的外部入口兼容。
2. 将页面实现拆分到 `ui/views/*`，避免单文件堆叠。
3. 通过 `get_config()` + dataclass 建立 View/Controller 契约。
4. 统一校验、提示框、样式和文案来源。

## 2. 模块职责

- `ui/theme.py`
  - 存放颜色、字体、按钮样式、Notebook 样式。
  - 通过 `configure_ttk_style()` 应用主题。
- `ui/strings.py`
  - 存放标题、错误提示、默认文本、路径显示前缀。
- `ui/validators.py`
  - UI 输入校验（列号、列索引转换等）。
  - 统一抛出 `ValidationError`。
- `ui/view_models.py`
  - 页面配置 dataclass（`UpdaterConfig`、`MultiColumnConfig` 等）。
- `ui/dialog_service.py`
  - `messagebox` 适配层，便于测试替换。
- `ui/widgets/`
  - 可复用控件和工厂方法。
- `ui/views/`
  - 每个页面独立文件，提供：
    - `get_config()`
    - `set_xxx_label(...)` 语义化更新方法

## 3. View/Controller 契约

### 3.1 View 必须提供

1. 页面配置读取：
   - `get_config()` 返回 `ui.view_models` 中对应 dataclass。
2. 标签更新方法（按页面能力提供）：
   - 如 `set_master_file_label(path)`、`set_target_folder_label(path)`。

### 3.2 Controller 约束

1. 不直接访问 `frame.xxx_var` 或 `frame.xxx_label`。
2. 只通过：
   - `frame.get_config()`
   - `frame.set_xxx_label()`
3. 校验异常统一捕获 `ValidationError` 并通过 `DialogService` 提示。

## 4. 新增页面流程

1. 在 `ui/view_models.py` 增加配置 dataclass（如需）。
2. 在 `ui/views/` 新建页面类，实现：
   - UI 构建
   - `get_config()`
   - 语义化标签更新方法
3. 在 `controllers.py` 新增/扩展控制器，仅做编排：
   - 文件选择
   - 调用 `get_config()`
   - 设置 processor 参数并执行
4. 在 `ui_components.py` 追加兼容导出。
5. 在 `app.py` 装配新页面。

## 5. 回归检查清单

1. `python -m py_compile app.py controllers.py ui_components.py`
2. `python -m unittest discover -s tests -p "test_ui_*.py"`
3. 手工检查：
   - 文件/目录未选择时提示一致
   - 列号非法时提示一致
   - toggle 状态能正确传递到 processor
   - 各页流程至少一条成功路径 + 一条失败路径

## 6. Master到小表统一模式

`Master到小表` 页面已统一为单列/多列一体化入口：

1. 使用统一字段：
   - 小表：`Key列`、`原文列`、`更新开始列`
   - Master：`Key列`、`原文列`、`内容开始列`
   - 参数：`更新列数`（默认 `1`）
2. 控制器分流规则：
   - `更新列数 == 1` 调用 `ExcelProcessor`
   - `更新列数 > 1` 调用 `MultiColumnExcelProcessor`
3. 主界面不再显示单独“多列更新”标签页，减少模式选择复杂度。
