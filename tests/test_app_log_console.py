import collections
import queue
import threading
import time
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


class BrokenBusyWidget:
    _processing_action = True

    def configure(self, **_kwargs):
        raise RuntimeError("configure-boom")

    def state(self, _value):
        raise RuntimeError("state-boom")


class BusyTrackingWidget:
    _processing_action = True

    def __init__(self):
        self.state_value = "normal"

    def configure(self, **kwargs):
        self.state_value = kwargs["state"]


def wait_until(predicate, timeout_seconds=1.5):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


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
        instance._closing = False
        instance._app_diagnostic_once_keys = set()
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

        self.assertTrue(instance._closing)
        instance.task_runner.shutdown.assert_called_once_with()
        instance.root.destroy.assert_called_once_with()

    def test_drain_log_queue_logs_schedule_failure_once_when_not_closing(self):
        instance = self._make_app_stub()
        instance.root.after.side_effect = RuntimeError("after-boom")

        instance._drain_log_queue()
        instance._drain_log_queue()

        matching = [line for line in instance._log_buffer if "APP_LOG_PUMP_SCHEDULE_FAILED" in line]
        self.assertEqual(len(matching), 1)
        self.assertIn("RuntimeError", matching[0])

    def test_drain_log_queue_ignores_schedule_failure_while_closing(self):
        instance = self._make_app_stub()
        instance._closing = True
        instance.root.after.side_effect = RuntimeError("after-boom")

        instance._drain_log_queue()

        self.assertFalse(any("APP_LOG_PUMP_SCHEDULE_FAILED" in line for line in instance._log_buffer))

    def test_set_processing_busy_logs_widget_diagnostic_when_all_state_paths_fail(self):
        instance = self._make_app_stub()
        instance._iter_descendants = MagicMock(return_value=iter([BrokenBusyWidget()]))

        instance._set_processing_busy(True)
        instance._drain_log_queue()

        matching = [line for line in instance._log_buffer if "APP_WIDGET_BUSY_STATE_FAILED" in line]
        self.assertEqual(len(matching), 1)
        self.assertIn("BrokenBusyWidget", matching[0])
        self.assertIn("target_state=disabled", matching[0])
        self.assertIn("RuntimeError", matching[0])

    def test_drain_log_queue_delivers_task_completion_on_drain_thread_before_logging_schedule_failure(self):
        instance = self._make_app_stub()
        busy_widget = BusyTrackingWidget()
        instance._iter_descendants = MagicMock(side_effect=lambda _root: iter([busy_widget]))
        instance.root.after.side_effect = RuntimeError("after-boom")
        instance.task_runner = app.TkSingleTaskRunner(
            root=instance.root,
            set_busy=instance._set_processing_busy,
            set_status=instance._set_status_text,
            diagnostic_sink=instance._emit_log,
        )

        action_thread_ids = []
        callback_thread_ids = []
        results = []
        errors = []

        def action():
            action_thread_ids.append(threading.get_ident())
            return 7

        def on_success(result):
            callback_thread_ids.append(threading.get_ident())
            results.append(result)

        self.assertTrue(instance.task_runner.run("DrainTask", action, on_success, errors.append))
        self.assertEqual(instance._task_status_text, "Running: DrainTask")
        self.assertEqual(busy_widget.state_value, "disabled")
        self.assertTrue(wait_until(lambda: instance.task_runner._completion_queue.qsize() == 1))

        self.assertEqual(results, [])
        self.assertEqual(errors, [])
        self.assertEqual(callback_thread_ids, [])

        drain_thread_id = threading.get_ident()
        instance._drain_log_queue()

        self.assertEqual(results, [7])
        self.assertEqual(errors, [])
        self.assertEqual(callback_thread_ids, [drain_thread_id])
        self.assertNotEqual(action_thread_ids, callback_thread_ids)
        self.assertFalse(instance.task_runner._running)
        self.assertEqual(instance._task_status_text, "Done: DrainTask")
        self.assertEqual(busy_widget.state_value, "normal")

        instance._drain_log_queue()

        matching = [line for line in instance._log_buffer if "APP_LOG_PUMP_SCHEDULE_FAILED" in line]
        self.assertEqual(len(matching), 1)
        self.assertTrue(any(line.endswith("Running: DrainTask") for line in instance._log_buffer))
        self.assertTrue(any(line.endswith("Done: DrainTask") for line in instance._log_buffer))


if __name__ == "__main__":
    unittest.main()
