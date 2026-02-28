import unittest
from unittest.mock import MagicMock, patch

from ui.widgets.log_window import LogWindow


class LogWindowTestCase(unittest.TestCase):
    @patch("ui.widgets.log_window.ttk.Button")
    @patch("ui.widgets.log_window.ttk.Scrollbar")
    @patch("ui.widgets.log_window.tk.Text")
    @patch("ui.widgets.log_window.ttk.Frame")
    @patch("ui.widgets.log_window.tk.Toplevel")
    def test_show_creates_once_and_reuses_existing_window(
        self,
        mock_toplevel,
        mock_frame,
        mock_text,
        mock_scrollbar,
        _mock_button,
    ):
        root = MagicMock()
        window_widget = MagicMock()
        window_widget.winfo_exists.return_value = True
        mock_toplevel.return_value = window_widget
        mock_frame.side_effect = [MagicMock(), MagicMock()]
        text_widget = MagicMock()
        mock_text.return_value = text_widget
        scrollbar_widget = MagicMock()
        mock_scrollbar.return_value = scrollbar_widget

        window = LogWindow(root)
        window.show()
        window.show()

        self.assertEqual(mock_toplevel.call_count, 1)
        window_widget.deiconify.assert_called_once()
        window_widget.lift.assert_called_once()
        window_widget.focus_force.assert_called_once()

    @patch("ui.widgets.log_window.ttk.Button")
    @patch("ui.widgets.log_window.ttk.Scrollbar")
    @patch("ui.widgets.log_window.tk.Text")
    @patch("ui.widgets.log_window.ttk.Frame")
    @patch("ui.widgets.log_window.tk.Toplevel")
    def test_set_all_and_append_lines_write_text(
        self,
        mock_toplevel,
        mock_frame,
        mock_text,
        mock_scrollbar,
        _mock_button,
    ):
        root = MagicMock()
        window_widget = MagicMock()
        window_widget.winfo_exists.return_value = True
        mock_toplevel.return_value = window_widget
        mock_frame.side_effect = [MagicMock(), MagicMock()]
        text_widget = MagicMock()
        text_widget.yview = MagicMock()
        mock_text.return_value = text_widget
        mock_scrollbar.return_value = MagicMock()

        window = LogWindow(root)
        window.show()
        window.set_all(["A", "B"])
        window.append_lines(["C"])

        text_widget.delete.assert_called_with("1.0", "end")
        self.assertIn(("end", "A\nB\n"), [call.args for call in text_widget.insert.call_args_list])
        self.assertIn(("end", "C\n"), [call.args for call in text_widget.insert.call_args_list])

    @patch("ui.widgets.log_window.ttk.Button")
    @patch("ui.widgets.log_window.ttk.Scrollbar")
    @patch("ui.widgets.log_window.tk.Text")
    @patch("ui.widgets.log_window.ttk.Frame")
    @patch("ui.widgets.log_window.tk.Toplevel")
    def test_clear_calls_callback_and_close_resets_state(
        self,
        mock_toplevel,
        mock_frame,
        mock_text,
        mock_scrollbar,
        _mock_button,
    ):
        root = MagicMock()
        on_clear = MagicMock()
        window_widget = MagicMock()
        window_widget.winfo_exists.return_value = True
        mock_toplevel.return_value = window_widget
        mock_frame.side_effect = [MagicMock(), MagicMock()]
        text_widget = MagicMock()
        text_widget.yview = MagicMock()
        mock_text.return_value = text_widget
        mock_scrollbar.return_value = MagicMock()

        window = LogWindow(root, on_clear=on_clear)
        window.show()
        window.clear()
        on_clear.assert_called_once()

        close_callback = window_widget.protocol.call_args.args[1]
        close_callback()
        self.assertFalse(window.is_alive())
        window_widget.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
