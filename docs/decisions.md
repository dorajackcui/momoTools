# Decisions

## Current Source of Truth

This directory is the canonical home for active project documentation. Historical notes, snapshots, and superseded docs live under `archive/old_docs/`.

## Stable Design Decisions

- Preserve workbook-processing behavior unless a business-rule change is explicitly approved.
- Keep `controllers.py` and `ui_components.py` as compatibility layers.
- Enforce a layered architecture: `ui -> controller_modules -> core`.
- Run one processing task at a time through the task runner.

## Processing Semantics

- `key + match` is the default row identity for master-to-target style updates.
- Excel cell values follow the normalization and blank-detection rules in `docs/io-contract.md`.
- Blank values are skipped by default because `allow_blank_write=False`.
- `fill_blank_only` and `overwrite` remain distinct modes and must not silently change behavior.
- Reverse update order is deterministic: sorted target paths, later files override earlier ones.

## Update-Master Mode Policies

- `Merge Masters`
  - append-oriented flow
  - allows new keys
  - supports `combined_key` or `key_only`
  - keeps first-processed duplicate source row for the same identity
- `Update Master`
  - dense-row overwrite behavior
  - allows new keys
  - uses `key_only`
  - match column is treated as updatable content
- `Update Content`
  - sparse non-blank overwrite behavior
  - existing keys only
  - uses `combined_key`
  - match column remains part of row identity, not a content target

## Terminology Decisions

- Terminology config version is currently `1`.
- `extractors` are required in terminology config.
- `compound_split` remains parser-compatible but is ignored by the runtime extraction stage.
- `terms_summary` distinguishes `body` and `suffix` term types.
- `relations_summary` includes both `cross_file` and `affix_group` style outputs.

## Documentation Rules

- Update the owning doc in the same change set when behavior changes.
- Prefer one clear source of truth over repeated copies of the same rule.
- Keep detailed Excel value semantics in `docs/io-contract.md` instead of duplicating them elsewhere.
- Move uncertain or superseded narrative into `archive/old_docs/` instead of deleting it.

## Known Unclear Areas

- There is no documented release-management process beyond the PyInstaller spec.
- There is no documented lint or typecheck toolchain beyond syntax compilation.
- Session-specific runtime notes existed previously, but not all of them represent stable guarantees; they were archived rather than carried forward as canonical docs.
