# Update Master Manual Samples

This folder contains hand-checkable Excel samples for the `Master Update` group:

- `source_text/`
  - Use the `Source Text` tab.
  - UI columns: `Key col = 2`, `Match col = 3`, `Last update col = 11`
  - Expected behavior:
    - row identity is `key` only
    - new keys can be appended
    - later processed files overwrite earlier files
    - blank values from update files are valid writes
- `translation/`
  - Use the `Translation` tab.
  - UI columns: `Key col = 2`, `Match col = 3`, `Last update col = 11`
  - Expected behavior:
    - row identity is `key + source text`
    - only existing rows are updated
    - only non-blank update cells are written
    - same key with changed source text does not match
- `source_text_content_corners/`
  - Use the `Source Text` tab.
  - UI columns: `Key col = 2`, `Match col = 3`, `Last update col = 11`
  - Focus:
    - update workbooks keep their original numeric/date inputs for inspection
    - expected output workbooks persist content cells as strings
    - literal text `"None"` stays `"None"`
    - literal text `"NaN"` stays `"NaN"`
    - `0` becomes text `"0"` and `0.0` becomes text `"0.0"` in the expected master workbook
    - decimal values become text such as `"12.34"` in the expected master workbook
    - percentage samples use numeric `0.25` in the update workbook and text `"0.25"` in the expected master workbook
    - fraction samples use numeric `1/3` with a fraction number format in the update workbook and text `"0.3333333333333333"` in the expected master workbook
    - date samples use an Excel date value in the update workbook and the plain `str(value)` result in the expected master workbook, such as `"2026-03-16 00:00:00"`
    - blank content clears existing values in dense `Update Master` mode
    - whitespace-only content is preserved as content in dense mode
- `translation_content_corners/`
  - Use the `Translation` tab.
  - UI columns: `Key col = 2`, `Match col = 3`, `Last update col = 11`
  - Focus:
    - update workbooks keep their original numeric/date inputs for inspection
    - expected output workbooks persist content cells as strings
    - literal text `"None"` stays `"None"`
    - literal text `"NaN"` stays `"NaN"`
    - `0` becomes text `"0"` and `0.0` becomes text `"0.0"` in the expected master workbook
    - decimal values become text such as `"12.34"` in the expected master workbook
    - percentage samples use numeric `0.25` in the update workbook and text `"0.25"` in the expected master workbook
    - fraction samples use numeric `1/3` with a fraction number format in the update workbook and text `"0.3333333333333333"` in the expected master workbook
    - date samples use an Excel date value in the update workbook and the plain `str(value)` result in the expected master workbook, such as `"2026-03-16 00:00:00"`
    - blank content does not overwrite existing values in sparse `Update Content` mode
    - whitespace-only content is treated as blank and skipped in sparse mode

These corner-case samples use the literal text `"NaN"`. A Python `float('nan')` is not a stable manual-sample value for `.xlsx` round-trips under `openpyxl`, because it reads back as a blank cell.

Each case contains:

- `master.xlsx`: the starting workbook
- `updates/`: update files in a useful default order
- `expected/master_after_run.xlsx`: expected result after running with the files listed in order

If you need to regenerate the workbooks, run:

```powershell
.\scripts\python.cmd scripts\generate_update_master_manual_samples.py
```
