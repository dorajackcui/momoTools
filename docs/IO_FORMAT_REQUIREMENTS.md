# IO Contract (Canonical)

Last updated: 2026-03-03
Audience: agents and engineers touching processor behavior
Owns: Excel read/match/write semantics for update flows
Does not own: UI workflow and architecture decisions

## 1) Covered Flows

1. `master -> target (single)` in `core/excel_processor.py`
2. `master -> target (multi)` in `core/multi_column_processor.py`
3. `target -> master (reverse)` in `core/reverse_excel_processor.py`

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
