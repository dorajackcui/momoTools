# Deployment

## Runtime Target

The application is primarily intended for Windows desktop use. Some processing paths rely on Microsoft Excel through COM automation, so packaging and release validation should assume a Windows environment.

## Packaging

The repository includes a PyInstaller spec file:

- `TM_builder.spec`

The spec packages:

- `app.py` as the entry script
- `win32com.client` as a hidden import
- `刷表.ico` as the bundled icon asset
- a windowed executable named `TM_builder`

## Build Notes

The current repository documents packaging configuration but does not include a canonical scripted release pipeline in `docs/`. If you need to build a distributable executable, use `TM_builder.spec` as the starting point and validate the resulting app on a Windows machine with Excel-dependent workflows.

## Pre-Release Checks

Before packaging or sharing a build:

```bash
python scripts/run_regression_suite.py --with-golden
```

Optional diagnostics:

```bash
python scripts/run_perf_baseline.py
python -m unittest tests.test_private_data_skip_blank_write -v
```

## Operational Constraints

- COM-dependent features require Microsoft Excel installed for the target user.
- Non-COM workbook paths can run without Excel automation, but behavior differs for compatibility repair and post-processing flows.
- The app keeps logs in memory for the current session only.

## Gaps

The repo does not currently document:

- an official installer workflow
- CI/CD release automation
- versioning or release-note conventions

Those gaps should be clarified before formalizing deployment automation.
