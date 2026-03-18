#!/usr/bin/env python3
"""Validate the repository documentation governance structure."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


DOCS_README_PATH = Path("docs/README.md")
ROOT_AGENTS_PATH = Path("AGENTS.md")
REQUIRED_LOCAL_AGENTS_HEADINGS = (
    "## What This Directory Owns",
    "## Canonical Docs To Update",
    "## Change Routing",
    "## Local Invariants",
    "## Modification Boundaries",
    "## Minimum Verification",
)


def _normalize_relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _run_git(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _collect_repo_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def _collect_local_agents(root: Path) -> list[Path]:
    return [
        path
        for path in _collect_repo_files(root, "**/AGENTS.md")
        if _normalize_relpath(path, root) != ROOT_AGENTS_PATH.as_posix()
    ]


def _extract_markdown_section(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"(?ms)^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _parse_registry_paths(docs_readme_text: str) -> list[str]:
    section = _extract_markdown_section(docs_readme_text, "## Local Contract Registry")
    if section is None:
        return []
    return re.findall(r"`([^`\n]+/AGENTS\.md)`", section)


def _find_missing_headings(text: str) -> list[str]:
    return [heading for heading in REQUIRED_LOCAL_AGENTS_HEADINGS if heading not in text]


def _extract_bullet_lines(section_text: str) -> list[str]:
    return [
        line.strip()
        for line in section_text.splitlines()
        if line.strip().startswith("- ")
    ]


def _validate_local_agents_file(path: Path, root: Path) -> list[str]:
    relpath = _normalize_relpath(path, root)
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    missing_headings = _find_missing_headings(text)
    if missing_headings:
        errors.append(
            f"{relpath}: missing required headings: {', '.join(missing_headings)}"
        )
        return errors

    change_routing = _extract_markdown_section(text, "## Change Routing") or ""
    if not change_routing.strip():
        errors.append(f"{relpath}: `## Change Routing` must not be empty")
    elif not re.search(r"docs/[^`\s]+\.md", change_routing):
        errors.append(f"{relpath}: `## Change Routing` must reference at least one `docs/*.md` target")

    invariants = _extract_markdown_section(text, "## Local Invariants") or ""
    invariant_lines = _extract_bullet_lines(invariants)
    if not invariant_lines:
        errors.append(f"{relpath}: `## Local Invariants` must contain at least one bullet")
    else:
        missing_owner = [line for line in invariant_lines if "Owner:" not in line]
        if missing_owner:
            errors.append(f"{relpath}: every `## Local Invariants` bullet must include `Owner:`")

    return errors


def validate_docs_system(root: Path) -> list[str]:
    docs_readme = root / DOCS_README_PATH
    errors: list[str] = []

    if not docs_readme.exists():
        return [f"Missing required governance file: {DOCS_README_PATH.as_posix()}"]

    docs_readme_text = docs_readme.read_text(encoding="utf-8")
    registry_paths = _parse_registry_paths(docs_readme_text)
    if not registry_paths:
        errors.append(
            f"{DOCS_README_PATH.as_posix()}: `## Local Contract Registry` must list at least one local `AGENTS.md` path"
        )
        return errors

    registry_set = set(registry_paths)
    local_agents = _collect_local_agents(root)
    local_agent_paths = {_normalize_relpath(path, root) for path in local_agents}

    missing_from_registry = sorted(local_agent_paths - registry_set)
    for relpath in missing_from_registry:
        errors.append(f"{relpath}: local contract is not registered in {DOCS_README_PATH.as_posix()}")

    missing_from_disk = sorted(registry_set - local_agent_paths)
    for relpath in missing_from_disk:
        errors.append(
            f"{DOCS_README_PATH.as_posix()}: registered local contract does not exist: {relpath}"
        )

    for path in local_agents:
        errors.extend(_validate_local_agents_file(path, root))

    return errors


def _normalize_paths(raw: str) -> list[str]:
    return [line.strip().replace("\\", "/") for line in raw.splitlines() if line.strip()]


def _collect_staged_paths(root: Path) -> list[str]:
    result = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], root)
    if result.returncode != 0:
        return []
    return _normalize_paths(result.stdout)


def is_docs_governance_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == "README.md":
        return True
    if normalized == "AGENTS.md" or normalized.endswith("/AGENTS.md"):
        return True
    return normalized.startswith("docs/") and normalized.endswith(".md")


def should_validate_staged_only(root: Path) -> bool:
    staged_paths = _collect_staged_paths(root)
    return any(is_docs_governance_path(path) for path in staged_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository docs governance structure.")
    parser.add_argument("--root", default=".", help="Repository root path.")
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Only validate when staged documentation-governance paths changed.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.staged_only and not should_validate_staged_only(root):
        print("OK: no staged documentation-governance changes detected.")
        return 0

    errors = validate_docs_system(root)
    if not errors:
        print("OK: docs governance structure is valid.")
        return 0

    print("Docs governance issues found:")
    for error in errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
