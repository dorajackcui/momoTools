# Docs Index (Current)

Last updated: 2026-02-26 (Terminology Extractor MVP added)

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
- `docs/sample_terminology_rules.json`
  - Sample Terminology Extractor rule config for local testing.
- `docs/terminology_rule_config_notes.md`
  - Field-by-field explanation for terminology rule config.

## New feature docs touchpoints

- Terminology extractor implementation lives in:
  - `core/terminology/*`
  - `ui/views/terminology_extractor.py`
  - `controller_modules/terminology_extractor.py` (`TerminologyExtractorController`)
  - `controllers.py` (compatibility facade / re-export)
  - `app.py` (new `Utilities` tab entry)

## Archived docs

- Archived on 2026-02-26 under `docs/archive/2026-02-26/`:
  - `refactor_design.md`
  - `ui_refactor_guide.md`
  - `new_processor_template.md`
- Reason:
  - These files are historical design/process references, not required for daily session handoff.

## Maintenance rule

- If behavior changes in `controllers.py`, `core/*.py`, or UI flow:
  - for controller logic changes, edit `controller_modules/*` first,
  - keep `controllers.py` as compatibility facade,
  - update `docs/SESSION_DUMP.md` first,
  - then update `docs/memo_pending_translation_rules.md` if policy changed,
  - and keep detailed IO specifics in `IO_FORMAT_REQUIREMENTS.md`.
- Before committing broad text edits, run encoding guardrail:
  - `python scripts/check_text_encoding.py`
