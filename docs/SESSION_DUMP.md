# Session Context Dump

Snapshot date: 2026-02-26
Audience: new AI/dev session handoff
Scope: current working behavior (not historical design intent)

## 1) What this project is

TM_builder is a desktop Tkinter toolset for Excel localization workflows:

- Master -> small sheets (single-column or multi-column update)
- small sheets -> Master (reverse fill)
- utility actions (column clear/insert/delete, compatibility save, deep replace)
- untranslated stats export

## 2) Runtime constraints

- Platform: Windows
- Python: standard local env
- Excel COM dependency exists for:
  - `core/excel_cleaner.py`
  - `core/excel_compatibility_processor.py`
  - post-process steps in `core/excel_processor.py` and `core/multi_column_processor.py`
- If COM is unavailable, COM-related features fail while pure openpyxl paths still work.

## 3) Current UI map (actual tabs)

Defined in `app.py`:

- Top-level tab `填表工具`
  - `Master到小表` (UpdaterController; single/multi auto split by `更新列数`)
  - `小表到Master` (ReverseUpdaterController)
- Top-level tab `辅助工具`
  - `列清空` (ClearerController)
  - `兼容性处理` (CompatibilityController)
  - `深度替换` (DeepReplaceController)
  - `字数统计` (UntranslatedStatsController)

## 4) Current behavior highlights

## 4.1 Fill mode and post-process

- Fill behavior:
  - `覆盖` (default)
  - `填空` (`fill_blank_only=True`)
- Blank check source of truth: `core/kernel/excel_io.py:is_blank_value`
- Post-process toggle:
  - available in Master->small (single/multi)
  - default enabled
  - when disabled, only skips COM save step

## 4.2 Untranslated stats export (important recent change)

- In `UntranslatedStatsController`:
  - selecting target folder now auto-generates output path
  - auto output location = parent folder of selected small-sheet folder
  - file name = `未翻译统计.xlsx`, conflict strategy = `未翻译统计 (1).xlsx`, `(2)`...
  - manual output selection is still supported as optional override
  - if folder changes later, output path resets to new auto path
  - `process_stats()` no longer blocks on "must manually choose output file"

## 4.3 IO contract detail

- Read `IO_FORMAT_REQUIREMENTS.md` for strict column/sheet/default rules.
- Treat that file as canonical detailed behavior reference.

## 5) Source entrypoints you usually need

- App wiring: `app.py`
- UI orchestration: `controllers.py`
- Processor logic:
  - `core/excel_processor.py`
  - `core/multi_column_processor.py`
  - `core/reverse_excel_processor.py`
  - `core/untranslated_stats_processor.py`
  - `core/deep_replace_processor.py`
  - `core/excel_cleaner.py`
  - `core/excel_compatibility_processor.py`
- Shared kernel: `core/kernel/*`

## 6) Test entrypoints

- Syntax smoke:
  - `python -m py_compile app.py controllers.py ui_components.py`
- UI unit tests:
  - `python -m unittest discover -s tests -p "test_ui_*.py"`
- App smoke:
  - `python -m unittest tests.test_app_smoke`
- Optional golden regression utility:
  - `python scripts/run_golden_regression.py`

## 7) Known unresolved items (business/policy)

See `docs/memo_pending_translation_rules.md`:

- rule for matched rows when source/translation text is empty-string
- numeric/display fidelity policy (`str(value)` vs Excel displayed text)

## 8) Fast start checklist for next session

1. Read this file (`docs/SESSION_DUMP.md`) first.
2. Read pending decisions (`docs/memo_pending_translation_rules.md`).
3. Confirm no local regression: run UI tests.
4. If touching IO logic, cross-check `IO_FORMAT_REQUIREMENTS.md`.
5. If behavior changes, update this dump before ending session.
