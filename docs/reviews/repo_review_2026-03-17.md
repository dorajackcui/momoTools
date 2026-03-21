# Repo Review (2026-03-17)

(Closed)
按严重程度排序（P0 > P1 > P2）。


## (Closed) 1) P1 — 任务回调在 UI 调度失败时会退化到后台线程执行，违反 Tk 主线程约束  

- **问题位置**
  - `controller_modules/task_runner.py::_dispatch_to_ui` 在 `root.after` 异常时直接 `callback()`。
- **为什么它是问题**
  - 架构文档明确 UI 更新应在主线程。该 fallback 可能在工作线程内执行 `on_success/on_error`，进而触发 Tk 组件更新。
- **实际风险**
  - 产生非确定性 UI 崩溃（`TclError`）、状态错乱（busy 状态恢复异常）或“偶发无法复现”的线上问题。
- **修复建议**
  1. 禁止 worker 线程直接执行 UI 回调；`after` 失败时改为记录致命事件并安全终止任务。
  2. 为 `_dispatch_to_ui` 增加可观测性（错误日志 + telemetry code）。
  3. 增加专门单测覆盖 `after` 抛错路径。

## (Closed) 2) P1 — 关键 IO 失败原因被吞掉，导致定位困难

- **问题位置**
  - `core/kernel/excel_io.py::apply_cell_updates` 捕获 `Exception` 后仅返回 `False`。
  - `app.py` 中 `_drain_log_queue`、`_set_processing_busy` 多处 `except Exception: pass`。
- **为什么它是问题**
  - 错误上下文（异常类型、文件路径、行列信息）丢失，调用方只能知道“失败了”，无法知道“为什么失败”。
- **实际风险**
  - 用户侧出现“更新失败”但无有效日志；研发侧难以区分权限问题、文件损坏、临时文件锁、API 误用。
- **修复建议**
  1. `apply_cell_updates` 返回 `(ok, error)` 或抛出结构化异常，保持错误原因链。
  2. UI 层避免裸 `pass`，至少记录 debug/error 日志。
  3. 将错误码与上下文统一汇总到 `EventLogger`。

## (Closed) 3) P2 — 应用装配集中在 `app.py`，扩展新工具的改动面偏大

- **问题位置**
  - `app.py` 顶部集中导入全部 controller/view，`_build_tool_specs` 手工维护长列表。
- **为什么它是问题**
  - 新增/调整工具需要同时触碰多个位置，且 `app.py` 既负责窗口生命周期又负责模块装配，职责偏重。
- **实际风险**
  - 变更冲突频繁、回归风险增加；新成员难以快速定位扩展点。
- **修复建议**
  1. 将工具注册迁移到独立 registry 模块（声明式配置）。
  2. 采用按组注册 + 依赖注入，降低 `app.py` 热点复杂度。
  3. 保留 `controllers.py` 兼容面的同时，限制新增逻辑继续堆积在入口文件。

## (Closed) 4) P2 — 测试缺口：缺少对高风险失败路径/冲突策略的直接断言

- **问题位置**
  - `tests/test_task_runner.py` 覆盖了并发锁与成功/失败路径，但未覆盖 `root.after` 抛错后的线程安全行为。
  - `tests/test_core_processors_regression.py` 覆盖了空值/宽列/常规更新，但未见 `combined_key` 冲突处理策略断言。
- **为什么它是问题**
  - 当前高风险点主要在异常路径和数据冲突路径，而这两类路径回归最容易被遗漏。
- **实际风险**
  - 后续重构可能在不自知情况下改变冲突语义或重新引入跨线程 UI 更新。
- **修复建议**
  1. 增加冲突样例：同 key 多来源、多文件顺序变化、并行读取下结果稳定性。
  2. 为 task runner 增加 `after` 失败时的行为契约测试（不触 UI、正确释放 busy、可记录诊断信息）。
  3. 为 `apply_cell_updates` 增加错误传播单测（例如只读文件、被占用文件）。
