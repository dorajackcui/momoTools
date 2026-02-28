import unittest
from unittest.mock import MagicMock, patch

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
        root.title.assert_called_once_with("Momo build your mastersheet")
        root.geometry.assert_called_once_with("540x680")
        root.minsize.assert_called_once_with(520, 640)
        root.resizable.assert_called_once_with(True, True)
        notebook.pack.assert_called_once()
        mock_setup_style.assert_called_once()
        mock_init_processors.assert_called_once()
        mock_init_components.assert_called_once()

    def test_registry_contains_expected_tabs_and_no_multi_tab(self):
        instance = app.ExcelUpdaterApp.__new__(app.ExcelUpdaterApp)
        instance.excel_processor = object()
        instance.multi_processor = object()
        instance.reverse_excel_processor = object()
        instance.clearer = object()
        instance.compatibility_processor = object()
        instance.deep_replace_processor = object()
        instance.untranslated_stats_processor = object()
        instance.terminology_processor = object()

        specs = instance._build_tool_specs()

        self.assertEqual(
            [spec.group for spec in specs],
            ["main", "main", "utilities", "utilities", "utilities", "utilities", "utilities"],
        )
        self.assertEqual(
            [spec.tab_text for spec in specs],
            [
                "Master->Target",
                "Target->Master",
                "Column Clear",
                "Compatibility",
                "Deep Replace",
                "Untranslated Stats",
                "Term Extractor",
            ],
        )
        self.assertNotIn("Multi Column", [spec.tab_text for spec in specs])


if __name__ == "__main__":
    unittest.main()
