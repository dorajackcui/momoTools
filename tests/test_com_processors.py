import unittest
from unittest.mock import MagicMock, patch

try:
    from core.excel_cleaner import ExcelColumnClearer
    from core.excel_compatibility_processor import ExcelCompatibilityProcessor
except Exception:  # pragma: no cover - environment-dependent import guard
    ExcelColumnClearer = None
    ExcelCompatibilityProcessor = None


@unittest.skipIf(
    ExcelColumnClearer is None or ExcelCompatibilityProcessor is None,
    "win32com is unavailable in this environment",
)
class ComProcessorsTestCase(unittest.TestCase):
    @patch("core.excel_compatibility_processor.iter_excel_files")
    @patch("core.excel_compatibility_processor.Dispatch")
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
        mock_dispatch.return_value = excel_app

        processor = ExcelCompatibilityProcessor()
        processor.set_folder_path("C:\\tmp")

        processed = processor.process_files()

        self.assertEqual(processed, 1)
        workbook.Save.assert_called_once()
        workbook.Close.assert_called_once()
        excel_app.Quit.assert_called_once()
        self.assertEqual(len(processor.stats.errors), 1)

    @patch("core.excel_compatibility_processor.iter_excel_files")
    @patch("core.excel_compatibility_processor.Dispatch")
    def test_compatibility_processor_set_log_callback_routes_logs(
        self,
        mock_dispatch,
        mock_iter_excel_files,
    ):
        mock_iter_excel_files.return_value = ["C:\\tmp\\a.xlsx"]
        excel_app = MagicMock()
        excel_app.Workbooks.Open.side_effect = Exception("broken file")
        mock_dispatch.return_value = excel_app

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
    @patch("core.excel_cleaner.win32com.client.Dispatch")
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
        mock_dispatch.return_value = excel_app

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
    @patch("core.excel_cleaner.win32com.client.Dispatch")
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
        mock_dispatch.return_value = excel_app

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


if __name__ == "__main__":
    unittest.main()
