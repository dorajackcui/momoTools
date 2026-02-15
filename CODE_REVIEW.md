# TM_builder Code Review（聚焦格式稳定性与可维护性）

## 结论速览

项目核心风险不在“功能做不到”，而在：

1. **I/O 与平台耦合较重**（Win32 COM 与 OpenPyXL/Pandas混用），在“格式严格”场景下可预测性不足。
2. **错误处理过于吞异常**，容易出现“显示成功但部分文件未按预期处理”的情况。
3. **列索引/表头策略在不同模式不一致**，对使用者和后续维护者都不友好。
4. **并发与资源释放细节存在隐患**，在大批量文件时稳定性风险提升。

---

## 高优先级问题（建议先改）

### 1) 后处理（Excel COM）与主处理强耦合，且缺少可开关策略
- `excel_processor.py` 在主流程末尾默认执行 `_post_process`，强依赖 Windows + 已安装 Excel。这样会让“读写逻辑成功”与“后处理环境可用”绑定到一起。  
- 建议：
  - 将后处理改为**可配置开关**（UI 勾选“启用兼容性后处理”）；
  - 后处理失败时提供**失败清单**与可重试入口，而非仅日志。

参考：`core/excel_processor.py` 中 `process_files` 的后处理调用、`_post_process` 对 `Dispatch('Excel.Application')` 的依赖。

### 2) 大量 `except Exception: continue/return 0`，错误被静默吞掉
- 多处逐行处理出现“捕获所有异常后跳过”，导致难以定位具体脏数据或列越界来源。  
- 建议：
  - 区分可预期异常（列越界、空值）与不可预期异常；
  - 记录结构化错误（文件名、sheet、行号、列号、异常类型）；
  - 最终汇总“成功/失败/跳过原因”。

参考：`core/excel_processor.py`、`core/multi_column_processor.py`、`core/untranslated_stats_processor.py` 中的广义异常处理。

### 3) 并发 worker 数在 0 文件时可能为 0
- `max_workers = min(32, len(file_paths))` 在空文件夹时为 0，会触发 `ThreadPoolExecutor` 参数错误。  
- 建议：`max_workers = min(32, max(1, len(file_paths)))`，并在空列表时提前返回。

参考：`core/excel_processor.py` 与 `core/multi_column_processor.py`。

### 4) 使用 OpenPyXL 私有 API 写单元格
- 代码使用 `ws._get_cell` / `ws._cell`。这是内部 API，版本兼容风险高。  
- 建议统一为公开 API：`ws.cell(row=row, column=col, value=value)`。

参考：`core/excel_processor.py`、`core/multi_column_processor.py`。

---

## 中优先级问题

### 5) 表头处理策略不一致，且默认值偏“隐式”
- 部分处理器跳过表头，部分不跳过，且逻辑分散在实现细节中。  
- 建议：
  - 在 UI 和处理器统一引入 `skip_header`（默认值可按模块设置但必须显式展示）；
  - 将“首行是否参与匹配/更新”写入日志首屏。

### 6) 文件筛选规则不统一
- 有的模块忽略 `~$` 临时文件，有的没有。  
- 建议抽出统一文件发现函数（带可选过滤器），避免规则漂移。

### 7) Controller 与参数校验重复
- 列索引转换和校验逻辑在多个 controller 中重复。  
- 建议提炼通用校验器（例如 `parse_positive_column_index`），统一错误文案。

### 8) COM 打开文件路径建议规范化
- Win32 COM 对相对路径、特殊字符路径容错差异较大。  
- 建议统一 `os.path.abspath` + 明确编码/异常提示。

---

## 与“严格格式输出”强相关的建议

### 9) 增加“格式回归测试样本集”
- 建议提供最小样本（含样式、冻结窗格、筛选、命名范围、公式、批注、工作簿属性），每次改 I/O 库或参数后跑一次对比。
- 对比维度：
  - 文件可被 Excel 打开且无修复提示；
  - 关键元属性（creator/modified、defined names、sheet state）是否符合预期；
  - 非目标列样式未被污染。

### 10) 把“读写策略”做成显式模式
- 例如：
  - `safe_preserve_mode`（先读后写、必要时 COM 回写）；
  - `fast_mode`（仅 openpyxl/pandas，不做 COM 后处理）。
- 这样在“速度”与“格式保真”之间可控取舍，避免当前隐式行为。

### 11) 引入“变更最小化写入”
- 已经有 `updates` 聚合思路，建议进一步记录“原值==新值不写入”，减少不必要写回，降低格式扰动概率。

---

## 工程化建议

### 12) 增加最基础自动化测试（即便是小规模）
- 重点测：
  - 空目录、空表、缺列、重复 key、不同行尾空格；
  - 中文/英文统计模式；
  - 多列更新的列映射正确性。

### 13) 类型注解与日志接口统一
- 当前 `log_callback` 使用方式一致性一般。建议定义统一 Logger Protocol，并补齐关键函数类型注解，降低重构风险。

### 14) 代码组织
- `core/` 中多个处理器有大量重复扫描与写回逻辑，可抽象 `FileCollector`、`WorkbookIO`、`RowMatcher`。

---

## 推荐实施顺序（2 周版本）

1. **第一阶段（稳定性）**：修复 worker=0、私有 API 写入、统一错误汇总。  
2. **第二阶段（格式保障）**：后处理开关化 + 格式回归样本。  
3. **第三阶段（维护性）**：抽公共校验/文件扫描/日志结构。  

