# AGENTS.md

## What This Directory Owns

`core/master_update/` owns the policy-based engine behind `Merge Masters`, `Source Text`, `Translation`, and the composed `Source+Translation` flow. It is the implementation home for row identity policy, source collection, executor behavior, and mode-specific wiring for update-master workflows.

## Canonical Docs To Update

- `docs/io-contract.md`
- `docs/decisions.md`
- `docs/testing.md`
- `docs/architecture.md` when orchestration boundaries or compatibility surfaces move

## Change Routing

- Row identity, blank handling, match-column behavior, or mode-specific write semantics -> `docs/io-contract.md`
- Stable mode policy for `Merge Masters`, `Source Text`, `Translation`, or `Source+Translation` -> `docs/decisions.md`
- Dispatcher ownership, compatibility surface, or UI-facing orchestration boundary changes -> `docs/architecture.md`
- Minimum verification or regression-routing changes -> `docs/testing.md`
- Directory-only editing guidance, routing, or minimum verification for `core/master_update/` -> `core/master_update/AGENTS.md`

## Local Invariants

- Detailed workbook semantics for update-master flows are owned by `docs/io-contract.md`. Owner: `docs/io-contract.md`
- Durable mode guarantees for `Merge Masters`, `Source Text`, `Translation`, and `Source+Translation` are owned by `docs/decisions.md`. Owner: `docs/decisions.md`
- Prefer policy, collector, or executor changes here over branching update-master behavior in controllers. Owner: local
- Keep UI-specific validation and dialog behavior out of this directory. Owner: local

## Modification Boundaries

- Keep controller-facing compatibility stable unless an explicit migration is planned.
- Do not redefine workbook semantics in controllers or UI glue.
- Treat source collection, row identity, and executor behavior as core responsibilities of this directory.
- If you add a new update-master mode, route it through `docs/README.md` and the relevant canonical docs in the same change set.

## Minimum Verification

- `.\scripts\python.cmd -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher`
- If the change touches UI-facing master-update wiring: `.\scripts\python.cmd -m unittest tests.test_ui_update_master_views tests.test_ui_merge_masters_view`
- If the change affects workbook semantics: `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden`
