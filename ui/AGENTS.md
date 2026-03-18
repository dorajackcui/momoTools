# AGENTS.md

## What This Directory Owns

`ui/` owns Tkinter views, widgets, styles, validators, strings, and view-model dataclasses. It is the presentation layer for the desktop app and the local contract for UI-specific editing guidance.

## Canonical Docs To Update

- `docs/architecture.md`
- `docs/testing.md`
- `docs/decisions.md` when a UI orchestration rule becomes a durable guarantee

## Change Routing

- UI composition, notebook layout, view-model shape, or controller-facing UI state flow -> `docs/architecture.md`
- UI validation expectations or minimum verification changes -> `docs/testing.md`
- Durable orchestration rules that should not silently drift -> `docs/decisions.md`
- Directory-only editing guidance, routing, or minimum verification for `ui/` -> `ui/AGENTS.md`

## Local Invariants

- Tkinter widget updates and callbacks that touch Tk state must stay on the main thread. Owner: `docs/architecture.md`
- Views collect input and render state; they do not own workbook business rules. Owner: `docs/architecture.md`
- Shared form and state shapes stay in UI helpers such as `ui/view_models.py`, not in core modules. Owner: local
- Visual and copy edits should stay aligned with existing Tk patterns unless the change is an intentional redesign. Owner: local

## Modification Boundaries

- Do not call processors directly from views.
- Do not move workbook semantics into validators or widgets.
- Preserve `ui_components.py` compatibility exports unless an explicit migration is approved.
- Keep controller orchestration in `controller_modules/`, not in view classes.

## Minimum Verification

- `.\scripts\python.cmd -m unittest discover -s tests -p "test_ui_*.py"`
- `.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_task_runner`
