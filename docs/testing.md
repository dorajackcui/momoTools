# Testing

## Test Stack

The repository uses Python `unittest`.

Primary test areas:

- `tests/test_*.py`: unit and integration-style regression tests
- `tests/test_ui_*.py`: Tkinter UI and controller contract tests
- `tests/golden/`: workbook fixture manifests and comparison templates
- `tests/_private_data/`: ignored local-only fixtures for production-like validation

## Prerequisites And Environment Caveats

- The canonical test environment installs `requirements.txt`.
- Missing `pandas` can cause processor and exporter tests to fail during module import.
- Missing `pywin32` no longer blocks app-module import, but COM-backed runtime tests still require it when exercising the real COM path.
- Full COM confidence still belongs on Windows with Microsoft Excel installed.

Check environment gaps first if failures appear before test execution starts.

All commands below use `.\scripts\python.cmd`, which prefers a repo-local Python and avoids depending on PATH access. In a normal unsandboxed shell, `python ...` remains equivalent if your environment is already configured.

## Standard Commands

Run the app smoke-oriented subset:

```powershell
.\scripts\python.cmd -m unittest tests.test_app_smoke tests.test_app_component_registry tests.test_app_log_console
```

Run UI-focused tests:

```powershell
.\scripts\python.cmd -m unittest discover -s tests -p "test_ui_*.py"
```

Run task-runner and controller wiring checks:

```powershell
.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_task_runner
```

Run folder-precheck and file-enumeration coverage for tool flows:

```powershell
.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_com_processors tests.test_core_processors_regression
```

Run the canonical regression suite:

```powershell
.\scripts\python.cmd scripts/run_regression_suite.py --with-golden
```

Run golden regression directly:

```powershell
.\scripts\python.cmd scripts/run_golden_regression.py --manifest tests/golden/manifest.sample.json
```

Run the optional private-data regression:

```powershell
.\scripts\python.cmd -m unittest tests.test_private_data_skip_blank_write -v
```

Run the performance baseline report:

```powershell
.\scripts\python.cmd scripts/run_perf_baseline.py
```

## Quick Checks

- Docs-only changes:

```powershell
.\scripts\python.cmd scripts/check_text_encoding.py --root docs
```

- COM dependency regression around import safety:

```powershell
.\scripts\python.cmd -m unittest tests.test_app_smoke tests.test_com_processors
```

## Change-Oriented Verification Matrix

| Change type | Minimum verification |
| --- | --- |
| Docs-only | `.\scripts\python.cmd scripts/check_text_encoding.py --root docs` |
| UI / controller changes | `.\scripts\python.cmd -m unittest discover -s tests -p "test_ui_*.py"` and `.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_task_runner` |
| Folder precheck / processor file-list changes | `.\scripts\python.cmd -m unittest tests.test_ui_controllers tests.test_com_processors tests.test_core_processors_regression` |
| IO semantics / processor behavior | `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden` |
| Terminology changes | `.\scripts\python.cmd -m unittest tests.test_terminology_processor tests.test_terminology_extractors tests.test_ui_terminology_controller` |
| Update-master changes | `.\scripts\python.cmd -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher tests.test_ui_update_master_views tests.test_ui_merge_masters_view` |
| Packaging / release work | `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden` plus a Windows packaging check from `TM_builder.spec` |

If workbook IO behavior changes, include regression coverage and run the golden suite.

## When To Add Tests

Add or update tests when changing:

- processor semantics
- controller validation or dispatch behavior
- public compatibility surfaces
- UI view contracts or shared widgets
- regression scripts and reports

## Golden Regression Notes

`tests/golden/` stores committed minimal fixtures and manifest templates for workbook comparisons.

Key files:

- `tests/golden/manifest.sample.json`: executable sample manifest
- `tests/golden/manifest.template.json`: template for new fixture sets
- `tests/golden/templates/`: report templates

The golden regression script exits with `0` on success and `1` on failure.

## Private Data Policy

- Store local production-like samples only under `tests/_private_data/`.
- This directory is ignored by Git.
- Local hooks can block accidental commit or push of restricted files.
- Private-data tests must use temporary copies and must not write back into `tests/_private_data/`.
- The private-data regression test auto-skips when required local fixtures are missing.

## Failure Triage First

Check these before debugging business logic:

- Missing Python packages such as `pandas`
- Missing `pywin32` for COM-backed code paths
- Files locked by Excel or another process
- Wrong column mapping
- Blank writes skipped because `allow_blank_write` is disabled
- No visible logs because no task was started or the session log buffer is empty

Historical troubleshooting notes were archived under [archive/old_docs/README.md](../archive/old_docs/README.md).
