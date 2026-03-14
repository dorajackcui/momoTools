# IO Contract (Canonical)

Last updated: 2026-03-03
Audience: agents and engineers touching processor behavior
Owns: Excel read/match/write semantics for update flows
Does not own: UI workflow and architecture decisions

## 1) Covered Flows

1. `master -> target (single)` in `core/excel_processor.py`
2. `master -> target (multi)` in `core/multi_column_processor.py`
3. `target -> master (reverse)` in `core/reverse_excel_processor.py`
4. `master update suite` in `core/master_merge_processor.py`

## 2) Shared Value Rules (`core/kernel/excel_io.py`)

### 2.1 Combined key

`build_combined_key(key_value, match_value, separator='|')`

1. Key and match are normalized with `safe_to_str(..., strip=True)`.
2. `None` becomes `""`.
3. If either normalized part is empty, row is skipped (invalid combined key).

### 2.2 Blank detection

`is_blank_value(value)` is true only when:

1. `value is None`
2. `value` is string and `value.strip() == ""`

False for: `0`, `0.0`, `float('nan')`, `"nan"`.

### 2.3 String conversion

`safe_to_str(value, strip=...)`:

1. `None -> ""`
2. Non-string -> `str(value)`
3. `strip=False` preserves leading/trailing whitespace

### 2.4 Blank write policy

`allow_blank_write`:

1. Default is `False`.
2. `False`: blank content (by `is_blank_value`) is skipped, not written.
3. `True`: blank content can be written (including clearing cells).
4. Does not change key-match rules or `fill_blank_only` logic.

## 3) Flow Semantics

### 3.1 Master -> target (single)

1. Build `master_dict[combined_key]`.
2. On key match:
- overwrite: always write
- fill-blank-only: write only if target cell is blank by `is_blank_value`
3. Blank content handling follows `allow_blank_write`.
4. `post_process_enabled` affects only COM post-process step.

### 3.2 Master -> target (multi)

1. Same match logic as single mode.
2. Write per configured column.
3. `fill_blank_only` evaluated per target cell.
4. Missing master content columns are treated as `""`.
5. Blank content handling is per cell via `allow_blank_write`.

### 3.3 Target -> master (reverse)

1. Scan target files from row 2.
2. Content normalized with `safe_to_str(..., strip=False)`.
3. Update master on combined key match.
4. `fill_blank_only` checks master destination cell.
5. Blank content handling follows `allow_blank_write`.
6. Merge order is deterministic: sorted path order, later file overrides earlier.

### 3.4 Master update suite (shared engine)

1. Inputs:
- one master file
- one update folder with multiple files (same headers)
- `key_col`, `match_col`
- `last_update_col` (shared upper bound for both master and source scanning; default is column K / 1-based 11)
- source priority order (top is processed first)
2. Row identity can be policy-driven:
- `combined_key`: `key + '|' + match` after normalization, both must be non-blank
- `key_only`: normalized `key` only, `match` can be blank
3. Source-row candidate rules:
- `Merge Masters` (append-only): source rows are treated as complete rows (no per-cell blank filtering in merge planning).
- `Update Master`: source rows are treated as complete rows (no per-cell blank filtering; blank values are valid update values).
- `Update Content`: only non-blank source cells are considered update candidates.
4. Modes and policies:
- `Merge Masters`: `fill_blank_only + allow_new_key`; key policy is UI-selectable (default `combined_key`), and execution is append-only by default (assume existing master rows are already filled)
- `Update Master`: `overwrite by dense row values` (`overwrite_non_blank`) + `allow_new_key`; key policy is fixed `key_only`
- `Update Content`: `overwrite with non-blank values` (`overwrite_non_blank`) + `existing_key_only`; key policy is fixed `combined_key`
- Compatibility note: policy token `overwrite_non_blank` is kept stable for API/dispatcher compatibility; concrete write semantics are mode-specific (`Update Master` dense vs `Update Content` sparse).
5. Match-column write behavior:
- In `Merge Masters` append-only mode, `match_col` is written only when appending a new row; existing master rows are not modified.
- In `Update Master` (`key_only`), `match_col` is treated as content and can be updated.
- In `combined_key` overwrite mode (`Update Content`), `match_col` is reserved for matching and excluded from content update columns.
6. Priority winner in overwrite modes:
- `last_processed` (later processed file overrides earlier processed file)
7. New key handling:
- `allow_new_key`: append as new row
- `existing_key_only`: skip new key and count as skipped
8. Duplicate keys in master:
- In overwrite modes (`Update Master` / `Update Content`), all duplicate rows for the same key are synchronized to the merged value.
- In `Merge Masters` append-only mode, existing duplicate rows are not modified.
9. Duplicate identities in source updates:
- In `Merge Masters` append-only mode, duplicate identities use first-processed full row (`first_processed` wins for the whole row).
- In `Update Master` dense mode, duplicate identities use last-processed full row (`last_processed` wins for the whole row).
- In `Update Content` sparse mode, duplicate identities follow per-cell non-blank overwrite (`last_processed` per touched cell).

### 3.5 Performance Notes

For `Merge Masters` (append-only default):

1. Source candidates are aggregated first.
2. Master scan reads only columns needed to build row identity (key/match).
3. Existing master rows are not opened for per-cell update planning.
4. Read-write workbook open/save is skipped when there are no new keys to append.
5. Stage timing summary is logged for observability.

For `Update Master` (dense-row overwrite):

1. Source candidates are aggregated first.
2. Master scan uses read-only planning.
3. Existing matched rows are planned against full content-column scope (no touched-column sparse pruning).
4. Read-write workbook open/save is skipped when planned updates and new rows are both empty.
5. Stage timing summary is logged for observability.

For `Update Content` (sparse overwrite):

1. Source candidates are aggregated first.
2. Master scan uses read-only planning.
3. Read-write workbook open/save is skipped when planned updates and new rows are both empty.
4. Candidate touched columns are tracked to avoid full content-column loops on matched rows.
5. Stage timing summary is logged for observability.

## 4) Special-Value Matrix

| Raw value | Key/match normalization | Written content | Blank under `is_blank_value` |
| --- | --- | --- | --- |
| `None` | `""` | `""` | Yes |
| `""` | `""` | `""` | Yes |
| `"   "` | `""` | preserved with `strip=False` | Yes |
| `0` / `0.0` | `"0"` / `"0.0"` | `"0"` / `"0.0"` | No |
| `float('nan')` | `"nan"` | `"nan"` | No |
| `"nan"` | `"nan"` | `"nan"` | No |

## 5) Change Rule

If IO behavior changes, update this file in the same change set.
