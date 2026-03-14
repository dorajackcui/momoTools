# AGENTS.md

## What This Directory Owns

`ui/` contains Tkinter views, widgets, styles, validators, strings, and view-model dataclasses. It is the presentation layer for the desktop app.

## Stable UI Rules

- Tkinter UI updates must stay on the main thread.
- Views should collect input and render state, not own business rules.
- Controllers remain the orchestration boundary between `ui/` and `core/`.
- Shared form/state shapes should live in `ui/view_models.py` or nearby UI helpers, not in core modules.

## Modification Boundaries

- Do not call processors directly from views.
- Do not move workbook semantics into validators or widgets.
- Preserve existing compatibility exports through `ui_components.py` unless an explicit migration is approved.
- Keep visual/text changes aligned with existing Tk patterns unless the task explicitly calls for UI redesign.

## What To Re-Read Before Editing

- `docs/architecture.md`
- `docs/testing.md`
- `tests/test_ui_*.py`
- `tests/test_ui_controllers.py`

## Minimum Verification

- `python -m unittest discover -s tests -p "test_ui_*.py"`
- `python -m unittest tests.test_ui_controllers tests.test_task_runner`
