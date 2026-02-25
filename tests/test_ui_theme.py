import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

from ui.theme import configure_ttk_style


class ThemeStyleTestCase(unittest.TestCase):
    @patch("ui.theme.ttk.Style")
    def test_configure_ttk_style_prefers_vista_and_registers_minimal_styles(self, mock_style_cls):
        style = MagicMock()
        mock_style_cls.return_value = style

        configure_ttk_style()

        style.theme_use.assert_called_once_with("vista")

        configured = [call.args[0] for call in style.configure.call_args_list if call.args]
        for style_name in (
            "App.TFrame",
            "Surface.TFrame",
            "Surface.TLabel",
            "SurfaceMuted.TLabel",
            "Status.TLabel",
            "Primary.TButton",
        ):
            self.assertIn(style_name, configured)

        mapped = [call.args[0] for call in style.map.call_args_list if call.args]
        self.assertIn("Primary.TButton", mapped)

    @patch("ui.theme.ttk.Style")
    def test_configure_ttk_style_falls_back_to_default_when_vista_unavailable(self, mock_style_cls):
        style = MagicMock()
        style.theme_use.side_effect = [tk.TclError("no vista"), None]
        mock_style_cls.return_value = style

        configure_ttk_style()

        self.assertEqual(style.theme_use.call_args_list[0].args[0], "vista")
        self.assertEqual(style.theme_use.call_args_list[1].args[0], "default")


if __name__ == "__main__":
    unittest.main()
