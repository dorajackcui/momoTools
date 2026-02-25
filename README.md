# Momo - Build your mastersheet

基于 `key + match` 的 Excel 批量处理工具集，支持多个处理模式与多文件并发处理。

## 主要功能

### 填表工具
- `Master 到小表`：统一单列/多列更新入口，`更新列数=1` 为单列，`>1` 自动多列。
- `小表到 Master`：从多个小表回填到 Master。

### 辅助工具
- `列清空/插入/删除`：按列号批量处理文件。
- `兼容性处理`：通过 Excel COM 重新保存文件。
- `深度替换`：按同名文件在目录间替换。
- `字数统计`：统计未翻译内容并导出。

## UI 架构（2026 Refactor）

UI 层已按“视图契约 + 可复用组件”重构，入口保持兼容：

- `app.py`：应用入口与装配。
- `ui_components.py`：兼容导出层（旧 import 不受影响）。
- `controllers.py`：控制器编排层（不再直接读取 `frame.xxx_var`）。
- `ui/`：新 UI 内部实现。
  - `ui/theme.py`：主题常量和 `ttk` 样式配置。
  - `ui/strings.py`：集中式文案。
  - `ui/validators.py`：统一输入校验。
  - `ui/view_models.py`：视图配置 dataclass。
  - `ui/dialog_service.py`：消息框封装。
  - `ui/widgets/`：复用控件（含 `ToggleSwitch`）。
  - `ui/views/`：各工具页面的独立视图实现。

## 开发与测试

- 语法检查：`python -m py_compile app.py controllers.py ui_components.py`
- UI 单元测试：`python -m unittest discover -s tests -p "test_ui_*.py"`
- 启动 smoke：`python -m unittest tests.test_app_smoke`

## 注意事项

- 处理前请备份重要文件。
- 兼容性处理和列清理依赖本机已安装 Microsoft Excel（`win32com`）。
- 建议先用小批量样例验证列配置，再处理全量文件。
