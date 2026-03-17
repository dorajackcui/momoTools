# Architecture

## Overview

`momoTools` is a desktop Tkinter application organized into UI, controller, and core processing layers. The design goal is to keep Excel localization workflows stable while making the codebase easier to evolve and test.

## Main Components

- `app.py`
  - Creates the Tk root window
  - Initializes processors
  - Builds notebook groups and tool tabs
  - Owns status and log-window wiring
- `ui/`
  - Views under `ui/views/`
  - Shared widgets under `ui/widgets/`
  - Theme, strings, validators, and view-model dataclasses
- `controller_modules/`
  - Validates user input
  - Adapts UI state into processor configuration
  - Dispatches work through the task runner
  - Reports completion and errors back to the UI
- `core/`
  - Implements workbook processing behavior
  - Contains update, reverse-update, merge, terminology, compatibility, and utility processors
- `core/kernel/`
  - Shared Excel IO helpers, normalization rules, event logging, and shared types
- `core/pipeline/`
  - Reusable execution helpers used by processor flows
- `scripts/`
  - Regression, performance, and maintenance scripts

## Layer Boundaries

Allowed dependencies:

- `ui -> controller_modules`
- `controller_modules -> core`
- `core -> core/kernel`
- `core -> core/pipeline`

Not allowed:

- `core` importing from `ui` or `controller_modules`
- `ui` calling processors directly
- New feature logic living only in `controllers.py`

## Runtime Model

- The app is centered on `ExcelUpdaterApp` in `app.py`.
- UI work stays on the Tk main thread.
- Background processing runs through `TkSingleTaskRunner`.
- Completion callbacks marshal back to the UI with `root.after(...)`.
- The app enforces a single-task lock; concurrent processing requests are rejected.
- Cancellation is not currently implemented.
- File and folder selection prechecks belong to the `controller_modules` + `ui` dialog layer.
- Shared folder prechecks currently cover content-sync flows, batch job folders, and target-folder writes for `Column Clear/Insert/Delete`, `Compatibility`, and `Deep Replace`.
- `Deep Replace` source-folder selection remains a plain path selection and does not use target-folder write prechecks.
- Core processors still own workbook business behavior; input prechecks must not redefine IO semantics.

## Tool Groups

The current UI organizes tools into three notebook groups:

- Content Sync
  - `Master->Target`
  - `Target->Master`
  - `Batch`
- Utilities
  - `Column Clear`
  - `Compatibility`
  - `Deep Replace`
  - `Untranslated Stats`
  - `Term Extractor`
- Update Master
  - `Merge Masters`
  - `Source Text`
  - `Translation`
    - exports a per-run unmatched-segment Excel report with `key`, `match`, source file, and content columns

## Observability

- Processors emit messages through `log_callback`.
- Structured failures are emitted through `EventLogger`.
- The application drains log messages into an in-memory bounded buffer.
- Status text follows the `Running`, `Done`, and `Failed` task states.

## Compatibility Surface

These entrypoints are treated as stable unless an explicit migration is approved:

- `app.py`
- `controllers.py` exports, including compatibility imports
- `ui_components.py`
- Existing processor class names and setter method names

## Architecture Notes

- `controllers.py` is a compatibility facade, not the main implementation layer.
- `core/master_update/` contains the policy-based engine behind merge and update-master workflows.
- `core/terminology/` is a staged pipeline for extraction, normalization, relation building, review output, and export.
- Detailed Excel read/write semantics live in [io-contract.md](./io-contract.md).

Historical architecture notes and previous refactor guides were moved to [archive/old_docs/README.md](../archive/old_docs/README.md).
