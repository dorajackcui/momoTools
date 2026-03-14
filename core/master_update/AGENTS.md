# AGENTS.md

## What This Directory Owns

`core/master_update/` contains the policy-based engine behind the three update-master flows surfaced in the UI:

- `Merge Masters`
- `Update Master`
- `Update Content`

Treat this directory as the implementation home for row identity policy, source collection, executor behavior, and mode-specific write rules for update-master workflows.

## Stable Rules

- `Merge Masters`
  - append-oriented
  - allows new keys
  - supports `combined_key` or `key_only`
  - duplicate source identities keep the first processed full row
- `Update Master`
  - dense-row overwrite
  - allows new keys
  - identity is fixed to `key_only`
  - blank values are valid update values
- `Update Content`
  - sparse non-blank overwrite
  - existing keys only
  - identity is fixed to `combined_key`

If any of those rules change, update both `docs/io-contract.md` and `docs/decisions.md`.

## Modification Boundaries

- Keep IO/value semantics aligned with `docs/io-contract.md`.
- Do not move UI-specific validation into this directory.
- Keep controller-facing compatibility behavior stable unless an explicit migration is planned.
- Prefer changing policies, collectors, or executors here instead of branching behavior in controllers.

## What To Re-Read Before Editing

- `docs/io-contract.md` for row identity, blank handling, and match-column semantics
- `docs/decisions.md` for stable mode policies
- `tests/test_master_merge_processor.py`
- `tests/test_master_merge_dispatcher.py`

## Minimum Verification

- `python -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher`
- If the change touches UI-facing master-update wiring:
  - `python -m unittest tests.test_ui_update_master_views tests.test_ui_merge_masters_view`
- If the change affects workbook semantics:
  - `python scripts/run_regression_suite.py --with-golden`
