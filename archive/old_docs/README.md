# Archived Legacy Docs

This directory preserves documentation that was previously useful but no longer matches the active documentation structure.

## Why These Files Were Moved

- Several docs mixed architecture, runtime snapshot, testing policy, and troubleshooting in overlapping ways.
- Some files captured point-in-time refactor context rather than stable project guidance.
- The active source of truth now lives in:
  - `README.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/architecture.md`
  - `docs/development.md`
  - `docs/testing.md`
  - `docs/deployment.md`
  - `docs/decisions.md`

## Replacement Map

- `docs_README_2026-03-03.md`
  - Replaced by `README.md` and `docs/README.md`
- `docs_ARCHITECTURE_2026-03-03.md`
  - Replaced by `docs/architecture.md`
- `docs_IO_FORMAT_REQUIREMENTS_2026-03-03.md`
  - Replaced by `docs/io-contract.md`
- `docs_PRIVATE_TEST_DATA_POLICY_2026-03-03.md`
  - Replaced by `docs/testing.md`
- `docs_troubleshooting_2026-03-03.md`
  - Condensed into `docs/testing.md`
- `docs_SESSION_DUMP_2026-03-05.md`
  - Preserved as a runtime snapshot only, not a stable contract
- `docs_terminology_rule_config_notes_2026-03-05.md`
  - Background context for terminology work not yet promoted to a standalone active doc

## What Is Archived Here

- Prior canonical docs that were superseded by the new structure
- Runtime snapshots and troubleshooting notes preserved for context
- Historical refactor notes under `legacy_docs_archive/`

## Archive Notes

- `legacy_docs_archive/` contains older refactor planning artifacts from `docs/archive/2026-02-26/`.
- Keep archived material for context, but prefer linking active docs instead of editing or reviving these files as current guidance.
