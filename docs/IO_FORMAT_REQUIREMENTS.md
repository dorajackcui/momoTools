# IO Format Requirements (Current Implementation)

Last updated: 2026-02-28
Audience: agents and engineers touching Excel read/write behavior
Purpose: define current IO semantics and special-value handling rules
Out of scope: UI flow, architecture rationale, and unresolved product policy decisions

## 1) Scope

This document describes current behavior for the three main data-update flows:

1. `master -> target (single)` in `core/excel_processor.py`
2. `master -> target (multi)` in `core/multi_column_processor.py`
3. `target -> master (reverse)` in `core/reverse_excel_processor.py`

## 2) Shared Rules (Source Of Truth)

Source module: `core/kernel/excel_io.py`

### 2.1 Key construction

Function: `build_combined_key(key_value, match_value, separator='|')`

1. Uses `safe_to_str(..., strip=True)` for both key and match values.
2. `None` is converted to `""`.
3. If either normalized key or match is empty, combined key is invalid and row is skipped.

### 2.2 Blank detection (for `fill_blank_only`)

Function: `is_blank_value(value)`

Blank is only:

1. `value is None`
2. string with `value.strip() == ""`

Not blank:

1. `0` / `0.0`
2. `float('nan')`
3. `"nan"`

### 2.3 Stringification

Function: `safe_to_str(value, strip=...)`

1. `None -> ""`
2. Non-string values are converted by `str(value)`.
3. With `strip=False`, leading/trailing whitespace is preserved.

## 3) Flow Semantics

### 3.1 Master -> target (single)

1. Master values are read into `master_dict[combined_key]`.
2. For matched target rows:
   1. overwrite mode: always write matched value
   2. fill-blank-only mode: write only if target update cell is blank by `is_blank_value`
3. `post_process_enabled` only controls COM post-process; it does not change business match/update decisions.

### 3.2 Master -> target (multi)

1. Same matching logic as single mode.
2. Updates are applied per target column across configured column count.
3. `fill_blank_only` is evaluated per target cell.
4. Missing master content columns are treated as `""`.

### 3.3 Target -> master (reverse)

1. Target files are scanned from row 2.
2. Target content values are normalized with `safe_to_str(..., strip=False)`.
3. Master rows are updated on combined key match.
4. `fill_blank_only` checks blank state on the master update cell.
5. Merge precedence is deterministic:
   1. target file list is sorted by path
   2. merge follows sorted order
   3. later file in sorted order overrides earlier value for same key

## 4) Special-Value Matrix

| Raw value | As key/match input | As written content | Treated blank in `fill_blank_only` |
| --- | --- | --- | --- |
| `None` | `""` (invalid key component) | `""` | Yes |
| `""` | empty (invalid key component) | `""` | Yes |
| `"   "` | stripped to empty (invalid key component) | preserved with `strip=False` | Yes |
| `0` / `0.0` | `"0"` / `"0.0"` | `"0"` / `"0.0"` | No |
| `float('nan')` | `"nan"` | `"nan"` | No |
| `"nan"` | `"nan"` | `"nan"` | No |

## 5) Notes

1. Current behavior is implementation-accurate, not policy-ideal.
2. Policy-level open questions stay in `docs/memo_pending_translation_rules.md`.
3. If IO behavior changes, update this file in the same change set.
