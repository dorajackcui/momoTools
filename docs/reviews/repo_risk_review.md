# Repo 风险 Review（性能 / 安全 / 工程化）

> 范围：基于当前仓库代码静态审查（未做生产流量压测），重点覆盖 `core/`、`controller_modules/`、`scripts/` 与发布流程资产。

## P0

### 1) 反向流程对全量目标数据做内存聚合，存在 OOM 与长时间 GC 风险（性能）
- **问题位置**：`core/reverse_excel_processor.py` 的 `_read_target_files()` + `_update_master_file()`。
- **为什么是问题**：当前实现先并行读取所有目标文件到 `results`，再把每个 `local_dict` 合并到一个全局 `data_dict`，最后再统一更新 master。数据规模一旦上来（文件多、键值大、重复率低），会导致 Python 堆内存快速上升。
- **实际风险**：大批量任务可能出现内存峰值过高、频繁 Full GC、处理时间陡增，甚至进程被系统杀死；批处理稳定性下降。
- **修复建议**：改为“流式/分块更新”策略：
  1. 按文件或按批次读取并直接应用到 master（或中间索引），避免保留全量字典；
  2. 对超大任务启用分片（chunk）与阶段性落盘；
  3. 增加内存占用监控与阈值保护（超过阈值降并发或中断并提示）。
- **优先级**：**P0**

## P1

### 2) 单向流程每个文件先读后再重开写，I/O 放大（性能）
- **问题位置**：`core/excel_processor.py` 的 `_process_single_file()` 与 `core/kernel/excel_io.py` 的 `apply_cell_updates()`。
- **为什么是问题**：当前流程先 `read_only` 扫描一遍文件收集 `updates`，随后再次 `load_workbook` 写回并 `save`，导致每个文件至少两次打开/解析/关闭。
- **实际风险**：在网络盘、机械盘或大文件场景下吞吐明显下降，批任务耗时被放大。
- **修复建议**：
  1. 优先考虑单次打开完成读写（非 `read_only` 模式下边扫描边更新）；
  2. 若必须分离扫描与写入，增加“无更新时不重开”与批量保存策略，并评估 openpyxl `read_only` 与 `write_only` 组合路径。
- **优先级**：**P1**



### (Closed) 3) 并行读文件时共享统计对象无同步保护（工程化/正确性）
- **问题位置**：`core/reverse_excel_processor.py` 中 `_read_single_target_file()` 对 `self.stats.files_succeeded` 的自增。
- **为什么是问题**：该方法由 `run_parallel_map()` 线程池并发调用，`self.stats` 为共享对象且无锁保护，统计结果可能出现竞态。
- **实际风险**：任务成功/失败计数不准确，影响运维判断、问题回溯和自动化报告可信度。
- **修复建议**：
  1. 改为每线程返回局部计数，主线程汇总；
  2. 或在共享写操作上加锁（更推荐前者）。
- **优先级**：**P1**


