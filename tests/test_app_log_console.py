import collections
import queue
import threading
import unittest
from unittest.mock import MagicMock, patch

import app


class FakeLogWindow:
    def __init__(self, _root, *, title, on_clear):
        self.title = title
        self.on_clear = on_clear
        self.shown = 0
        self.all_lines = []
        self.appended = []
        self.alive = True

    def show(self):
        self.shown += 1

    def set_all(self, lines):
        self.all_lines = list(lines)

    def append_lines(self, lines):
        self.appended.extend(lines)

    def is_alive(self):
        return self.alive


class AppLogConsoleTestCase(unittest.TestCase):
    def _make_app_stub(self):
        instance = app.ExcelUpdaterApp.__new__(app.ExcelUpdaterApp)
        instance.root = MagicMock()
        instance.status_var = MagicMock()
        instance._task_status_text = "Ready"
        instance._latest_log_line = ""
        instance._log_queue = queue.Queue()
        instance._log_buffer = collections.deque(maxlen=2000)
        instance._log_window = None
        return instance

    def test_emit_log_is_thread_safe_and_drain_updates_buffer(self):
        instance = self._make_app_stub()

        thread = threading.Thread(target=lambda: instance._emit_log("worker-log"))
        thread.start()
        thread.join(timeout=1.0)

        self.assertEqual(instance._log_queue.qsize(), 1)
        instance._drain_log_queue()

        self.assertEqual(len(instance._log_buffer), 1)
        line = instance._log_buffer[0]
        self.assertTrue(line.startswith("["))
        self.assertIn("worker-log", line)
        self.assertTrue(instance.status_var.set.called)
        instance.root.after.assert_called_once()

    def test_drain_log_queue_drains_task_runner_before_processing_logs(self):
        instance = self._make_app_stub()
        instance.task_runner = MagicMock()
        instance._emit_log("queued-before-drain")

        def drain_runner():
            instance._emit_log("queued-by-runner-drain")

        instance.task_runner.drain_pending_completions.side_effect = drain_runner

        instance._drain_log_queue()

        self.assertEqual(len(instance._log_buffer), 2)
        self.assertTrue(instance._log_buffer[0].endswith("queued-before-drain"))
        self.assertTrue(instance._log_buffer[1].endswith("queued-by-runner-drain"))
        instance.task_runner.drain_pending_completions.assert_called_once_with()
        instance.root.after.assert_called_once()

    def test_open_log_window_replays_history_and_receives_incremental_logs(self):
        instance = self._make_app_stub()
        instance._log_buffer.extend(["[10:00:00] A", "[10:00:01] B"])

        with patch("app.LogWindow", FakeLogWindow):
            instance._open_log_window()
            self.assertIsNotNone(instance._log_window)
            self.assertEqual(instance._log_window.shown, 1)
            self.assertEqual(instance._log_window.all_lines, ["[10:00:00] A", "[10:00:01] B"])

            instance._emit_log("C")
            instance._drain_log_queue()

            self.assertTrue(any(line.endswith("C") for line in instance._log_window.appended))

    def test_log_buffer_keeps_recent_2000_lines(self):
        instance = self._make_app_stub()

        for i in range(2005):
            instance._emit_log(f"line {i}")
        instance._drain_log_queue()

        self.assertEqual(len(instance._log_buffer), 2000)
        self.assertFalse(any(line.endswith("line 0") for line in instance._log_buffer))
        self.assertTrue(any(line.endswith("line 2004") for line in instance._log_buffer))

    def test_running_status_has_priority_over_latest_log_summary(self):
        instance = self._make_app_stub()

        instance._set_status_text("Running: Master->Target")
        instance._emit_log("detail message")
        instance._drain_log_queue()

        latest_status = instance.status_var.set.call_args_list[-1].args[0]
        self.assertEqual(latest_status, "Running: Master->Target")

        instance._set_status_text("Ready")
        instance._emit_log("ready-detail")
        instance._drain_log_queue()
        latest_status = instance.status_var.set.call_args_list[-1].args[0]
        self.assertTrue(latest_status.endswith("ready-detail"))

    def test_root_close_shuts_down_task_runner_before_destroy(self):
        instance = self._make_app_stub()
        instance.task_runner = MagicMock()

        instance._on_root_close()

        instance.task_runner.shutdown.assert_called_once_with()
        instance.root.destroy.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
