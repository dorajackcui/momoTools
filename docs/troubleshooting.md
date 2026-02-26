# Troubleshooting Guide (Current)

Last updated: 2026-02-26

## 1) Empty folder or no Excel files

Symptom:
- task finishes with 0 updates, or shows no files found.

Check:
- selected folder actually contains `.xlsx`/`.xls`.
- temporary files (`~$`) are ignored in some flows.

Note:
- thread-pool crash on empty list was fixed in kernel helpers.

## 2) File lock or save failure

Symptom:
- write-back fails, workbook cannot be opened, or output not saved.

Check:
- file is open in Excel or locked by another process/user.
- file permissions are read-only.

Action:
- close all related Excel windows/processes.
- rerun and inspect log lines with `[E_*]` codes and `file=...`.

## 3) COM-related failures (Windows + Office dependency)

Affected functions:
- `ExcelColumnClearer`
- `ExcelCompatibilityProcessor`
- post-process steps in Master->small single/multi processors

Check:
- Microsoft Excel installed locally.
- Office COM registration available.

Action:
- run with a minimal sample workbook first.
- if COM path is not required, disable post-process toggle where available.

## 4) Wrong columns / no matched updates

Symptom:
- process runs but updates are unexpectedly low or zero.

Check:
- key/match/update column indices are configured correctly (UI is 1-based input, processor uses 0-based internally after conversion).
- selected sheet assumptions (`active` sheet only).
- key/match values contain empty cells or unexpected whitespace.

Reference:
- `IO_FORMAT_REQUIREMENTS.md` for detailed per-mode column defaults.

## 5) Untranslated stats output path confusion

Current behavior:
- selecting stats target folder auto-generates output file in the parent folder.
- default name is `未翻译统计.xlsx`; conflicts auto-increment to `未翻译统计 (n).xlsx`.
- manual output path remains optional override.
- changing target folder resets output path to new auto path.

If user cannot find output:
- check the parent directory of the selected small-sheet folder first.

## 6) Regression check quick commands

- `python -m py_compile app.py controllers.py ui_components.py`
- `python -m unittest discover -s tests -p "test_ui_*.py"`
- optional: `python scripts/run_golden_regression.py`
