#!/usr/bin/env python3
"""Check repository text files are UTF-8 without BOM."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".scss",
    ".html",
    ".xml",
    ".bat",
    ".cmd",
    ".ps1",
    ".gitattributes",
    ".editorconfig",
}

TEXT_FILENAMES = {
    "README",
    "LICENSE",
    "AGENTS.md",
}


def iter_repo_files(root: Path) -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            encoding="utf-8",
        )
        candidates = [root / line for line in output.splitlines() if line.strip()]
    except Exception:
        candidates = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]

    result: list[Path] = []
    for path in candidates:
        name = path.name
        suffix = path.suffix.lower()
        stem = path.stem.upper()
        if suffix in TEXT_EXTENSIONS or name in TEXT_FILENAMES or stem in TEXT_FILENAMES:
            result.append(path)
    return sorted(set(result))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate text encoding for repository files.")
    parser.add_argument("--root", default=".", help="Repository root path.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    utf8_bom_issues: list[Path] = []
    utf16_bom_issues: list[Path] = []
    decode_issues: list[Path] = []

    for path in iter_repo_files(root):
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            utf8_bom_issues.append(path)
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            utf16_bom_issues.append(path)
        if b"\x00" in raw[:4096]:
            continue
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            decode_issues.append(path)

    if not utf8_bom_issues and not utf16_bom_issues and not decode_issues:
        print("OK: all checked text files are UTF-8 without BOM.")
        return 0

    print("Encoding issues found:")
    if utf8_bom_issues:
        print(f"- UTF-8 BOM files: {len(utf8_bom_issues)}")
        for path in utf8_bom_issues:
            print(f"  - {path.relative_to(root)}")
    if utf16_bom_issues:
        print(f"- UTF-16 BOM files: {len(utf16_bom_issues)}")
        for path in utf16_bom_issues:
            print(f"  - {path.relative_to(root)}")
    if decode_issues:
        print(f"- Non-UTF-8 text files: {len(decode_issues)}")
        for path in decode_issues:
            print(f"  - {path.relative_to(root)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
