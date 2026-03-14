# Development

## Environment Matrix

| Profile | Expected dependencies | What should work |
| --- | --- | --- |
| `Docs-only / static checks` | Python only | Docs edits, encoding checks, repo navigation |
| `Core non-COM development` | `requirements.txt` installed | App/module imports, UI/controller work, non-COM processor changes, targeted tests |
| `Full desktop validation on Windows` | `requirements.txt`, `pywin32`, Microsoft Excel, Windows | COM tools, compatibility repair, column tools, post-processing confidence, packaging validation |

Notes:

- The canonical developer environment is `pip install -r requirements.txt`.
- Missing `pywin32` no longer blocks importing the app module, but COM-backed tools still require it at runtime.
- Missing `pandas` or other required packages can still block processor imports and broader test suites.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional local safety setup for restricted fixtures:

```bash
git config core.hooksPath .githooks
```

## Running The App

```bash
python app.py
```

Behavior by environment:

- With full dependencies, all standard tabs should initialize.
- Without `pywin32`, the app can still import and non-COM paths can be developed, but COM-backed tools raise a clear runtime error when invoked.
- Real validation for compatibility repair, column tools, and COM post-processing still belongs on Windows with Excel installed.

## Workflow

1. Start from a small workbook sample before touching production-like files.
2. Keep UI logic in `ui/`, orchestration in `controller_modules/`, and workbook rules in `core/`.
3. Update the owning doc in `docs/` when behavior changes.
4. Preserve compatibility surfaces unless there is an approved migration plan.
5. Treat `docs/io-contract.md` as the owning doc for Excel value semantics.

## Quick Checks

- Docs-only changes:

```bash
python scripts/check_text_encoding.py --root docs
```

- App import and smoke-adjacent changes:

```bash
python -m unittest tests.test_app_smoke tests.test_app_component_registry tests.test_app_log_console
```

- Full canonical regression:

```bash
python scripts/run_regression_suite.py --with-golden
```

## Change-Type Verification Matrix

| Change type | Minimum verification |
| --- | --- |
| Docs-only | `python scripts/check_text_encoding.py --root docs` |
| UI / controller wiring | `python -m unittest discover -s tests -p "test_ui_*.py"` and `python -m unittest tests.test_ui_controllers tests.test_task_runner` |
| IO semantics / processor behavior | `python scripts/run_regression_suite.py --with-golden` |
| Terminology pipeline | `python -m unittest tests.test_terminology_processor tests.test_terminology_extractors tests.test_ui_terminology_controller` |
| Update-master behavior | `python -m unittest tests.test_master_merge_processor tests.test_master_merge_dispatcher tests.test_ui_update_master_views tests.test_ui_merge_masters_view` |
| Packaging / release work | `python scripts/run_regression_suite.py --with-golden` and validate from `TM_builder.spec` on Windows |

## Related Docs

- [Docs guide](./README.md)
- [Architecture](./architecture.md)
- [Excel IO contract](./io-contract.md)
- [Testing](./testing.md)
- [Decisions](./decisions.md)
