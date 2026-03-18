# AGENTS.md

## What This Directory Owns

`core/terminology/` owns the staged terminology extraction pipeline: config loading, file discovery, candidate extraction, normalization, aggregation, relation building, review output, and Excel export.

## Canonical Docs To Update

- `docs/decisions.md`
- `docs/io-contract.md` when export workbook expectations change
- `docs/testing.md`
- `docs/architecture.md` when orchestration or integration boundaries move

## Change Routing

- Terminology config compatibility or durable terminology-output guarantees -> `docs/decisions.md`
- Export sheet or column semantics that affect downstream workbook expectations -> `docs/io-contract.md`
- Pipeline integration or orchestration boundary changes -> `docs/architecture.md`
- Minimum verification changes -> `docs/testing.md`
- Directory-only editing guidance, routing, or minimum verification for `core/terminology/` -> `core/terminology/AGENTS.md`

## Local Invariants

- Terminology config compatibility and durable output guarantees are owned by `docs/decisions.md`. Owner: `docs/decisions.md`
- Workbook-facing export contract changes belong in `docs/io-contract.md` when downstream spreadsheets rely on them. Owner: `docs/io-contract.md`
- Export schema changes are high risk because they can break review spreadsheets and regression expectations. Owner: local
- Prefer focused pipeline-stage changes over broad processor branching. Owner: local

## Modification Boundaries

- Keep UI path-state or form behavior out of this directory.
- Do not silently change exporter sheet names or summary columns without updating docs and tests.
- Keep config parsing, extraction, aggregation, relation building, and export responsibilities in this directory.
- If runtime work adds a new cross-directory integration point, update `docs/architecture.md` and this local contract in the same change set.

## Minimum Verification

- `.\scripts\python.cmd -m unittest tests.test_terminology_processor tests.test_terminology_extractors`
- If controller or UI wiring changes: `.\scripts\python.cmd -m unittest tests.test_ui_terminology_controller`
