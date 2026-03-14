# New Processor Template (Kernel Adapter Pattern)

Use this checklist when adding a new processor mode.

## Step 1: Keep public API minimal and stable

1. Create class in `core/`.
2. Preserve old-style constructor (`log_callback=None`) if applicable.
3. Expose explicit setter methods for external configuration.

## Step 2: Declare mode contract

1. Define `ModeIOContract(mode_name=..., skip_header=...)`.
2. Keep file extensions and key separator explicit.

## Step 3: Reuse kernel building blocks

1. `iter_excel_files` for recursive file collection.
2. `build_combined_key` for `key|match` semantics.
3. `open_workbook` for safe workbook lifecycle.
4. `apply_cell_updates` for batched write-back.
5. `run_parallel_map` or `run_parallel_sum` for safe concurrency.

## Step 4: Error visibility

1. Track `ProcessingStats`.
2. Emit `ErrorEvent` with stable `code`.
3. Keep user-visible exception flow unchanged.

## Step 5: Regression requirement

1. Add/extend case in `tests/golden/manifest.template.json`.
2. Add sample entry in `tests/golden/sample_inventory_template.md`.
3. Run `scripts/run_golden_regression.py` before merge.
