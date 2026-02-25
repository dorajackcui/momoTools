# Golden Regression Assets

This folder stores fixture definitions and reports for strict IO/format regression.

## Layout

- `manifest.template.json`: Template manifest for workbook comparison.
- `sample_inventory_template.md`: Template to track fixture coverage.
- `templates/`: Baseline/failure report templates.
- `reports/`: Generated reports from `scripts/run_golden_regression.py`.

## How To Run

```bash
python scripts/run_golden_regression.py --manifest tests/golden/manifest.template.json
```

Exit code is `0` if all cases pass, `1` if any case fails.
