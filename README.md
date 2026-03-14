# momoTools

Desktop Excel tooling for localization workflows. The app centers on `key + match` row identity and includes master-to-target updates, reverse syncing, batch runs, terminology extraction, and update-master utilities.

## Install

The canonical developer setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional local safety setup for restricted fixtures:

```bash
git config core.hooksPath .githooks
```

## Quick Start

Launch the desktop app:

```bash
python app.py
```

Run the canonical regression entrypoint:

```bash
python scripts/run_regression_suite.py --with-golden
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
