# Docs Index

Last updated: 2026-02-28
Audience: agents and engineers onboarding into this repository
Purpose: provide the shortest reliable navigation path for project context
Out of scope: detailed implementation history in archived docs

## Recommended Reading Order

1. `docs/ARCHITECTURE.md`
2. `docs/SESSION_DUMP.md`
3. `docs/IO_FORMAT_REQUIREMENTS.md`
4. `docs/refactor_baseline.md`
5. `docs/troubleshooting.md`
6. `docs/memo_pending_translation_rules.md`

## Core Pages (4)

1. `docs/ARCHITECTURE.md`
- Stable design principles, layering rules, compatibility contract.

2. `docs/SESSION_DUMP.md`
- Current runtime snapshot (UI map, task model, observability state, commands).

3. `docs/IO_FORMAT_REQUIREMENTS.md`
- Single source of truth for IO semantics and special-value handling.

4. `docs/README.md` (this file)
- Docs navigation, responsibilities, and update rules.

## Appendix Pages

1. `docs/refactor_baseline.md` - Maintainability refactor boundary and gate.
2. `docs/troubleshooting.md` - Operational diagnosis and quick fixes.
3. `docs/memo_pending_translation_rules.md` - Unresolved business policy questions only.
4. `docs/terminology_rule_config_notes.md` - Terminology extractor config field notes.
5. `docs/sample_terminology_rules.json` - Sample terminology rule config.
6. `docs/archive/*` - Historical references only (links may not reflect current paths).

## Regression And Perf Commands

Core regression:

```bash
python scripts/run_regression_suite.py --with-golden
```

Optional lightweight performance baseline (report-only, non-blocking):

```bash
python scripts/run_perf_baseline.py
python scripts/run_regression_suite.py --with-perf
python scripts/run_regression_suite.py --with-perf --perf-baseline-json tests/perf/reports/<old>.json
```

## Recent Docs Changes

1. `IO_FORMAT_REQUIREMENTS.md` moved from repo root to `docs/IO_FORMAT_REQUIREMENTS.md`.
2. Core docs entry is now a 4-page model to reduce context fragmentation.

## Maintenance Rules

1. Keep architecture principles in `docs/ARCHITECTURE.md` only.
2. Keep dynamic current-state details in `docs/SESSION_DUMP.md` only.
3. Keep IO behavior details in `docs/IO_FORMAT_REQUIREMENTS.md` only.
4. Update docs in the same PR/commit as behavior changes.
5. Before committing broad text edits, run:

```bash
python scripts/check_text_encoding.py --root docs
```
