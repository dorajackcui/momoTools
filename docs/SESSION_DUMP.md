# Session Snapshot (Current Runtime)

Last updated: 2026-03-03
Audience: agents/devs starting a new session
Owns: current runtime/UI/task snapshot
Does not own: stable architecture and IO edge semantics

## 1) Product Scope

Desktop Tkinter toolset for Excel localization workflows:

1. `Master->Target` update (single and multi-column)
2. `Target->Master` reverse update
3. Batch orchestration for single/reverse update modes
4. Utilities: column clear, compatibility save, deep replace, untranslated stats
5. Terminology extraction from rule config JSON

## 2) Runtime Constraints

1. Primary runtime is Windows desktop.
2. COM-dependent paths:
- `core/excel_cleaner.py`
- `core/excel_compatibility_processor.py`
- post-process step in single/multi update processors when enabled
3. Non-COM openpyxl paths still run without COM.

## 3) Current UI Structure (`app.py`)

Top-level notebook groups:

1. `Main Tools`
- `Master->Target` (`UpdaterController`)
- `Target->Master` (`ReverseUpdaterController`)
- `Batch` (`BatchController`)

2. `Utilities`
- `Column Clear`
- `Compatibility`
- `Deep Replace`
- `Untranslated Stats`
- `Term Extractor`

## 4) Task Model

1. Controllers dispatch processing through `TaskRunner`.
2. Production runner is `TkSingleTaskRunner` (worker thread + UI callback marshal).
3. Single-task lock is enabled (`TASK_ALREADY_RUNNING` on concurrent start).
4. No cancellation support.

## 5) User Feedback Model

1. Status line uses `Running: <task>`, `Done: <task>`, `Failed: <task>`.
2. `View Logs` opens `LogWindow`.
3. Logs are queue-drained into an in-memory bounded buffer (session only).

## 6) Behavior Highlights (Current)

1. Fill modes: overwrite / fill blank only.
2. Blank write policy:
- default `allow_blank_write=False` (skip blank content write)
- opt-in `allow_blank_write=True` (blank content can clear cells)
3. Reverse merge order is deterministic (sorted target file paths, later overrides earlier).
4. Terminology extractor pipeline: extract -> normalize/dedup -> relation/review -> export.
5. Terminology output sheets: `terms_summary`, `relations_summary`, `review`, `details`.

## 7) Session Entry Checklist

1. Read `docs/ARCHITECTURE.md`.
2. Read this file.
3. Read `docs/IO_FORMAT_REQUIREMENTS.md` before changing processors.
4. Use commands from `docs/README.md`.
5. If runtime behavior changes, update this file in the same change set.
