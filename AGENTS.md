# AGENTS.md

## Overview

`momoTools` is a Tkinter desktop application for Excel localization workflows. The stable business core is workbook processing around `key + match` row identity, reverse syncing into a master workbook, terminology extraction, and update-master flows.

Start documentation decisions from `docs/README.md`. Before editing inside a directory that has a local `AGENTS.md`, re-read that local contract and update it in the same change set whenever its routing, invariants, or minimum verification change.

## Repository Map

- `app.py`: desktop entrypoint, tab wiring, processor initialization
- `controllers.py`: compatibility facade for controller exports
- `controller_modules/`: validation, orchestration, task runner, UI-to-core glue
- `core/`: workbook processing behavior and domain logic
- `core/kernel/`: shared IO, normalization, logging, and helper primitives
- `core/master_update/`: merge/update-master engine internals
- `core/terminology/`: terminology pipeline stages and export logic
- `ui/`: Tkinter views, widgets, styles, validators, and view models
- `scripts/`: regression, perf, encoding, docs, and git-hook utilities
- `tests/`: `unittest` suite, golden fixtures, and optional private-data tests
- `docs/`: active canonical docs and governance entry
- `archive/old_docs/`: superseded docs and historical notes

## Required Reads Before Editing

- `docs/README.md`: canonical doc owners, change routing, and local contract registry
- Local contracts when you work in a registered directory:
  - `ui/AGENTS.md`
  - `core/master_update/AGENTS.md`
  - `core/terminology/AGENTS.md`
- `docs/testing.md`: canonical verification matrix when the change is larger than docs-only

## Global Constraints

- Keep layering strict: `ui -> controller_modules -> core`.
- Do not import UI or controller modules from `core/`.
- Keep `controllers.py` and `ui_components.py` as compatibility surfaces.
- Workbook IO behavior changes must be explicit and documented in the owning canonical docs; do not silently change blank-write, row-identity, or mode-overwrite behavior.
- Tkinter UI updates must stay on the main thread.
- Processing runs through a single-task runner; concurrent launches are intentionally blocked.

## Validation Defaults

- `docs-only`
  - `.\scripts\python.cmd scripts/check_text_encoding.py --root docs`
  - `.\scripts\python.cmd scripts/check_docs_system.py`
- `UI / controller changes`
  - `.\scripts\python.cmd -m unittest discover -s tests -p "test_ui_*.py"`
  - `.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_task_runner`
- `IO semantics or processor behavior`
  - `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden`
- `Terminology changes`
  - `.\scripts\python.cmd -m unittest tests.test_terminology_processor tests.test_terminology_extractors tests.test_ui_terminology_controller`
- `Update-master changes`
  - `.\scripts\python.cmd -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher tests.test_ui_update_master_views tests.test_ui_merge_masters_view`

Use `docs/testing.md` for the canonical full matrix and environment caveats.

## Important Constraints

- Primary runtime target is Windows desktop.
- COM-dependent flows require local Microsoft Excel and `pywin32` for real execution.
- Full regression assumes the environment can install `requirements.txt`; missing `pandas` or `pywin32` can cause import-time test failures outside the scoped app smoke path.
- Private-data tests must never write back into `tests/_private_data/`.
- Keep historical docs in `archive/old_docs/`; do not delete context without replacing it with a clearer active source.
