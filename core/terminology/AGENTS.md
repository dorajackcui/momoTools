# AGENTS.md

## What This Directory Owns

`core/terminology/` is the staged terminology extraction pipeline: config loading, file discovery, candidate extraction, normalization, aggregation, relation building, and Excel export.

## Stable Rules

- Terminology config version is currently `1`.
- `extractors` are required in terminology config.
- `compound_split` remains parser-compatible but is ignored by the runtime extraction stage.
- Exported summaries must continue to distinguish `body` and `suffix` term types.
- `relations_summary` continues to cover both `cross_file` and `affix_group` relations.

If those rules change, update `docs/decisions.md`. If output sheet semantics change, update `docs/io-contract.md` when the change affects workbook contract expectations.

## Pipeline Notes

- Discovery and filtering happen before extraction.
- Runtime extraction currently builds only record and tag-span extractors.
- `compound_split` is carried for compatibility and later relation logic, not for direct runtime candidate extraction.
- Export schema changes are high risk because they can break downstream review spreadsheets and regression expectations.

## Modification Boundaries

- Keep UI path-state or form behavior out of this directory.
- Do not silently change exporter sheet names or summary columns without updating tests and docs.
- Prefer small pipeline-stage changes over broad processor branching.

## What To Re-Read Before Editing

- `docs/decisions.md`
- `docs/testing.md`
- `docs/sample_terminology_rules.json`
- `tests/test_terminology_processor.py`
- `tests/test_terminology_extractors.py`

## Minimum Verification

- `python -m unittest tests.test_terminology_processor tests.test_terminology_extractors`
- If controller/UI wiring changes:
  - `python -m unittest tests.test_ui_terminology_controller`
