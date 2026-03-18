import unittest
from unittest.mock import MagicMock, patch

import app


def _startup_dependency_error():
    required_modules = (
        "core.excel_processor",
        "core.multi_column_processor",
        "core.terminology",
        "core.untranslated_stats_processor",
    )
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ModuleNotFoundError as exc:
            return str(exc)
    return None


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
        root.geometry.assert_called_once_with("540x700")
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
        root.protocol.assert_called_once_with("WM_DELETE_WINDOW", instance._on_root_close)
        root.after.assert_called_once()
        mock_setup_style.assert_called_once()
        mock_init_processors.assert_called_once()
        mock_init_components.assert_called_once()

    @patch("app.ExcelUpdaterApp.init_components")
    @patch("app.ExcelUpdaterApp.setup_style")
    @patch("app.ttk.Button")
    @patch("app.ttk.Label")
    @patch("app.ttk.Frame")
    @patch("app.ttk.Notebook")
    @patch("app.tk.StringVar")
    @patch("app.tk.Tk")
    def test_app_constructs_with_real_processor_initialization_when_dependencies_are_installed(
        self,
        mock_tk,
        mock_string_var,
        mock_notebook,
        mock_status_frame,
        mock_status_label,
        mock_view_logs_button,
        mock_setup_style,
        mock_init_components,
    ):
        dependency_error = _startup_dependency_error()
        if dependency_error is not None:
            self.skipTest(f"startup dependencies unavailable: {dependency_error}")

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

        self.assertIsNotNone(instance.excel_processor)
        self.assertIsNotNone(instance.multi_processor)
        self.assertIsNotNone(instance.reverse_excel_processor)
        self.assertIsNotNone(instance.clearer)
        self.assertIsNotNone(instance.compatibility_processor)
        self.assertIsNotNone(instance.deep_replace_processor)
        self.assertIsNotNone(instance.master_merge_processor)
        self.assertIsNotNone(instance.untranslated_stats_processor)
        self.assertIsNotNone(instance.terminology_processor)
        self.assertIsInstance(instance.task_runner, app.TkSingleTaskRunner)
        root.protocol.assert_called_once_with("WM_DELETE_WINDOW", instance._on_root_close)
        mock_setup_style.assert_called_once()
        mock_init_components.assert_called_once()
        root.after.assert_called_once()

    def test_registry_contains_expected_tabs_and_no_multi_tab(self):
        instance = app.ExcelUpdaterApp.__new__(app.ExcelUpdaterApp)
        instance.excel_processor = object()
        instance.multi_processor = object()
        instance.reverse_excel_processor = object()
        instance.clearer = object()
        instance.compatibility_processor = object()
        instance.deep_replace_processor = object()
        instance.master_merge_processor = object()
        instance.untranslated_stats_processor = object()
        instance.terminology_processor = object()
        instance.task_runner = object()

        specs = instance._build_tool_specs()

        self.assertEqual(
            [spec.group for spec in specs],
            [
                "main",
                "main",
                "main",
                "utilities",
                "utilities",
                "utilities",
                "utilities",
                "utilities",
                "update_master",
                "update_master",
                "update_master",
                "update_master",
            ],
        )
        self.assertEqual(
            [spec.tab_text for spec in specs],
            [
                "Master->Target",
                "Target->Master",
                "Batch",
                "Column Clear",
                "Compatibility",
                "Deep Replace",
                "Untranslated Stats",
                "Term Extractor",
                "Merge Masters",
                "Source Text",
                "Translation",
                "Source+Translation",
            ],
        )
        self.assertNotIn("Multi Column", [spec.tab_text for spec in specs])


if __name__ == "__main__":
    unittest.main()
