# Reverse Stats Manual Samples

This folder contains manual sample workbooks for validating the reverse updater stats fix in `core/reverse_excel_processor.py`.

Quick rerun command:

```powershell
.\scripts\python.cmd scripts\run_reverse_manual_samples.py
```

## Samples

### `01_precedence`

Purpose: verify that sorted target-file merge precedence is unchanged.

Expected result:

- Run reverse update with `master.xlsx` and the `targets/` folder.
- The master translation cell should become `from_b`.
- This confirms later sorted files still win for duplicate `key + match`.

### `02_read_failure`

Purpose: verify one unreadable target file does not block successful files.

Expected result:

- Run reverse update with `master.xlsx` and the `targets/` folder.
- `targets/a.xlsx` is a valid workbook and should still update the master to `from_good`.
- `targets/b.xlsx` is intentionally not a real Excel workbook even though it has the `.xlsx` suffix.
- The log window should contain `E_TARGET_READ` for `b.xlsx`.

## UI Settings

Use the reverse updater defaults:

- Target key column: `1`
- Target match column: `2`
- Target translation column: `3`
- Master key column: `2`
- Master match column: `3`
- Master translation column: `4`

Keep these options disabled unless you want to explore other cases:

- `仅填空（关闭=覆盖）`
- `允许写入空白值（谨慎）`
