# Architecture (Canonical)

Last updated: 2026-03-03
Audience: agents and engineers
Owns: stable design boundaries and compatibility contracts
Does not own: runtime snapshot and IO edge semantics

## 1) Design Goals

1. Keep Excel localization workflows stable while improving maintainability.
2. Preserve existing behavior unless an explicit business-rule change is approved.
3. Keep legacy entrypoints/imports compatible.

## 2) Layer Boundaries

1. UI layer (`ui/views`, `ui/widgets`, `ui/theme`, `ui/strings`)
- Handles layout, widget interaction, and view state.
- Must not contain Excel business logic.

2. Controller layer (`controller_modules`, `controllers.py` facade)
- Handles validation, processor binding, task scheduling, success/error UX.
- `controllers.py` is compatibility facade, not primary feature implementation.

3. Core layer (`core/*`)
- Handles Excel business logic and processing semantics.
- Exposes stable processor classes and setter methods consumed by controllers/tests.

4. Shared internals (`core/kernel`, `core/pipeline`)
- Kernel: IO/value/error primitives.
- Pipeline: reusable execution blocks.

## 3) Dependency Rules

Allowed:

1. `ui -> controller_modules`
2. `controller_modules -> core`
3. `core -> core/kernel`, `core/pipeline`

Not allowed:

1. `core` importing UI/controller modules
2. `ui` calling processors directly
3. New behavior implemented only in `controllers.py`

## 4) Runtime Contract

1. Tk UI updates stay on main thread.
2. Processing tasks run via `TkSingleTaskRunner` worker thread.
3. Completion callbacks return to UI via `root.after(...)`.
4. Single-task lock blocks concurrent processing actions.
5. Cancellation is not supported currently.

## 5) Observability Contract

1. Processors emit logs via `log_callback`.
2. Structured failures are emitted through `EventLogger`.
3. App log bus (queue + periodic drain) feeds status line and log window.
4. Task status uses `Running`, `Done`, `Failed`.

## 6) Compatibility Surface (Stable)

1. `app.py` entrypoint behavior
2. `controllers.py` exported symbols (`filedialog` included)
3. `ui_components.py` compatibility exports
4. Existing processor class names and setter method names

## 7) Refactor Guardrails

### Frozen contracts

1. Processor decision semantics stay unchanged:
- key/match behavior
- fill mode (`overwrite`, `fill_blank_only`)
- blank write policy (`allow_blank_write`)
- mode default columns
2. Public compatibility surfaces in this doc stay unchanged unless explicitly approved.
3. IO contract remains owned by `docs/IO_FORMAT_REQUIREMENTS.md`.

### Allowed changes

1. Code deduplication and module extraction.
2. Scheduling/task-runner internal improvements.
3. Observability/logging plumbing improvements.
4. Test coverage expansion (unit/golden/private fixture tests).
5. Deterministic processing and merge-order hardening.

### Disallowed changes

1. Silent business-rule changes.
2. User-visible breaking interaction changes without explicit migration.
3. Breaking imports or entry symbols used by current code/tests.

### Required regression gate

```bash
python scripts/run_regression_suite.py --with-golden
```

Optional diagnostics (non-gating):

```bash
python scripts/run_perf_baseline.py
python -m unittest tests.test_private_data_skip_blank_write -v
```

## 8) Doc Routing Rules

When behavior changes, update only the owning doc:

1. Stable design changes -> `docs/ARCHITECTURE.md`
2. Runtime snapshot changes -> `docs/SESSION_DUMP.md`
3. IO semantics changes -> `docs/IO_FORMAT_REQUIREMENTS.md`
4. Terminology config contract changes -> `docs/terminology_rule_config_notes.md`
5. Runtime troubleshooting updates -> `docs/troubleshooting.md`
