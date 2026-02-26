# Memo: Pending Translation/Data Handling Decisions

Last updated: 2026-02-26
Owner: TBD
Status: Open

This file keeps only unresolved policy questions and currently locked baselines.

## Locked baseline (already implemented)

1. Fill mode toggle exists in:
   - `master_to_target_single`
   - `master_to_target_multi`
   - `target_to_master_reverse`
2. Fill-blank rule is fixed:
   - blank = `None`, empty string, whitespace-only string
   - source of truth = `core/kernel/excel_io.py:is_blank_value`
3. Post-process toggle (COM save) exists for Master -> small(single/multi), default enabled, not persisted.

## Pending 1: empty source/translation content behavior

Question:
- For matched rows where incoming content is empty-string (`""`), should update behavior clear existing target cell or keep existing value?

Current implementation tendency:
- values are passed through logical string flow; business intent for empty-string is not formally locked.

Decision needed:
- Option A: allow clearing target cell with empty-string input
- Option B: keep original target cell when incoming is empty-string

Suggested acceptance cases:
- matched row + target cell already has text + incoming empty-string
- verify behavior under both `覆盖` and `填空` modes

## Pending 2: number/string display fidelity

Question:
- Should output preserve logical value (`str(value)`), or preserve exact Excel displayed text/format?

Current implementation tendency:
- mostly logical value path; may differ from display formatting (e.g., `1`, `1.0`, formatted date/percentage).

Decision needed:
- Option A: keep logical value standardization
- Option B: preserve display-format text

Suggested acceptance cases:
- `0`, `1`, `1.0`, `00123`, date-formatted cell, percentage-formatted cell

## Related references

- Detailed IO behavior: `IO_FORMAT_REQUIREMENTS.md`
- Session snapshot: `docs/SESSION_DUMP.md`
- Historical notes archived under: `docs/archive/2026-02-26/`
