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
6. Update Master suite (merge/update/content)

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

3. `Update Master`
- `Merge Masters` (`MasterMergeController`)
- `Update Master` (`UpdateMasterController`)
- `Update Content` (`UpdateContentController`)

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
6. Update Master modes use one processor with policy combinations:
- `Merge Masters`: fill blank only + allow new key (append-only default; existing master rows are not modified)
- `Update Master`: dense-row overwrite (blank values are valid and can clear master cells) + allow new key
- `Update Content`: sparse non-blank overwrite + existing key only
- Compatibility note: policy value `overwrite_non_blank` is intentionally preserved for dispatcher/API compatibility, while actual write behavior is mode-specific.
7. `Merge Masters` source duplicate behavior:
- duplicate identities in updates keep first-processed full row (whole-row winner), then append only if master lacks the identity.
8. `Update Master` source duplicate behavior:
- duplicate identities in updates keep last-processed full row (whole-row winner).
9. Row-key strategy split:
- `Merge Masters`: UI toggle for `combined_key` (default) vs `key_only`
- `Update Master`: fixed `key_only`; `match` column is updatable content
- `Update Content`: fixed `combined_key`; requires key+match hit
10. Update Master suite emits stage timing summaries:
- `Merge Masters`: `collect_sources`, `scan_master_ro`, `open_master_rw_apply`, `save_master`, `total`
- `collect_sources`
- `scan_master_ro`
- `plan_updates`
- `open_master_rw_apply`
- `save_master`
- `total`
11. Update Master suite column scope:
- shared `last_update_col` for all three modes (applies to both master and source)
- default UI value is `K` (1-based column 11)

## 7) Session Entry Checklist

1. Read `docs/ARCHITECTURE.md`.
2. Read this file.
3. Read `docs/IO_FORMAT_REQUIREMENTS.md` before changing processors.
4. Use commands from `docs/README.md`.
5. If runtime behavior changes, update this file in the same change set.
