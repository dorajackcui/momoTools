# Terminology Rule Config Contract

Last updated: 2026-03-05
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

## 3) Current Term Model (`terms_summary`)

`terms_summary` is a deduplicated term set table with 2 term types:

1. `body`
- Prefix/body term from split results.
- Terms without delimiters are included as `body`.

2. `suffix`
- Suffix term from split results.
- Must keep the split delimiter (`\u00B7` or `:`) in the displayed term text.

Split behavior:
- Split by first matched delimiter in `affix_delimiters`.
- `body` is left side of delimiter.
- `suffix` is `delimiter + right side` (preserve original delimiter marker and raw style).

Dedup/display behavior:
- Dedup key follows normalization settings.
- Dedup dimension is `(term_type, dedup_key)`.
- Display term uses the first seen raw value.

## 4) Current Relation Model (`relations_summary`)

`relations_summary` emits:

1. `cross_file`
- Deduplicated terms appearing in at least 2 files.

2. `affix_group`
- Built from raw extracted terms.
- Uses first-delimiter split.
- Emits both directions:
- `prefix_anchor`: `body -> suffix set`
- `suffix_anchor`: `suffix -> body set`

## 5) Output Columns

`terms_summary` columns:
- `term_id`, `term_type`, `term_norm`, `occurrences_count`, `files_count`, `files_list`, `keys_count`, `keys_list`, `first_extractor`, `is_low_confidence`, `review_reasons`.

`relations_summary` columns:
- `relation_type`, `evidence_count`, `cross_term`, `cross_files_count`, `cross_files_list`, `affix_role`, `affix_anchor_term`, `affix_related_count`, `affix_related_list`, `affix_delimiters`, `notes`.

## 6) Runtime Observability

Processor logs include:

1. Config snapshot
- config `path`, effective `versions`, effective `files`.

2. Stage counters
- discovered files, selected files
- `rows_scanned`
- `rows_skipped_by_version`
- candidate / normalized / body term / suffix term / relation / review counts.

3. Stage timings (`timings_ms`)
- `config`, `discovery`, `extract`, `aggregate`, `export`, `total`.

