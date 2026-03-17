# Excel IO Contract

## Purpose

This document is the canonical source of truth for Excel read, match, normalization, and write behavior. If workbook IO semantics change, update this file in the same change set.

## Scope

Covered flows:

- `core/excel_processor.py`
- `core/multi_column_processor.py`
- `core/reverse_excel_processor.py`
- `core/master_merge_processor.py`
- shared helpers under `core/kernel/excel_io.py`

## Core Principle

Workbook cell values follow a "what you see is what you write" bias:

- processor values are normalized into strings through shared helpers
- `None` is not preserved as a special output token; it becomes `""`
- non-string values are converted with `str(value)`
- whitespace preservation depends on the calling flow and `strip` setting

The system does not keep a separate escaped representation for `None`, `NaN`, or blank-looking values.

## Shared Value Rules

### `safe_to_str(value, strip=...)`

- `None -> ""`
- strings stay strings
- non-string values become `str(value)`
- `strip=True` trims leading and trailing whitespace
- `strip=False` preserves leading and trailing whitespace

### `is_blank_value(value)`

A value is blank only when:

- `value is None`
- `value` is a string and `value.strip() == ""`

These are not blank:

- `0`
- `0.0`
- `float('nan')`
- `"nan"`

### Combined key normalization

`build_combined_key(key_value, match_value, separator='|')`:

- normalizes both parts with `safe_to_str(..., strip=True)`
- turns `None` into `""`
- treats either empty side as an invalid combined key

## Special-Value Matrix

| Raw value | Normalized key or match | Written content | Blank |
| --- | --- | --- | --- |
| `None` | `""` | `""` | Yes |
| `""` | `""` | `""` | Yes |
| `"   "` | `""` with `strip=True` | preserved with `strip=False` | Yes |
| `0` / `0.0` | `"0"` / `"0.0"` | `"0"` / `"0.0"` | No |
| `float('nan')` | `"nan"` | `"nan"` | No |
| `"nan"` | `"nan"` | `"nan"` | No |

## Blank Write Policy

`allow_blank_write` controls whether blank content may be written:

- default is `False`
- when `False`, blank content is skipped and existing target content is left unchanged
- when `True`, blank content may be written, including clearing cells
- this does not change key matching or `fill_blank_only` behavior

## Flow Semantics

### Master to target: single-column

- rows are matched by combined key
- `overwrite` always writes matched content
- `fill_blank_only` writes only when the destination cell is blank
- blank content follows `allow_blank_write`
- `post_process_enabled` affects only the COM post-process step

### Master to target: multi-column

- uses the same key-match behavior as single-column mode
- writes one configured content cell at a time
- `fill_blank_only` is evaluated per destination cell
- missing source columns are treated as `""`
- blank content follows `allow_blank_write` per cell

### Target to master: reverse update

- scans target files from row 2
- normalizes content with `safe_to_str(..., strip=False)`
- updates master rows on combined-key match
- `fill_blank_only` checks the destination cell in the master workbook
- blank content follows `allow_blank_write`
- processing order is deterministic: sorted paths, later files override earlier ones

### Master update suite

Inputs:

- one master workbook
- one update folder
- `key_col`
- `match_col`
- `last_update_col`
- source priority order

Supported row identity policies:

- `combined_key`
- `key_only`

Mode behavior:

- `Merge Masters`
  - append-oriented flow
  - source rows are treated as complete rows
  - allows new keys
  - default identity is `combined_key`, with UI support for `key_only`
  - when `key_only` is selected, source rows still require a non-blank `match_col` value; rows with blank match cells are skipped instead of appended
  - duplicate source identities keep the first processed full row
- `Update Master`
  - dense-row overwrite
  - blank values are valid update values
  - allows new keys
  - identity is fixed to `key_only`
  - duplicate source identities keep the last processed full row
- `Update Content`
  - sparse non-blank overwrite
  - existing keys only
  - identity is fixed to `combined_key`
  - duplicate source identities follow last-processed overwrite per touched cell
  - exports an unmatched-entry Excel report for every run using the same `combined_key` match rule
  - report rows are emitted per unmatched source identity and include `key`, `match`, source file, and expanded content columns
- `Source+Translation`
  - composed pipeline flow
  - shares one master workbook and one `key_col` / `match_col` / `last_update_col` setting set
  - takes separate update folders and priority orders for the `Source Text` and `Translation` stages
  - runs `Update Master` semantics first, then `Update Content` semantics
  - if the second stage fails, first-stage master writes are not rolled back

Match-column behavior:

- in `Merge Masters`, `match_col` is written only for appended rows
- in `Merge Masters` with `key_only`, `match_col` is still a required non-blank source field for row admission
- in `Update Master`, `match_col` is treated as updatable content
- in `Update Content`, `match_col` stays part of row identity and is not updated as content

## Performance-Related Semantics

- processors aggregate source candidates before applying writes
- read-write workbook open/save is skipped when there is no effective work to apply
- update-master flows log stage timing summaries for observability

## Change Rule

- update this document whenever Excel value normalization, blank handling, matching rules, or mode-specific write behavior changes
- when changing these rules, run `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden`
