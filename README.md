# momoTools

Desktop Excel tooling for localization workflows. The app centers on `key + match` row identity and includes master-to-target updates, reverse syncing, batch runs, terminology extraction, and update-master utilities.

## Install

Standard local setup:

```powershell
python -m venv .venv
.\scripts\python.cmd -m pip install -r requirements.txt
```

Sandbox-safe setup for path-restricted shells such as Codex:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap_repo_python.ps1 -BasePython "C:\Path\To\python.exe"
.\scripts\python.cmd -m pip install -r requirements.txt
```

`.\scripts\python.cmd` is the repo-safe Python entrypoint. It prefers a repo-local `.venv`, then falls back to an optional repo-local `.python` copy, so sandboxed or path-restricted shells do not depend on PATH.

Optional local safety setup for restricted fixtures:

```powershell
git config core.hooksPath .githooks
```

## Quick Start

Launch the desktop app:

```powershell
.\scripts\python.cmd app.py
```

Run the canonical regression entrypoint:

```powershell
.\scripts\python.cmd scripts/run_regression_suite.py --with-golden
```

## Risk Notes

- Primary runtime target is Windows desktop.
- COM-backed tools require Microsoft Excel plus `pywin32`.
- Back up important Excel files before running bulk operations.
- Full regression coverage assumes the environment can install `requirements.txt`.

## Documentation

- Start here: [docs/README.md](./docs/README.md)
- Agent guidance: [AGENTS.md](./AGENTS.md)
- Historical context: [archive/old_docs/README.md](./archive/old_docs/README.md)
