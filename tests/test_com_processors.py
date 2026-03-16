import unittest
from unittest.mock import MagicMock, patch

from core.excel_cleaner import COM_DEPENDENCY_ERROR as CLEANER_COM_ERROR
from core.excel_cleaner import ExcelColumnClearer
from core.excel_compatibility_processor import COM_DEPENDENCY_ERROR as COMPAT_COM_ERROR
from core.excel_compatibility_processor import ExcelCompatibilityProcessor


class ComProcessorsTestCase(unittest.TestCase):
    @patch("core.excel_compatibility_processor.iter_excel_files")
    @patch("core.excel_compatibility_processor._load_dispatch")
    @patch("builtins.print")
    def test_compatibility_processor_handles_file_failure_and_quits_excel(
        self,
        _mock_print,
        mock_dispatch,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx", "C:\\tmp\\b.xlsx"]

        workbook = MagicMock()
        excel_app = MagicMock()
        excel_app.Workbooks.Open.side_effect = [workbook, Exception("broken file")]
        mock_dispatch.return_value = MagicMock(return_value=excel_app)

        processor = ExcelCompatibilityProcessor()
        processor.set_folder_path("C:\\tmp")

        processed = processor.process_files()

        self.assertEqual(processed, 1)
        workbook.Save.assert_called_once()
        workbook.Close.assert_called_once()
        excel_app.Quit.assert_called_once()
        self.assertEqual(len(processor.stats.errors), 1)

    @patch("core.excel_compatibility_processor.iter_excel_files")
    def test_compatibility_processor_list_target_files_matches_process_enumeration(
        self,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\b.xlsx", "C:\\tmp\\a.xlsx"]
        processor = ExcelCompatibilityProcessor()
        processor.set_folder_path("C:\\tmp")

        self.assertEqual(
            processor.list_target_files(),
            ["C:\\tmp\\b.xlsx", "C:\\tmp\\a.xlsx"],
        )

    @patch("core.excel_compatibility_processor.iter_excel_files")
    @patch("core.excel_compatibility_processor._load_dispatch")
    def test_compatibility_processor_set_log_callback_routes_logs(
        self,
        mock_dispatch,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx"]
        excel_app = MagicMock()
        excel_app.Workbooks.Open.side_effect = Exception("broken file")
        mock_dispatch.return_value = MagicMock(return_value=excel_app)

        logs = []
        processor = ExcelCompatibilityProcessor()
        processor.set_log_callback(logs.append)
        processor.set_folder_path("C:\\tmp")

        processed = processor.process_files()

        self.assertEqual(processed, 0)
        self.assertTrue(logs)
        self.assertTrue(any("compatibility_processor" in msg for msg in logs))
        excel_app.Quit.assert_called_once()

    @patch("core.excel_cleaner.iter_excel_files")
    @patch("core.excel_cleaner._load_win32com_client")
    @patch("builtins.print")
    def test_column_clearer_continues_on_error_and_releases_excel(
        self,
        _mock_print,
        mock_dispatch,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx", "C:\\tmp\\b.xlsx"]

        worksheet = MagicMock()
        worksheet.UsedRange.Rows.Count = 5
        clear_range = MagicMock()
        worksheet.Range.return_value = clear_range

        workbook = MagicMock()
        workbook.ActiveSheet = worksheet

        excel_app = MagicMock()
        excel_app.Workbooks.Open.side_effect = [workbook, Exception("broken file")]
        mock_dispatch.return_value = MagicMock(Dispatch=MagicMock(return_value=excel_app))

        clearer = ExcelColumnClearer()
        clearer.set_folder_path("C:\\tmp")
        clearer.set_column_number(2)

        processed = clearer.clear_column_in_files()

        self.assertEqual(processed, 2)
        worksheet.Range.assert_called_once()
        clear_range.ClearContents.assert_called_once()
        workbook.Save.assert_called_once()
        workbook.Close.assert_called_once()
        excel_app.Quit.assert_called_once()
        self.assertEqual(len(clearer.stats.errors), 1)

    @patch("core.excel_cleaner.iter_excel_files")
    @patch("core.excel_cleaner._load_win32com_client")
    def test_column_clearer_set_log_callback_routes_logs(
        self,
        mock_dispatch,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx"]

        worksheet = MagicMock()
        worksheet.UsedRange.Rows.Count = 5
        clear_range = MagicMock()
        worksheet.Range.return_value = clear_range

        workbook = MagicMock()
        workbook.ActiveSheet = worksheet
        excel_app = MagicMock()
        excel_app.Workbooks.Open.return_value = workbook
        mock_dispatch.return_value = MagicMock(Dispatch=MagicMock(return_value=excel_app))

        logs = []
        clearer = ExcelColumnClearer()
        clearer.set_log_callback(logs.append)
        clearer.set_folder_path("C:\\tmp")
        clearer.set_column_number(2)

        processed = clearer.clear_column_in_files()

        self.assertEqual(processed, 1)
        self.assertTrue(logs)
        self.assertTrue(any("Processing:" in msg for msg in logs))
        excel_app.Quit.assert_called_once()

    @patch("core.excel_cleaner.iter_excel_files")
    def test_column_clearer_list_target_files_matches_internal_listing(
        self,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx"]
        clearer = ExcelColumnClearer()
        clearer.set_folder_path("C:\\tmp")

        self.assertEqual(
            clearer.list_target_files(),
            clearer._list_target_files(),
        )

    @patch("core.excel_cleaner.iter_excel_files", return_value=[])
    @patch("core.excel_cleaner._load_win32com_client", side_effect=RuntimeError(CLEANER_COM_ERROR))
    def test_column_clearer_raises_clear_error_when_pywin32_is_missing(
        self,
        _mock_loader,
        _mock_iter_excel_files,
    ):
        clearer = ExcelColumnClearer()
        clearer.set_folder_path("C:\\tmp")
        clearer.set_column_number(2)

        with self.assertRaisesRegex(RuntimeError, "pywin32 is required"):
            clearer.clear_column_in_files()

    @patch("core.excel_compatibility_processor.iter_excel_files", return_value=[])
    @patch("core.excel_compatibility_processor._load_dispatch", side_effect=RuntimeError(COMPAT_COM_ERROR))
    def test_compatibility_processor_raises_clear_error_when_pywin32_is_missing(
        self,
        _mock_loader,
        _mock_iter_excel_files,
    ):
        processor = ExcelCompatibilityProcessor()
        processor.set_folder_path("C:\\tmp")

        with self.assertRaisesRegex(RuntimeError, "pywin32 is required"):
            processor.process_files()


if __name__ == "__main__":
    unittest.main()
