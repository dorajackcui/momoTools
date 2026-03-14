# AGENTS.md

## Overview

`momoTools` is a Tkinter desktop application for Excel localization workflows. The stable business core is workbook processing around `key + match` row identity, reverse syncing into a master workbook, terminology extraction, and update-master flows.

Start navigation from `docs/README.md`. Keep this file focused on repo layout, non-obvious constraints, and validation defaults for agents.

## Repository Map

- `app.py`: desktop entrypoint, tab wiring, processor initialization
- `controllers.py`: compatibility facade for controller exports
- `controller_modules/`: validation, orchestration, task runner, UI-to-core glue
- `core/`: workbook processing behavior and domain logic
- `core/kernel/`: shared IO, normalization, logging, and helper primitives
- `core/master_update/`: merge/update-master engine internals
- `core/terminology/`: terminology pipeline stages and export logic
- `ui/`: Tkinter views, widgets, styles, validators, and view models
- `scripts/`: regression, perf, encoding, and git-hook utilities
- `tests/`: `unittest` suite, golden fixtures, and optional private-data tests
- `docs/`: active canonical docs
- `archive/old_docs/`: superseded docs and historical notes

## Source Of Truth

- Project navigation and doc ownership: `docs/README.md`
- Layering, runtime model, compatibility boundaries: `docs/architecture.md`
- Excel normalization and write semantics: `docs/io-contract.md`
- Environment setup and developer workflow: `docs/development.md`
- Validation commands and test selection: `docs/testing.md`
- Packaging and release constraints: `docs/deployment.md`
- Stable behavioral decisions: `docs/decisions.md`

If behavior changes, update the owning doc in the same change set.

## Environment Matrix

- `Docs-only / static checks`
  - No app startup required.
  - Use docs encoding validation and targeted text edits only.
- `Core non-COM development`
  - Install `requirements.txt`.
  - App/module imports and non-COM processor work should function.
  - If `pywin32` is missing, COM tools load but raise a clear runtime error when invoked.
- `Full desktop validation on Windows`
  - Requires Windows, Microsoft Excel, and `pywin32`.
  - Needed for compatibility repair, column tools, and COM-backed post-processing confidence.

## Working Rules

- Keep layering strict: `ui -> controller_modules -> core`.
- Do not import UI or controller modules from `core/`.
- Keep `controllers.py` and `ui_components.py` as compatibility surfaces.
- Treat `docs/io-contract.md` as the only owning doc for value normalization, blank handling, and match/write rules.
- Do not silently change `allow_blank_write=False`, `fill_blank_only`, row identity policy, or mode-specific overwrite semantics.
- Tkinter UI updates must stay on the main thread.
- Processing runs through a single-task runner; concurrent launches are intentionally blocked.

## Validation Defaults

- `docs-only`
  - `python scripts/check_text_encoding.py --root docs`
- `UI / controller changes`
  - `python -m unittest discover -s tests -p "test_ui_*.py"`
  - `python -m unittest tests.test_ui_controllers tests.test_task_runner`
- `IO semantics or processor behavior`
  - `python scripts/run_regression_suite.py --with-golden`
- `Terminology changes`
  - `python -m unittest tests.test_terminology_processor tests.test_terminology_extractors tests.test_ui_terminology_controller`
- `Update-master changes`
  - `python -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher tests.test_ui_update_master_views tests.test_ui_merge_masters_view`

See `docs/testing.md` for the fuller change-type matrix and environment caveats.

## Important Constraints

- Primary runtime target is Windows desktop.
- COM-dependent flows require local Microsoft Excel and `pywin32` for real execution.
- Full regression assumes the environment can install `requirements.txt`; missing `pandas` or `pywin32` can cause import-time test failures outside the scoped app smoke path.
- Private-data tests must never write back into `tests/_private_data/`.
- Keep historical docs in `archive/old_docs/`; do not delete context without replacing it with a clearer source of truth.
