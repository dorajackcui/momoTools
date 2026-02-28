# Memo: Pending Translation/Data Handling Decisions

Last updated: 2026-02-28
Audience: product/engineering decision makers for business semantics
Purpose: track unresolved business policy choices only
Out of scope: architecture, async model, logging infrastructure, or tooling design

## Scope Rule

This file stores unresolved business decisions only.

Do not place here:

1. Layering or architecture guidance (use `docs/ARCHITECTURE.md`).
2. Current runtime wiring snapshots (use `docs/SESSION_DUMP.md`).
3. Troubleshooting operations (use `docs/troubleshooting.md`).

## Locked Baseline (Already Implemented)

1. Fill mode toggle exists in:
- `master_to_target_single`
- `master_to_target_multi`
- `target_to_master_reverse`
2. Fill-blank rule source of truth:
- `core/kernel/excel_io.py:is_blank_value`
3. Post-process toggle exists for Master->target single/multi, default enabled, not persisted.

## Pending 1: Empty incoming content behavior

Question:

For matched rows where incoming content is empty string (`""`), should update clear target cell or keep existing value?

Options:

1. Allow clearing target cell with empty-string input.
2. Keep existing target cell when incoming content is empty-string.

Suggested acceptance cases:

1. Matched row + existing target text + incoming empty-string under overwrite mode.
2. Same under fill-blank-only mode.

## Pending 2: Numeric/display fidelity policy

Question:

Should output preserve logical value (`str(value)`) or preserve Excel displayed text/format?

Options:

1. Keep logical value standardization.
2. Preserve display-format text.

Suggested acceptance cases:

1. `0`, `1`, `1.0`, `00123`
2. Date-formatted and percentage-formatted cells.

## Related References

1. IO semantics detail: `docs/IO_FORMAT_REQUIREMENTS.md`
2. Current runtime snapshot: `docs/SESSION_DUMP.md`
3. Stable architecture principles: `docs/ARCHITECTURE.md`
