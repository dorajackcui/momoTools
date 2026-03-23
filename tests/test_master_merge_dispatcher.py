import unittest
from contextlib import contextmanager
from unittest.mock import patch

from core.master_merge_processor import (
    CELL_WRITE_POLICY_FILL_BLANK_ONLY,
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    MasterMergeProcessor,
    MasterMergeResult,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_KEY_ONLY,
)
from core.master_update.executors.base import BaseMasterUpdateExecutor
from core.master_update.executors.merge_masters import MergeMastersExecutor
from core.master_update.executors.update_content import UpdateContentExecutor
from core.master_update.executors.update_master import UpdateMasterExecutor


class FakeExecutor:
    seen_source_files = None

    def __init__(self, _processor):
        pass

    def resolve_source_files(self):
        return ["a.xlsx", "b.xlsx"]

    def run(self, source_files):
        type(self).seen_source_files = list(source_files)
        return MasterMergeResult(
            updated_cells=1,
            added_rows=0,
            merged_keys=1,
            source_files=len(source_files),
            unmatched_entries=2,
            unmatched_report_path="C:/tmp/translation_unmatched_report.xlsx",
        )


class MasterMergeDispatcherTestCase(unittest.TestCase):
    def test_resolve_executor_for_each_supported_combo(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)

        processor.set_policies(
            cell_write_policy=CELL_WRITE_POLICY_FILL_BLANK_ONLY,
            key_admission_policy=KEY_ADMISSION_POLICY_ALLOW_NEW,
            priority_winner_policy=PRIORITY_WINNER_POLICY_LAST_PROCESSED,
        )
        self.assertIs(processor._resolve_executor_cls(), MergeMastersExecutor)

        processor.set_policies(
            cell_write_policy=CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
            key_admission_policy=KEY_ADMISSION_POLICY_ALLOW_NEW,
            priority_winner_policy=PRIORITY_WINNER_POLICY_LAST_PROCESSED,
        )
        self.assertIs(processor._resolve_executor_cls(), UpdateMasterExecutor)

        processor.set_policies(
            cell_write_policy=CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
            key_admission_policy=KEY_ADMISSION_POLICY_EXISTING_ONLY,
            priority_winner_policy=PRIORITY_WINNER_POLICY_LAST_PROCESSED,
        )
        self.assertIs(processor._resolve_executor_cls(), UpdateContentExecutor)

    def test_unsupported_policy_combination_raises(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)
        processor.set_policies(
            cell_write_policy=CELL_WRITE_POLICY_FILL_BLANK_ONLY,
            key_admission_policy=KEY_ADMISSION_POLICY_EXISTING_ONLY,
            priority_winner_policy=PRIORITY_WINNER_POLICY_LAST_PROCESSED,
        )

        with self.assertRaises(ValueError):
            processor._resolve_executor_cls()

    def test_process_files_dispatches_to_resolved_executor(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)
        with patch.object(processor, "_resolve_executor_cls", return_value=FakeExecutor):
            result = processor.process_files()

        self.assertEqual(FakeExecutor.seen_source_files, ["a.xlsx", "b.xlsx"])
        self.assertEqual(processor.stats.files_total, 3)
        self.assertEqual(result.updated_cells, 1)
        self.assertEqual(result.source_files, 2)
        self.assertEqual(result.unmatched_entries, 2)
        self.assertEqual(result.unmatched_report_path, "C:/tmp/translation_unmatched_report.xlsx")

    def test_facade_api_methods_exist(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)
        for method_name in [
            "set_master_file",
            "set_update_folder",
            "set_columns",
            "set_priority_files",
            "set_policies",
            "set_row_key_policy",
            "list_update_files",
            "process_files",
        ]:
            self.assertTrue(hasattr(processor, method_name))
            self.assertTrue(callable(getattr(processor, method_name)))

        processor.set_row_key_policy(ROW_KEY_POLICY_KEY_ONLY)
        self.assertEqual(processor.row_key_policy, ROW_KEY_POLICY_KEY_ONLY)

    def test_resolve_layout_uses_last_update_col_without_probe(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)
        processor.set_master_file("C:/missing/master.xlsx")
        processor.set_columns(1, 2, 5)
        executor = BaseMasterUpdateExecutor(processor)

        with patch(
            "core.master_update.executors.base.open_workbook",
            side_effect=AssertionError("layout probe should be skipped"),
        ):
            layout = executor.resolve_layout()

        self.assertFalse(layout.probe_used)
        self.assertEqual(layout.probe_elapsed, 0.0)
        self.assertEqual(layout.max_col, 6)
        self.assertEqual(layout.content_col_indexes, [0, 3, 4, 5])

    def test_resolve_layout_falls_back_to_master_probe_when_last_update_col_missing(self):
        processor = MasterMergeProcessor(log_callback=lambda _msg: None)
        processor.set_master_file("C:/tmp/master.xlsx")
        processor.set_columns(1, 2, None)
        executor = BaseMasterUpdateExecutor(processor)

        class FakeWorkbook:
            def __init__(self):
                self.active = type("FakeSheet", (), {"max_column": 7})()

        @contextmanager
        def fake_open_workbook(*_args, **_kwargs):
            yield FakeWorkbook()

        with patch(
            "core.master_update.executors.base.open_workbook",
            side_effect=fake_open_workbook,
        ) as open_workbook_mock:
            layout = executor.resolve_layout()

        open_workbook_mock.assert_called_once_with(
            "C:/tmp/master.xlsx",
            read_only=True,
            keep_links=False,
        )
        self.assertTrue(layout.probe_used)
        self.assertGreaterEqual(layout.probe_elapsed, 0.0)
        self.assertEqual(layout.max_col, 7)
        self.assertEqual(layout.content_col_indexes, [0, 3, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
