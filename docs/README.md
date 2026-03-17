# Docs Guide

## Start Here

If you are new to the repo:

- Read the root `README.md` for install, startup, and high-level risks.
- Read `docs/architecture.md` to understand layer boundaries and runtime shape.
- Read `docs/testing.md` before changing code so you know which checks are expected.

If you are about to change behavior:

- Read `docs/io-contract.md` for workbook read/write semantics.
- Read `docs/decisions.md` for stable mode policies and compatibility constraints.
- Check whether the relevant subsystem also has a local `AGENTS.md`:
  - `core/master_update/AGENTS.md`
  - `core/terminology/AGENTS.md`
  - `ui/AGENTS.md`

## By Task

- Understand app structure and allowed dependencies: `docs/architecture.md`
- Change workbook matching, normalization, blank handling, or write rules: `docs/io-contract.md`
- Set up an environment or decide what should work without Windows/Excel: `docs/development.md`
- Pick the right test command for a change: `docs/testing.md`
- Package or validate a Windows desktop build: `docs/deployment.md`
- Confirm stable behavioral decisions and known gaps: `docs/decisions.md`
- Inspect terminology config examples: `docs/sample_terminology_rules.json`

## Source Of Truth

- `docs/architecture.md`
  - Owns application structure: layering, runtime model, tool-group layout, compatibility boundaries
  - Describe what exists and where orchestration lives; avoid duplicating detailed workbook rules here
- `docs/io-contract.md`
  - Owns workbook behavior: Excel normalization, blank detection, row identity, mode-specific write behavior
  - This is the only place for concrete IO semantics and pipeline execution behavior that affects results
- `docs/development.md`
  - Environment matrix, setup workflow, quick verification defaults
- `docs/testing.md`
  - Command selection, environment caveats, change-oriented test matrix
- `docs/deployment.md`
  - Packaging constraints and release validation expectations
- `docs/decisions.md`
  - Owns stable product and engineering decisions that should not drift silently
  - Record the durable rule or constraint, then link back to `architecture.md` or `io-contract.md` for implementation/detail when needed

Avoid restating the same rule in multiple active docs. Link back to the owning doc instead.

## Doc Update Rules

- Changing workbook IO semantics:
  - Update `docs/io-contract.md`
  - Run `.\scripts\python.cmd scripts/run_regression_suite.py --with-golden`
- Changing app structure, layer boundaries, or task-runner behavior:
  - Update `docs/architecture.md`
- Changing UI composition or orchestration shape without changing workbook results:
  - Update `docs/architecture.md`
  - Update `docs/decisions.md` only if the orchestration rule is intended to stay stable
- Changing environment assumptions, setup steps, or what works without COM:
  - Update `docs/development.md`
  - Update `docs/testing.md` if the expected validation path changes
- Changing validation expectations:
  - Update `docs/testing.md`
- Changing packaging or release constraints:
  - Update `docs/deployment.md`
- Changing a stable business rule or mode policy:
  - Update `docs/decisions.md`

## Doc Boundaries

- Put structural facts in `architecture.md`: tabs, layers, runtime ownership, compatibility surfaces.
- Put behavioral contracts in `io-contract.md`: matching, blank handling, overwrite rules, stage execution semantics.
- Put durable guardrails in `decisions.md`: rules that should not silently drift, even if implementation moves.
- If a rule needs examples or exact semantics, prefer one owning doc and have the others reference it briefly.

Historical or superseded material belongs in `archive/old_docs/`, not in active docs.
