# Docs Index (Current)

Last updated: 2026-02-26

## Recommended reading order for a new AI session

1. `docs/SESSION_DUMP.md` (project snapshot + current behavior + quick entrypoints)
2. `docs/memo_pending_translation_rules.md` (business decisions still unresolved)
3. `docs/troubleshooting.md` (common failures and checks)
4. `IO_FORMAT_REQUIREMENTS.md` (strict IO contract, detailed)

## Active docs

- `docs/SESSION_DUMP.md`
  - One-file handoff context for a new session.
- `docs/memo_pending_translation_rules.md`
  - Pending policy decisions for translation/data handling.
- `docs/troubleshooting.md`
  - Practical diagnosis steps and command checklist.

## Archived docs

- Archived on 2026-02-26 under `docs/archive/2026-02-26/`:
  - `refactor_design.md`
  - `ui_refactor_guide.md`
  - `new_processor_template.md`
- Reason:
  - These files are historical design/process references, not required for daily session handoff.

## Maintenance rule

- If behavior changes in `controllers.py`, `core/*.py`, or UI flow:
  - update `docs/SESSION_DUMP.md` first,
  - then update `docs/memo_pending_translation_rules.md` if policy changed,
  - and keep detailed IO specifics in `IO_FORMAT_REQUIREMENTS.md`.
