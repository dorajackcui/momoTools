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

Each case contains:

- `master.xlsx`: the starting workbook
- `updates/`: update files in a useful default order
- `expected/master_after_run.xlsx`: expected result after running with the files listed in order

If you need to regenerate the workbooks, run:

```powershell
.\scripts\python.cmd scripts\generate_update_master_manual_samples.py
```
