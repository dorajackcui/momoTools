# Development

## Environment Matrix

| Profile | Expected dependencies | What should work |
| --- | --- | --- |
| `Docs-only / static checks` | Python only | Docs edits, encoding checks, docs-governance checks, repo navigation |
| `Core non-COM development` | `requirements.txt` installed | App/module imports, UI/controller work, non-COM processor changes, targeted tests |
| `Full desktop validation on Windows` | `requirements.txt`, `pywin32`, Microsoft Excel, Windows | COM tools, compatibility repair, column tools, post-processing confidence, packaging validation |

Notes:

- The canonical developer environment is `pip install -r requirements.txt`.
- Missing `pywin32` no longer blocks importing the app module, but COM-backed tools still require it at runtime.
- Missing `pandas` or other required packages can still block processor imports and broader test suites.
- Sandboxed or path-restricted shells should not rely on a host `python.exe`; use the repo-local launcher in `scripts/python.cmd`.

## Setup

Standard local setup:

```powershell
python -m venv .venv
.\scripts\python.cmd -m pip install -r requirements.txt
```

Sandbox-safe setup for path-restricted shells:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap_repo_python.ps1 -BasePython "C:\Path\To\python.exe"
.\scripts\python.cmd -m pip install -r requirements.txt
```

Notes:

- `.\scripts\python.cmd` is the canonical Python entrypoint for this repo because it keeps working when PATH-based interpreters are blocked by sandbox rules.
- The bootstrap script is only needed when a shell cannot execute the base interpreter behind `.venv`. It copies the selected base Python into `.python/` inside the repo and recreates `.venv/` from that local copy.
- In a normal unsandboxed local shell you can still use `python ...` directly, but docs and automation should prefer `.\scripts\python.cmd ...`.

Optional local safety setup for restricted fixtures:

```powershell
git config core.hooksPath .githooks
```

## Running The App

```powershell
.\scripts\python.cmd app.py
```

Behavior by environment:

- With full dependencies, all standard tabs should initialize.
- Without `pywin32`, the app can still import and non-COM paths can be developed, but COM-backed tools raise a clear runtime error when invoked.
- Real validation for compatibility repair, column tools, and COM post-processing still belongs on Windows with Excel installed.

## Workflow

1. Start from a small workbook sample before touching production-like files.
2. Keep UI logic in `ui/`, orchestration in `controller_modules/`, and workbook rules in `core/`.
3. Use `docs/README.md` to identify the canonical owner doc and any local contract before changing documentation.
4. Update the owning doc and any touched local `AGENTS.md` in the same change set when behavior, routing, or verification changes.
5. Preserve compatibility surfaces unless there is an approved migration plan.
6. Use `docs/testing.md` as the canonical change-type verification matrix.

## Quick Checks

- Docs-only changes:

```powershell
.\scripts\python.cmd scripts/check_text_encoding.py --root docs
.\scripts\python.cmd scripts/check_docs_system.py
```

- App import and smoke-adjacent changes:

```powershell
.\scripts\python.cmd -m unittest tests.test_app_smoke tests.test_app_component_registry tests.test_app_log_console
```

- Full canonical regression:

```powershell
.\scripts\python.cmd scripts/run_regression_suite.py --with-golden
```

## Validation Routing

`docs/testing.md` is the canonical command matrix for change-type verification. Keep this file focused on environment and workflow, and update `docs/testing.md` instead of duplicating a second full matrix here.

## Related Docs

- [Docs guide](./README.md)
- [Architecture](./architecture.md)
- [Excel IO contract](./io-contract.md)
- [Testing](./testing.md)
- [Decisions](./decisions.md)
