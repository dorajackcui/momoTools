# Refactor Baseline (Behavior Freeze)

Snapshot date: 2026-02-28  
Scope: maintainability refactor only, no Excel business-rule changes.

## Frozen behavior contract

1. `core` processor decision rules are unchanged:
   - key/match matching
   - fill mode (`overwrite` vs `fill_blank_only`)
   - per-mode default column semantics
2. Public entrypoints remain compatible:
   - `app.py`
   - `controllers.py`
   - `ui_components.py`
   - existing processor class names and setter methods
3. IO contract is still defined by `IO_FORMAT_REQUIREMENTS.md`.

## Structural-only refactor boundary

Allowed:
- deduplicate shared pipeline flow code
- improve observability (error logging while keeping skip/continue behavior)
- add regression tests and executable fixtures
- improve deterministic merge/execution order

Not allowed in this refactor track:
- changing Excel business decisions
- changing UI interaction semantics
- breaking existing imports/entry symbols

## Regression gate

Single entry:

```bash
python scripts/run_regression_suite.py --with-golden
```

Golden-only:

```bash
python scripts/run_golden_regression.py --manifest tests/golden/manifest.sample.json
```
