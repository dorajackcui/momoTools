# Docs Guide

This file is the governance entry for the active documentation set. Use it to decide which canonical doc owns a change, which local contract to re-read, and which docs validation to run before finishing a change set.

## Documentation Layers

- `README.md`
  - Human onboarding: install, startup, risk notes, and top-level links
- Root `AGENTS.md`
  - Repo-wide agent workflow, global constraints, and default validation entrypoints
- `docs/*.md`
  - Canonical global documentation owners for cross-directory behavior and policy
- Local `AGENTS.md`
  - Directory contracts that define local routing, invariants, and minimum verification

`docs/README.md` is the only active governance index. Do not spread owner rules across multiple active files.

## Canonical Doc Owners

| Topic | Canonical owner | What belongs there |
| --- | --- | --- |
| Cross-repo structure | `docs/architecture.md` | Layering, runtime model, notebook/tool layout, compatibility surfaces, orchestration boundaries |
| Workbook IO semantics | `docs/io-contract.md` | Normalization, blank handling, row identity, match-column behavior, mode-specific write rules |
| Validation and commands | `docs/testing.md` | Change-oriented verification matrix, canonical commands, test selection |
| Environment and workflow | `docs/development.md` | Setup, environment matrix, development workflow, repo-local Python guidance |
| Packaging and release constraints | `docs/deployment.md` | Packaging expectations, Windows validation, release constraints |
| End-user quick guide | `docs/user_quick_start.md` | Minimal user-facing launch steps, common tab mapping, and safe operation reminders |
| Stable product and engineering decisions | `docs/decisions.md` | Durable guarantees that should not silently drift even if implementation moves |

Local `AGENTS.md` files do not replace these owners. They summarize directory-specific guidance and route changes back to the canonical owner docs.

## Local Contract Registry

- `ui/AGENTS.md`
  - UI presentation-layer contract for views, widgets, and UI-specific routing
- `core/master_update/AGENTS.md`
  - Update-master engine contract for row identity, executor routing, and mode-policy sync
- `core/terminology/AGENTS.md`
  - Terminology pipeline contract for config/output compatibility and export sync

If you add, remove, or relocate a local `AGENTS.md`, update this registry in the same change set.

## Change Routing Matrix

| If you change... | Update canonical doc(s) | Re-read or update local contract |
| --- | --- | --- |
| UI composition, notebook layout, view-model shape, UI-controller state flow | `docs/architecture.md` | `ui/AGENTS.md` |
| Task-runner ownership, compatibility surfaces, or cross-layer orchestration boundaries | `docs/architecture.md` | Nearest local contract when the change lives under a registered directory |
| Workbook matching, blank handling, write semantics, row identity, match-column behavior | `docs/io-contract.md` | `core/master_update/AGENTS.md` when the work is in update-master internals |
| Stable business rules or durable mode policies | `docs/decisions.md` | Relevant local contract for the touched subsystem |
| Terminology config compatibility or durable terminology output guarantees | `docs/decisions.md` | `core/terminology/AGENTS.md` |
| Terminology export sheet or column semantics that affect downstream workbook expectations | `docs/io-contract.md` | `core/terminology/AGENTS.md` |
| Validation commands, minimum verification, or change-type test routing | `docs/testing.md` | Relevant local contract when its `Minimum Verification` section changes |
| Environment assumptions, setup steps, or repo-local Python workflow | `docs/development.md` | None unless a local contract references the changed workflow directly |
| Packaging or release validation expectations | `docs/deployment.md` | None unless a local contract references the changed workflow directly |
| Directory-only editing guidance, routing, or minimum verification | Local `AGENTS.md` in that directory | That same local `AGENTS.md` |
| Docs governance, canonical ownership, or local-contract registration | `docs/README.md` | Any local `AGENTS.md` affected by the governance change |

When a change affects both a canonical owner doc and a local contract, update both in the same change set.

## Update Workflow

1. Start from the touched directories, then check whether one of them has a registered local `AGENTS.md`.
2. Use the matrix above to identify the canonical owner doc before writing or moving documentation.
3. Update the canonical owner doc first when behavior, structure, or policy changes.
4. Update the relevant local `AGENTS.md` whenever its routing, local invariants, or minimum verification changes.
5. Replace repeated rules with a short summary plus an explicit owner reference instead of copying full semantics into multiple files.
6. Run docs validation before finishing the change set:

```powershell
.\scripts\python.cmd scripts/check_text_encoding.py --root docs
.\scripts\python.cmd scripts/check_docs_system.py
```

## Anti-Duplication Rules

- Keep full semantics in exactly one canonical owner doc.
- Local `AGENTS.md` files may keep short directory-specific summaries, but every non-obvious invariant must identify its owner with `Owner: local` or `Owner: docs/...`.
- If a rule is fully owned by a canonical doc, local contracts should point to it instead of re-copying the full rule block.
- Root `AGENTS.md` may keep global working constraints and default validation entrypoints, but not a second source-of-truth ownership matrix.
- Move superseded material into `archive/old_docs/` instead of layering contradictory notes into active docs.

## Docs Review Checklist

- The canonical owner doc for each changed behavior, structure, validation rule, or environment rule was updated.
- Every touched registered directory still has a local `AGENTS.md` that matches the unified template.
- The `Local Contract Registry` still lists every child `AGENTS.md` and nothing missing from disk.
- Local `AGENTS.md` files keep summaries short, route detailed semantics back to owner docs, and tag each invariant with `Owner:`.
- Docs-only verification passes:

```powershell
.\scripts\python.cmd scripts/check_text_encoding.py --root docs
.\scripts\python.cmd scripts/check_docs_system.py
```

- Historical or superseded material was moved to `archive/old_docs/` instead of left active.
