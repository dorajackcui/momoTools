# Terminology Rule Config Contract

Last updated: 2026-03-03
Audience: engineers configuring terminology extractor
Owns: supported JSON fields and compatibility behavior

Sample: `docs/sample_terminology_rules.json`

## 1) Top-level Fields

1. `version`
- Must be `1`.

2. `files` (optional)
- List or comma-separated string.
- Empty / missing / `*` / `all` means process all discovered Excel files.

3. `versions` (optional)
- List or comma-separated string.
- Empty / missing / `*` / `all` means process all versions.
- If configured, input must contain a `version` column (case-insensitive name accepted).

4. `affix_delimiters` (optional)
- List or comma-separated string.
- Default: `["\u00B7", ":"]` (middle dot + colon).

5. `normalization` (optional), `thresholds` (optional), `extractors` (required)
- `normalization` and `thresholds` can be omitted (loader uses defaults).
- `extractors` must be a non-empty list.

## 2) Compatibility and Removed Fields

1. Removed and hard-fail:
- `compound_delimiters`
- `record_rule.conditions`
- `record_rule.version`

2. Compatibility aliases:
- `tag_span.open_tags` is preferred.
- `tag_span.open_tag` is still accepted.
- `tag_span.close_tags` defaults to `["</tag>", "</>"]`.

3. `compound_split` extractor:
- Parser still accepts it for compatibility.
- Runtime extractor stage ignores it (relation stage uses raw-term split by `affix_delimiters`).

## 3) Current Relation Model

`relations_summary` only emits:

1. `cross_file`
- Deduplicated terms appearing in at least 2 files.

2. `affix_group`
- Built from raw extracted terms.
- Split by first matched delimiter in `affix_delimiters`.
- Emits both `prefix_anchor` and `suffix_anchor`.

## 4) `relations_summary` Columns

`relation_type`, `evidence_count`, `cross_term`, `cross_files_count`, `cross_files_list`, `affix_role`, `affix_anchor_term`, `affix_related_count`, `affix_related_list`, `affix_delimiters`, `notes`.
