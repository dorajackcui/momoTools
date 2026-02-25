import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

import app


class AppSmokeTestCase(unittest.TestCase):
    @patch("app.ExcelUpdaterApp.init_components")
    @patch("app.ExcelUpdaterApp.init_processors")
    @patch("app.ExcelUpdaterApp.setup_style")
    @patch("app.ttk.Notebook")
    @patch("app.tk.Tk")
    def test_app_constructs_without_error(
        self,
        mock_tk,
        mock_notebook,
        mock_setup_style,
        mock_init_processors,
        mock_init_components,
    ):
        root = MagicMock()
        notebook = MagicMock()
        mock_tk.return_value = root
        mock_notebook.return_value = notebook

        instance = app.ExcelUpdaterApp()

        self.assertIsNotNone(instance)
        root.title.assert_called_once_with("Momo——Build your mastersheet")
        root.geometry.assert_called_once_with("540x680")
        root.minsize.assert_called_once_with(520, 640)
        root.resizable.assert_called_once_with(True, True)
        notebook.pack.assert_called_once()
        mock_setup_style.assert_called_once()
        mock_init_processors.assert_called_once()
        mock_init_components.assert_called_once()

    def test_main_tools_tab_no_longer_contains_multi_column_entry(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertNotIn("main_notebook.add(multi_frame, text='多列更新')", source)
        self.assertIn("UpdaterController(None, self.excel_processor, self.multi_processor)", source)
        self.assertNotIn("_build_outer_tab_icons", source)
        self.assertNotIn("PhotoImage", source)


if __name__ == "__main__":
    unittest.main()
