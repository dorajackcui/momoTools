# Private Test Data Policy

Last updated: 2026-03-03
Audience: engineers running local production-like regressions
Owns: private local fixture placement and protection rules

Goal: keep local production-like samples in workspace but out of git history.

## Location

Put local samples only under:
- `tests/_private_data/`

## Protections

1. `.gitignore` ignores `tests/_private_data/**`.
2. Git hooks block commit/push when restricted paths are detected:
   - `.githooks/pre-commit`
   - `.githooks/pre-push`
   - `scripts/git_hooks/block_private_data.py`

## One-time setup

Run in this repo:

```bash
git config core.hooksPath .githooks
```

## Notes

- This is strong local protection, not a mathematically absolute guarantee.
- If someone uses `git add -f` and disables hooks manually, data can still be committed.
- For team-level hard control, also add server-side checks in CI/review rules.

## Local Private Regression Entry

Run:

```bash
python -m unittest tests.test_private_data_skip_blank_write -v
```

Behavior:

1. Uses temporary copies and never writes back to `tests/_private_data`.
2. Auto-skips when required private folders/files are missing.
