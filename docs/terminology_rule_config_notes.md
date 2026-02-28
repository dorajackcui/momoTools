# Terminology Rule JSON Notes

Sample file: `docs/sample_terminology_rules.json`

## 1. Top-level fields

- `version`
  - Must be `1`.
- `files` (optional)
  - Controls which Excel files are processed.
  - Supports list or comma-separated string.
  - Missing / empty / `*` / `all` means process all discovered Excel files.
- `versions` (optional)
  - Global row filter by the Excel `version` column.
  - Supports list or comma-separated string.
  - Missing / empty / `*` / `all` means process all versions.
- `affix_delimiters` (optional)
  - Delimiters used by affix relation extraction from raw terms.
  - Supports list or comma-separated string.
  - Default: `["·", ":"]`.
- `normalization`
  - Term normalization settings.
- `thresholds`
  - Review threshold settings.
- `extractors`
  - Extractor list, executed in order.

## 2. Breaking changes

- `compound_delimiters` is removed.
  - If present, config loading fails immediately.
  - Use `affix_delimiters` instead.
- Old relation semantics (`variant_of`, `has_head`, `has_suffix`, `head_suffix_pair`) are removed from relation summary output.

## 3. Relation model (current)

The relation summary now contains only two relation types:

1. `cross_file`
   - One row per deduplicated term that appears in at least 2 files.
   - Terms that appear in only 1 file are excluded.
2. `affix_group`
   - Built from extractor raw terms.
   - Split once by the leftmost matched delimiter from `affix_delimiters`.
   - Split parts are grouped even if they are not standalone terms in `terms_summary`.
   - Evaluated independently from `cross_file` filtering.
   - Exports both directions:
     - `affix_role = prefix_anchor`
     - `affix_role = suffix_anchor`

## 4. `relations_summary` columns (current)

- `relation_type`
- `evidence_count`
- `cross_term`
- `cross_files_count`
- `cross_files_list`
- `affix_role`
- `affix_anchor_term`
- `affix_related_count`
- `affix_related_list`
- `affix_delimiters`
- `notes`

## 5. Practical notes

- If `versions` is configured, input files must contain a `version` column (case-insensitive match, e.g. `Version` is accepted).
- `compound_split` extractor entries in config are still parsed, but runtime extraction ignores them.
- Recommended output inspection order:
  1. `terms_summary`
  2. `relations_summary`
  3. `review`
  4. `details`
