# Session Context Dump

Snapshot date: 2026-02-26
Audience: new AI/dev session handoff
Scope: current working behavior (not historical design intent)

## 1) What this project is

TM_builder is a desktop Tkinter toolset for Excel localization workflows:

- Master -> target sheets (single-column or multi-column update)
- target sheets -> Master (reverse fill)
- utility actions (column clear/insert/delete, compatibility save, deep replace)
- untranslated stats export
- terminology extractor (rules-driven extraction and terminology asset export)

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

- Top-level tab `Main Tools`
  - `Master->Target` (UpdaterController; single/multi auto split by column count)
  - `Target->Master` (ReverseUpdaterController)
- Top-level tab `Utilities`
  - `Column Clear` (ClearerController)
  - `Compatibility` (CompatibilityController)
  - `Deep Replace` (DeepReplaceController)
  - `Untranslated Stats` (UntranslatedStatsController)
  - `Term Extractor` (TerminologyExtractorController)

## 4) Current behavior highlights

### 4.1 Fill mode and post-process

- Fill behavior:
  - overwrite (default)
  - fill blank only (`fill_blank_only=True`)
- Blank check source of truth: `core/kernel/excel_io.py:is_blank_value`
- Post-process toggle:
  - available in Master->target (single/multi)
  - default enabled
  - when disabled, only skips COM save step

### 4.2 Untranslated stats export

- In `UntranslatedStatsController`:
  - selecting target folder auto-generates output path
  - auto output location = parent folder of selected small-sheet folder
  - manual output selection is still supported as optional override
  - if folder changes later, output path resets to new auto path

### 4.3 Terminology extractor MVP

- Input:
  - input folder
  - rule config JSON
  - output xlsx path
- Pipeline:
  - extraction (`record_rule`, `tag_span`)
  - normalization + dedup
  - relation build (`variant_of`, `has_head`, `has_suffix`, `head_suffix_pair`)
  - review list generation
- `record_rule` now uses dual conditions:
  - optional `version` filter: column hits configured versions
  - `key` filter supports contains (default) or regex mode via `key_regex` (case-insensitive)
- `tag_span` supports multiple opening tags via `open_tag` (string/list/comma-string)
  or `open_tags` (list/string).
- `compound_split` in extractor config is ignored at runtime.
- compound relations are generated in post-cleaning stage from deduplicated `terms`
  using `compound_delimiters` (default `["·"]`).
- File scan:
  - recursive `.xlsx/.xls`
  - ignores `~$` temp files
  - active sheet only
  - `files` config is optional; missing/`*` means process all discovered files
- Output workbook sheets:
  - `terms_summary`
  - `relations_summary`
  - `review`
  - `details`

## 5) Source entrypoints you usually need

- App wiring: `app.py`
- UI orchestration: `controllers.py`
- Processor logic:
  - `core/excel_processor.py`
  - `core/multi_column_processor.py`
  - `core/reverse_excel_processor.py`
  - `core/untranslated_stats_processor.py`
  - `core/terminology/processor.py`
  - `core/deep_replace_processor.py`
  - `core/excel_cleaner.py`
  - `core/excel_compatibility_processor.py`
- Shared kernel: `core/kernel/*`

## 6) Test entrypoints

- Syntax smoke:
  - `python -m py_compile app.py controllers.py ui_components.py`
- UI unit tests:
  - `python -m unittest discover -s tests -p "test_ui_*.py"`
- Terminology tests:
  - `python -m unittest tests.test_terminology_extractors tests.test_terminology_processor`
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
