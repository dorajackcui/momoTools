import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import openpyxl

from core.deep_replace_processor import DeepReplaceProcessor
from core.excel_processor import ExcelProcessor
from core.kernel import run_parallel_map
from core.multi_column_processor import MultiColumnExcelProcessor
from core.reverse_excel_processor import ReverseExcelProcessor
from core.untranslated_stats_processor import UntranslatedStatsProcessor


def write_workbook(path: Path, rows: list[list[object]]) -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def read_cell(path: Path, row: int, col: int):
    workbook = openpyxl.load_workbook(path, data_only=True)
    try:
        return workbook.active.cell(row=row, column=col).value
    finally:
        workbook.close()


class CoreProcessorsRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_update_overwrite_and_fill_blank_only(self):
        master_path = self.root / "master.xlsx"
        target_folder = self.root / "targets_single"
        target_folder.mkdir()
        target_path = target_folder / "target.xlsx"

        write_workbook(
            master_path,
            [
                ["id", "key", "match", "value"],
                ["", "K1", "M1", "V1"],
            ],
        )
        write_workbook(
            target_path,
            [
                ["key", "match", "translation"],
                ["K1", "M1", ""],
                ["K1", "M1", "keep-me"],
            ],
        )

        processor = ExcelProcessor(log_callback=lambda _msg: None)
        processor.set_master_file(str(master_path))
        processor.set_target_folder(str(target_folder))
        processor.set_post_process_enabled(False)
        processor.set_fill_blank_only(True)

        updated_count = processor.process_files()

        self.assertEqual(updated_count, 1)
        self.assertEqual(read_cell(target_path, 2, 3), "V1")
        self.assertEqual(read_cell(target_path, 3, 3), "keep-me")

    def test_multi_column_update(self):
        master_path = self.root / "master_multi.xlsx"
        target_folder = self.root / "targets_multi"
        target_folder.mkdir()
        target_path = target_folder / "target.xlsx"

        write_workbook(
            master_path,
            [
                ["id", "key", "match", "meta", "v1", "v2"],
                ["", "K1", "M1", "", "A1", "A2"],
            ],
        )
        write_workbook(
            target_path,
            [
                ["id", "key", "match", "meta", "out1", "out2"],
                ["", "K1", "M1", "", "", "old"],
            ],
        )

        processor = MultiColumnExcelProcessor(log_callback=lambda _msg: None)
        processor.set_master_file(str(master_path))
        processor.set_target_folder(str(target_folder))
        processor.set_column_count(2)
        processor.set_post_process_enabled(False)
        processor.set_fill_blank_only(False)

        updated_count = processor.process_files()

        self.assertEqual(updated_count, 2)
        self.assertEqual(read_cell(target_path, 2, 5), "A1")
        self.assertEqual(read_cell(target_path, 2, 6), "A2")

    def test_reverse_update_has_deterministic_merge_precedence(self):
        master_path = self.root / "master_reverse.xlsx"
        target_folder = self.root / "targets_reverse"
        target_folder.mkdir()

        write_workbook(
            master_path,
            [
                ["id", "key", "match", "translation"],
                ["", "K1", "M1", ""],
            ],
        )

        write_workbook(
            target_folder / "a.xlsx",
            [
                ["key", "match", "translation"],
                ["K1", "M1", "from_a"],
            ],
        )
        write_workbook(
            target_folder / "b.xlsx",
            [
                ["key", "match", "translation"],
                ["K1", "M1", "from_b"],
            ],
        )

        processor = ReverseExcelProcessor(log_callback=lambda _msg: None)
        processor.set_master_file(str(master_path))
        processor.set_target_folder(str(target_folder))

        updated_count = processor.process_files()

        self.assertEqual(updated_count, 1)
        self.assertEqual(read_cell(master_path, 2, 4), "from_b")

    def test_untranslated_stats_and_export(self):
        target_folder = self.root / "stats_targets"
        target_folder.mkdir()
        source_path = target_folder / "stats.xlsx"
        output_path = self.root / "stats_output.xlsx"

        write_workbook(
            source_path,
            [
                ["id", "source", "translation"],
                [1, "hello world", ""],
                [2, "cat", "done"],
            ],
        )

        processor = UntranslatedStatsProcessor(log_callback=lambda _msg: None)
        processor.set_target_folder(str(target_folder))
        processor.set_stats_mode("english_words")
        processor.set_columns(1, 2)

        results = processor.process_files()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["untranslated_chars"], 2)
        self.assertEqual(results[0]["untranslated_rows"], 1)
        self.assertEqual(results[0]["total_chars"], 3)
        self.assertEqual(results[0]["total_rows"], 2)
        self.assertTrue(processor.export_to_excel(str(output_path)))
        self.assertTrue(output_path.exists())

    def test_deep_replace_rolls_back_when_copy_fails(self):
        source_folder = self.root / "replace_source"
        target_folder = self.root / "replace_target"
        source_folder.mkdir()
        target_folder.mkdir()

        source_file = source_folder / "sample.xlsx"
        target_file = target_folder / "sample.xlsx"
        source_file.write_text("new-content", encoding="utf-8")
        target_file.write_text("old-content", encoding="utf-8")

        processor = DeepReplaceProcessor(log_callback=lambda _msg: None)
        processor.set_source_folder(str(source_folder))
        processor.set_target_folder(str(target_folder))

        original_copy2 = shutil.copy2
        call_count = {"value": 0}

        def flaky_copy2(src, dst, *args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 2:
                raise OSError("simulated copy failure")
            return original_copy2(src, dst, *args, **kwargs)

        with patch("core.deep_replace_processor.shutil.copy2", side_effect=flaky_copy2):
            processed_files = processor.process_files()

        self.assertEqual(processed_files, 0)
        self.assertEqual(target_file.read_text(encoding="utf-8"), "old-content")
        self.assertFalse(Path(f"{target_file}.bak").exists())
        self.assertEqual(len(processor.stats.errors), 1)

    def test_parallel_map_preserves_input_order(self):
        items = [1, 2, 3]

        def worker(item):
            time.sleep((4 - item) * 0.01)
            return item * 10

        results = run_parallel_map(items, worker, max_workers_cap=3)
        self.assertEqual(results, [10, 20, 30])


if __name__ == "__main__":
    unittest.main()
