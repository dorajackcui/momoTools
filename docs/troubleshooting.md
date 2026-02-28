# Troubleshooting Guide

Last updated: 2026-02-28
Audience: operators, QA, and agents diagnosing runtime issues
Purpose: provide quick diagnosis paths and actionable checks
Out of scope: architecture rationale and business policy decisions

## 1) No files processed or unexpected zero updates

Symptoms:

1. Task completes with 0 updates.
2. Logs show no matched rows.

Checks:

1. Selected folder contains `.xlsx`/`.xls` files.
2. Column mapping is correct (UI input is 1-based, processors use 0-based internally).
3. Expected sheet is active sheet (current processors use active sheet assumptions).

## 2) File lock or save failures

Symptoms:

1. Workbook save fails.
2. File appears in error logs with `E_*` event code.

Checks:

1. File is not open in Excel by another user/process.
2. File permissions are writable.

Actions:

1. Close related Excel windows/processes.
2. Re-run and inspect log window entries for file path + error code.

## 3) COM-related failures

Affected paths:

1. `ExcelColumnClearer`
2. `ExcelCompatibilityProcessor`
3. Post-process in Master->target single/multi when enabled

Checks:

1. Microsoft Excel is installed locally.
2. COM registration works in current Windows user environment.

Workaround:

1. Disable post-process where toggle exists if COM step is not required.

## 4) `TASK_ALREADY_RUNNING` warning

Behavior:

1. App enforces single-task lock for processing actions.
2. Starting another processing task while one is running shows warning and does not launch second task.

Expected resolution:

1. Wait for current task to finish (`Done` or `Failed` in status bar), then retry.

## 5) Log window opens but appears empty

Checks:

1. A processing task was actually started.
2. `View Logs` window is not cleared manually.
3. Logs may appear shortly after start due to queue drain cycle.

Notes:

1. Log storage is session-only in memory.
2. Closing app clears log history by design.

## 6) Perf report interpretation (`--with-perf`)

Behavior:

1. Perf baseline is report-only in current phase.
2. `regressed` means slower than reference baseline JSON, but does not fail the suite.

Checks:

1. Compare multiple local runs to account for machine variance.
2. Treat large consistent deltas as investigation candidates.

## 7) Quick command set

Syntax smoke:

```bash
python -m py_compile app.py controllers.py ui_components.py
```

Full unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Unified regression:

```bash
python scripts/run_regression_suite.py --with-golden
```

Unified regression + perf report:

```bash
python scripts/run_regression_suite.py --with-golden --with-perf
```

Encoding guardrail for docs:

```bash
python scripts/check_text_encoding.py --root docs
```