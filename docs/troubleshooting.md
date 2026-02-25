# Troubleshooting Guide

## 1. `ThreadPoolExecutor(max_workers=0)` style failures

- Symptom: process crashes when folder is empty.
- Check: target folder contains zero matching Excel files.
- Status: fixed by guarded parallel helpers in `core/kernel/excel_io.py`.

## 2. File lock / cannot open workbook

- Symptom: write-back fails or files remain locked.
- Check:
  - Excel process still holding file.
  - Input file opened by another user.
- Action:
  - Close related Excel windows.
  - Re-run and inspect `[E_*]` event logs for file path.

## 3. COM-based processor failures

- Affected: `ExcelColumnClearer`, `ExcelCompatibilityProcessor`.
- Requirement: Microsoft Excel installed on Windows host.
- If failures persist:
  - validate Office COM registration.
  - run with minimal sample file to isolate environment issue.

## 4. Regression mismatch in golden checks

- Use `scripts/run_golden_regression.py`.
- Inspect report under `tests/golden/reports/`.
- Confirm:
  - same sheet (`active` vs named sheet)
  - same source fixture version
  - same processor mode and column configuration
