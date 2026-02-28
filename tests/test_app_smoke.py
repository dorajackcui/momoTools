import unittest
from unittest.mock import MagicMock, patch

import app


class AppSmokeTestCase(unittest.TestCase):
    @patch("app.ExcelUpdaterApp.init_components")
    @patch("app.ExcelUpdaterApp.init_processors")
    @patch("app.ExcelUpdaterApp.setup_style")
    @patch("app.ttk.Button")
    @patch("app.ttk.Label")
    @patch("app.ttk.Frame")
    @patch("app.ttk.Notebook")
    @patch("app.tk.StringVar")
    @patch("app.tk.Tk")
    def test_app_constructs_without_error(
        self,
        mock_tk,
        mock_string_var,
        mock_notebook,
        mock_status_frame,
        mock_status_label,
        mock_view_logs_button,
        mock_setup_style,
        mock_init_processors,
        mock_init_components,
    ):
        root = MagicMock()
        notebook = MagicMock()
        status_row = MagicMock()
        status_var = MagicMock()
        status_label = MagicMock()
        view_logs_button = MagicMock()
        mock_tk.return_value = root
        mock_string_var.return_value = status_var
        mock_notebook.return_value = notebook
        mock_status_frame.return_value = status_row
        mock_status_label.return_value = status_label
        mock_view_logs_button.return_value = view_logs_button

        instance = app.ExcelUpdaterApp()

        self.assertIsNotNone(instance)
        root.title.assert_called_once_with("Momo build your mastersheet")
        root.geometry.assert_called_once_with("540x680")
        root.minsize.assert_called_once_with(520, 640)
        root.resizable.assert_called_once_with(True, True)
        notebook.pack.assert_called_once()
        mock_status_frame.assert_called_once_with(root, style="App.TFrame")
        status_row.pack.assert_called_once()
        mock_string_var.assert_called_once_with(value="Ready")
        mock_status_label.assert_called_once_with(status_row, textvariable=status_var, anchor="w")
        status_label.pack.assert_called_once()
        self.assertTrue(mock_view_logs_button.called)
        args, kwargs = mock_view_logs_button.call_args
        self.assertIs(args[0], status_row)
        self.assertEqual(kwargs["text"], app.strings.VIEW_LOGS_BUTTON)
        self.assertEqual(kwargs["takefocus"], False)
        view_logs_button.pack.assert_called_once()
        root.after.assert_called_once()
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
        instance.task_runner = object()

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
