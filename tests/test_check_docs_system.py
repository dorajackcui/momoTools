import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import check_docs_system


DOCS_README = """# Docs Guide

## Local Contract Registry

- `ui/AGENTS.md`
- `core/master_update/AGENTS.md`
"""


LOCAL_AGENTS_TEMPLATE = """# AGENTS.md

## What This Directory Owns

- Example ownership.

## Canonical Docs To Update

- `docs/architecture.md`

## Change Routing

- Example routing -> `docs/architecture.md`
- Local-only rule maintenance -> `ui/AGENTS.md`

## Local Invariants

- Keep the contract concise. Owner: local
- Route structure changes to architecture. Owner: docs/architecture.md

## Modification Boundaries

- Stay within the directory contract.

## Minimum Verification

- `python -m unittest`
"""


class CheckDocsSystemTestCase(unittest.TestCase):
    def _write_repo(self, temp_dir: str) -> Path:
        root = Path(temp_dir)
        (root / "docs").mkdir(parents=True)
        (root / "ui").mkdir(parents=True)
        (root / "core" / "master_update").mkdir(parents=True)
        (root / "docs" / "README.md").write_text(DOCS_README, encoding="utf-8")
        (root / "ui" / "AGENTS.md").write_text(LOCAL_AGENTS_TEMPLATE, encoding="utf-8")
        (root / "core" / "master_update" / "AGENTS.md").write_text(
            LOCAL_AGENTS_TEMPLATE.replace("ui/AGENTS.md", "core/master_update/AGENTS.md"),
            encoding="utf-8",
        )
        return root

    def test_validate_docs_system_passes_for_valid_repo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(errors, [])

    def test_validate_docs_system_reports_unregistered_local_agents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "docs" / "README.md").write_text(
                "# Docs Guide\n\n## Local Contract Registry\n\n- `ui/AGENTS.md`\n",
                encoding="utf-8",
            )

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("core/master_update/AGENTS.md", errors[0])
            self.assertIn("not registered", errors[0])

    def test_validate_docs_system_reports_missing_registry_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "docs" / "README.md").write_text(
                DOCS_README + "- `core/terminology/AGENTS.md`\n",
                encoding="utf-8",
            )

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("registered local contract does not exist", errors[0])
            self.assertIn("core/terminology/AGENTS.md", errors[0])

    def test_validate_docs_system_reports_missing_required_heading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "ui" / "AGENTS.md").write_text(
                LOCAL_AGENTS_TEMPLATE.replace("## Minimum Verification\n", ""),
                encoding="utf-8",
            )

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("missing required headings", errors[0])
            self.assertIn("## Minimum Verification", errors[0])

    def test_validate_docs_system_reports_missing_owner_in_local_invariants(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "ui" / "AGENTS.md").write_text(
                LOCAL_AGENTS_TEMPLATE.replace(
                    "- Keep the contract concise. Owner: local\n",
                    "- Keep the contract concise.\n",
                ),
                encoding="utf-8",
            )

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("every `## Local Invariants` bullet must include `Owner:`", errors[0])

    def test_validate_docs_system_reports_change_routing_without_docs_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "ui" / "AGENTS.md").write_text(
                LOCAL_AGENTS_TEMPLATE.replace(
                    "- Example routing -> `docs/architecture.md`\n",
                    "- Example routing -> `ui/AGENTS.md`\n",
                ),
                encoding="utf-8",
            )

            errors = check_docs_system.validate_docs_system(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("must reference at least one `docs/*.md` target", errors[0])

    def test_main_staged_only_skips_when_no_docs_governance_paths_changed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            with patch("scripts.check_docs_system._collect_staged_paths", return_value=["core/app.py"]):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = check_docs_system.main(["--root", str(root), "--staged-only"])

            self.assertEqual(exit_code, 0)

    def test_main_staged_only_runs_validation_for_docs_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self._write_repo(temp_dir)
            (root / "ui" / "AGENTS.md").write_text(
                LOCAL_AGENTS_TEMPLATE.replace(
                    "- Keep the contract concise. Owner: local\n",
                    "- Keep the contract concise.\n",
                ),
                encoding="utf-8",
            )
            with patch("scripts.check_docs_system._collect_staged_paths", return_value=["ui/AGENTS.md"]):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = check_docs_system.main(["--root", str(root), "--staged-only"])

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
