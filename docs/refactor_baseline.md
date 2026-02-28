# Refactor Baseline (Behavior Freeze)

Last updated: 2026-02-28
Audience: maintainability refactor contributors
Purpose: define hard boundaries for structural refactor work
Out of scope: detailed runtime snapshot (see docs/SESSION_DUMP.md)

## Snapshot Scope

Maintainability refactor track only, with no Excel business-rule changes by default.

## Frozen Behavior Contract

1. Core processor decision rules remain unchanged:
- key/match matching behavior
- fill mode semantics (`overwrite` vs `fill_blank_only`)
- mode-specific default column semantics
2. Public entrypoints remain compatible:
- `app.py`
- `controllers.py`
- `ui_components.py`
- existing processor class names and setter method names
3. IO contract remains defined by `docs/IO_FORMAT_REQUIREMENTS.md`.

## Structural-only Refactor Boundary

Allowed:

1. Deduplicate shared pipeline flow code.
2. Improve observability while keeping existing skip/continue behavior.
3. Add regression tests and executable fixtures.
4. Improve deterministic execution/merge order.
5. Improve scheduling infrastructure (for example async controller task dispatch) without changing business decisions.
6. Improve UI-side observability plumbing (status/log routing) without changing business semantics.
7. Add report-only performance baseline infrastructure (non-blocking).

Not allowed in this track:

1. Changing Excel business decisions.
2. Changing UI interaction semantics in a user-visible breaking way.
3. Breaking existing imports or entry symbols.

## Regression Gate

Unified gate:

```bash
python scripts/run_regression_suite.py --with-golden
```

Golden-only:

```bash
python scripts/run_golden_regression.py --manifest tests/golden/manifest.sample.json
```

Optional lightweight performance baseline (report-only, non-blocking):

```bash
python scripts/run_perf_baseline.py
python scripts/run_regression_suite.py --with-perf
python scripts/run_regression_suite.py --with-perf --perf-baseline-json tests/perf/reports/<old>.json
```

## Note On Perf Reports

A `regressed` marker in perf reports is informational in this phase and does not fail regression by design.
