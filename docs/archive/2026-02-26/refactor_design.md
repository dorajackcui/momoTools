# Core Refactor Design (Strict IO Compatibility)

## Goals

1. Keep all public processor APIs unchanged.
2. Keep IO contracts unchanged (column semantics, sheet selection, key strategy).
3. Reduce duplicated core logic for scan/read/update/error handling.

## New Internal Kernel

- `core/kernel/types.py`
  - `ModeIOContract`
  - `ColumnSpec`
  - `ProcessingStats`
  - `ErrorEvent`
- `core/kernel/excel_io.py`
  - `iter_excel_files`
  - `build_combined_key`
  - `open_workbook`
  - `apply_cell_updates`
  - `run_parallel_map`
  - `run_parallel_sum`
- `core/kernel/event_logger.py`
  - `EventLogger` for structured internal error logging

## Processor Pattern

Each processor remains a public class with old methods, but internally follows:

1. Declare `ModeIOContract`.
2. Build mode-specific mapping/configuration.
3. Delegate common scan/read/write/concurrency to kernel helpers.
4. Use structured error events while preserving user-facing behavior.

## Stability Fixes Included

1. Empty target file list no longer causes thread-pool crash.
2. Workbook resources are closed consistently in read/write paths.
3. Error contexts include file and code to improve diagnostics.

## Explicit Non-Goals

1. No UI flow redesign.
2. No business rule changes.
3. No changes to controller method signatures.
