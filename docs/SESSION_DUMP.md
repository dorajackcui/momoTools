# Session Context Dump

Last updated: 2026-02-28
Audience: new agent/dev session handoff
Purpose: capture current runtime behavior and operational entrypoints
Out of scope: long-term design principles (see docs/ARCHITECTURE.md)

## 1) Project Snapshot

TM_builder is a desktop Tkinter toolset for Excel localization workflows:

1. Master -> target (single-column and multi-column updates)
2. target -> Master reverse fill
3. Utility tools (column clear/insert/delete, compatibility save, deep replace)
4. Untranslated stats export
5. Terminology extraction (rule-driven)

## 2) Runtime Constraints

1. Platform: Windows desktop runtime.
2. Excel COM dependency required for:
- `core/excel_cleaner.py`
- `core/excel_compatibility_processor.py`
- post-process step in `core/excel_processor.py` and `core/multi_column_processor.py` when enabled
3. Pure openpyxl flows still run without COM features.

## 3) Current UI Map

Defined in `app.py`:

1. Top-level group: `Main Tools`
- `Master->Target` (`UpdaterController`, auto routes single/multi by column count)
- `Target->Master` (`ReverseUpdaterController`)

2. Top-level group: `Utilities`
- `Column Clear`
- `Compatibility`
- `Deep Replace`
- `Untranslated Stats`
- `Term Extractor`

## 4) Current Execution Model

1. Controllers run actions through `TaskRunner` abstraction.
2. Production mode uses `TkSingleTaskRunner`:
- worker thread runs processor action
- UI callbacks return via `root.after(...)`
3. Single-task global lock is enabled:
- when one processing action is running, all processing buttons are disabled
- concurrent starts show `TASK_ALREADY_RUNNING`
4. No cancellation support in current scope.

## 5) Current UI Feedback Model

1. Status bar state:
- `Running: <task>`
- `Done: <task>`
- `Failed: <task>`
2. Log visualization:
- `View Logs` opens `LogWindow`
- app log bus uses queue + periodic drain
- log buffer is in-memory session scope (bounded, non-persistent)
3. Existing success/failure dialogs remain unchanged.

## 6) Core Behavior Highlights

1. Fill mode remains:
- overwrite
- fill blank only (`is_blank_value` in `core/kernel/excel_io.py`)
2. Reverse merge precedence is deterministic (sorted input order + ordered merge).
3. Post-process in single/multi remains configurable and defaults enabled.
4. Business decision rules are unchanged under refactor tracks.

## 7) Terminology Extractor Snapshot

1. Inputs: input folder, rule config JSON, output xlsx.
2. Rule config path is persisted and restored.
3. Pipeline includes extraction, normalization/dedup, relation build, review generation.
4. Global `versions` filter applies before extractor execution.
5. Output sheets: `terms_summary`, `relations_summary`, `review`, `details`.

## 8) Performance Baseline Snapshot

1. Script: `scripts/run_perf_baseline.py`
2. Scope: `master_to_target_single`, `master_to_target_multi`, `target_to_master_reverse`
3. Default repeats: 3 iterations per case
4. Output: markdown + json report in `tests/perf/reports`
5. `--baseline-json` comparison is report-only (non-blocking)

## 9) Entry Commands

Syntax smoke:

```bash
python -m py_compile app.py controllers.py ui_components.py
```

Unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Unified regression:

```bash
python scripts/run_regression_suite.py --with-golden
```

Optional perf with regression:

```bash
python scripts/run_regression_suite.py --with-golden --with-perf
```

## 10) Pending Business Decisions

Pending policy items are tracked in:

- `docs/memo_pending_translation_rules.md`

Do not place architecture notes there.

## 11) Fast Start Checklist

1. Read `docs/ARCHITECTURE.md`.
2. Read this snapshot (`docs/SESSION_DUMP.md`).
3. Run syntax + unittest baseline commands.
4. If touching IO semantics, verify `docs/IO_FORMAT_REQUIREMENTS.md`.
5. If behavior changes, update this file in the same change set.
