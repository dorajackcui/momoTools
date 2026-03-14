# Docs Canonical Index

Last updated: 2026-03-03
Audience: agents and engineers
Purpose: single source-of-truth navigation for maintainable docs

## Core Docs (Canonical, 6)

1. `docs/README.md` (this index, ownership and update rules)
2. `docs/ARCHITECTURE.md` (stable boundaries + refactor guardrails)
3. `docs/SESSION_DUMP.md` (current runtime snapshot)
4. `docs/IO_FORMAT_REQUIREMENTS.md` (IO behavior contract)
5. `docs/terminology_rule_config_notes.md` (terminology config contract)
6. `docs/troubleshooting.md` (operational diagnosis)

## Non-core Docs (Kept)

1. `docs/PRIVATE_TEST_DATA_POLICY.md` (private local fixture policy)
2. `docs/sample_terminology_rules.json` (config sample)
3. `docs/archive/*` (historical references only)

## Fast Path

Read in order:

1. `docs/ARCHITECTURE.md`
2. `docs/SESSION_DUMP.md`
3. `docs/IO_FORMAT_REQUIREMENTS.md`

## Source-of-Truth Ownership

| Topic | Owner doc |
| --- | --- |
| Layering, dependencies, compatibility, refactor boundaries | `docs/ARCHITECTURE.md` |
| Runtime UI/task/logging snapshot | `docs/SESSION_DUMP.md` |
| Excel IO semantics and special-value behavior | `docs/IO_FORMAT_REQUIREMENTS.md` |
| Terminology config and relation-output contract | `docs/terminology_rule_config_notes.md` |
| Runtime troubleshooting playbook | `docs/troubleshooting.md` |
| Private fixture safety policy | `docs/PRIVATE_TEST_DATA_POLICY.md` |

## Policy Decision Tracking

Open product/business policy decisions are not maintained in `docs/`.  
Track them in external issue/task systems and link them from PRs when relevant.

## Command Entry (Canonical)

```bash
python -m py_compile app.py controllers.py ui_components.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/run_regression_suite.py --with-golden
python scripts/run_perf_baseline.py
python -m unittest tests.test_private_data_skip_blank_write -v
```

## Update Rules

1. Update the owner doc in the same change set whenever behavior changes.
2. Keep each truth in one place only; avoid cross-file duplication.
3. Move outdated narrative docs to `docs/archive/*`.
4. Validate docs encoding before commit:

```bash
python scripts/check_text_encoding.py --root docs
```
