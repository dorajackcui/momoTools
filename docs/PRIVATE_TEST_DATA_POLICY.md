# Private Test Data Policy

Goal: keep local production-like test files in repo workspace, but never commit or push them.

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
