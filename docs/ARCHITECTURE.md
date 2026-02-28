# Architecture Overview

Last updated: 2026-02-28
Audience: agents and engineers who need project-level design context
Purpose: provide stable design principles, layering rules, and change boundaries
Out of scope: temporary run snapshots, pending business policy decisions, detailed IO edge-case tables

## 1) Project Goals And Non-goals

### Goals

1. Keep Excel localization workflows reliable and maintainable.
2. Preserve existing business behavior while improving structure, testability, and observability.
3. Provide a stable compatibility surface for existing entrypoints and imports.

### Non-goals

1. No silent business-rule rewrites under maintainability tasks.
2. No breaking change to public entrypoints for app startup and legacy imports.
3. No heavy tooling expansion as a prerequisite for normal development.

## 2) Layered Architecture

### UI layer (`ui/views`, `ui/widgets`, `ui/theme`, `ui/strings`)

1. Owns widget layout, user interaction, and view-level configuration input.
2. Must not contain Excel business logic.

### Controller layer (`controller_modules`, `controllers.py` facade)

1. Owns orchestration: validation, processor parameter binding, task scheduling, success/error UX.
2. `BaseController` centralizes shared execution helpers.
3. `TaskRunner` abstraction decouples controller behavior from sync/async execution policy.

### Core processor layer (`core/*`)

1. Owns Excel read/match/update logic and mode-specific business behavior.
2. Exposes stable processor classes and setter APIs used by controllers.
3. Must remain business-rule stable unless explicitly approved.

### Kernel and pipeline layer (`core/kernel`, `core/pipeline`)

1. Kernel provides shared primitives: IO contracts, workbook helpers, error/event structures.
2. Pipeline provides reusable execution flow blocks (parallel execution, post-process helpers).
3. These modules support deduplication across processors without changing mode semantics.

## 3) Dependency Direction And Boundaries

Allowed dependency direction:

1. `ui` -> `controller_modules`
2. `controller_modules` -> `core`
3. `core` -> `core/kernel` and `core/pipeline`

Disallowed patterns:

1. `core` importing UI or controller modules.
2. `ui` bypassing controllers to call processors directly.
3. New features implemented only in `controllers.py` compatibility facade.

## 4) Runtime Model

1. Tk main thread owns all widget updates (main thread / UI thread).
2. `TkSingleTaskRunner` executes processor actions on a worker thread.
3. Completion callbacks are marshaled back through `root.after(...)`.
4. Single-task global lock prevents concurrent processing actions.
5. During processing, only controls marked as processing actions are disabled.

## 5) Observability Model

1. Processors emit runtime messages through `log_callback`.
2. `EventLogger` emits structured error lines with mode and code context.
3. App-level log bus (`queue` + periodic drain) feeds:
- status bar summary
- optional log window (`View Logs` -> `LogWindow`)
4. Task state messages use `Running/Done/Failed` and remain visible even when logs are active.

## 6) Compatibility Contract

The following contracts are treated as stable public surfaces:

1. `app.py` app entrypoint behavior.
2. `controllers.py` facade exports and `filedialog` compatibility symbol.
3. `ui_components.py` compatibility export behavior.
4. Existing processor class names and setter method names used by controllers/tests.

## 7) Change Policy

### Required update path

1. Controller behavior changes: edit `controller_modules/*` first.
2. Keep `controllers.py` as compatibility facade, not primary implementation.
3. If core behavior changes, explicitly classify as either:
- structural refactor only, or
- business-rule change (requires explicit approval and regression expansion).

### Documentation sync checklist (triggered by relevant code changes)

1. Stable design changes -> update this file (`docs/ARCHITECTURE.md`).
2. Current runtime/feature snapshot changes -> update `docs/SESSION_DUMP.md`.
3. Refactor boundary changes -> update `docs/refactor_baseline.md`.
4. IO semantics changes -> update `docs/IO_FORMAT_REQUIREMENTS.md`.
5. Pending policy decisions only -> update `docs/memo_pending_translation_rules.md`.

### Validation checklist after meaningful changes

1. `python scripts/check_text_encoding.py --root docs`
2. `python -m py_compile app.py controllers.py ui_components.py`
3. `python -m unittest discover -s tests -p "test_*.py"`
4. `python scripts/run_regression_suite.py --with-golden`
