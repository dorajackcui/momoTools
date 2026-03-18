# Decisions

This document records stable product and engineering decisions that should not drift silently. Structural details live in `docs/architecture.md`, workbook semantics live in `docs/io-contract.md`, and validation commands live in `docs/testing.md`.

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
  - appended content cells are persisted as strings
  - when `key_only` is used, source rows with blank `match` are skipped
  - keeps first-processed duplicate source row for the same identity
- `Update Master`
  - dense-row overwrite behavior
  - allows new keys
  - uses `key_only`
  - content cells are persisted as strings, including match-column updates
  - match column is treated as updatable content
- `Update Content`
  - sparse non-blank overwrite behavior
  - existing keys only
  - uses `combined_key`
  - written content cells and unmatched-report content columns are persisted as strings
  - match column remains part of row identity, not a content target
  - every run exports an unmatched-entry detail report using the same `combined_key` match rule
- `Source+Translation`
  - remains an additive UI mode rather than replacing `Source Text` or `Translation`
  - keeps a fixed execution order: `Source Text` first, `Translation` second
  - does not roll back first-stage writes if the translation stage fails

## Terminology Decisions

- Terminology config version is currently `1`.
- `extractors` are required in terminology config.
- `compound_split` remains parser-compatible but is ignored by the runtime extraction stage.
- `terms_summary` distinguishes `body` and `suffix` term types.
- `relations_summary` includes both `cross_file` and `affix_group` style outputs.
