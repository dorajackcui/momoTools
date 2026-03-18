import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

from controller_modules.task_runner import InlineTaskRunner, TkSingleTaskRunner


class FakeRoot:
    pass


def wait_until(predicate, timeout_seconds=1.5):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class TaskRunnerTestCase(unittest.TestCase):
    def test_inline_task_runner_success(self):
        runner = InlineTaskRunner()
        results = []
        errors = []

        started = runner.run("sample", lambda: 42, results.append, errors.append)

        self.assertTrue(started)
        self.assertEqual(results, [42])
        self.assertEqual(errors, [])

    def test_inline_task_runner_error(self):
        runner = InlineTaskRunner()
        results = []
        errors = []

        def bad_action():
            raise RuntimeError("boom")

        started = runner.run("sample", bad_action, results.append, errors.append)

        self.assertTrue(started)
        self.assertEqual(results, [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "boom")

    def test_tk_single_task_runner_defers_completion_until_main_thread_drain(self):
        busy_states = []
        statuses = []
        results = []
        errors = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=busy_states.append,
            set_status=statuses.append,
        )

        self.assertTrue(runner.run("Master->Target", lambda: 7, results.append, errors.append))
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: Master->Target"])
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))

        self.assertEqual(results, [])
        self.assertEqual(errors, [])
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: Master->Target"])
        self.assertFalse(runner.run("Blocked", lambda: 8, results.append, errors.append))

        runner.drain_pending_completions()

        self.assertEqual(results, [7])
        self.assertEqual(errors, [])
        self.assertEqual(busy_states, [True, False])
        self.assertEqual(statuses, ["Running: Master->Target", "Done: Master->Target"])
        self.assertTrue(runner.run("AfterDrain", lambda: 9, results.append, errors.append))
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))
        runner.drain_pending_completions()

    def test_tk_single_task_runner_failure_drains_on_main_thread_and_releases_busy(self):
        busy_states = []
        statuses = []
        errors = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=busy_states.append,
            set_status=statuses.append,
        )

        def bad_action():
            raise ValueError("x")

        self.assertTrue(runner.run("Stats", bad_action, lambda _r: None, errors.append))
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))

        self.assertEqual(errors, [])
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: Stats"])

        runner.drain_pending_completions()

        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "x")
        self.assertEqual(busy_states, [True, False])
        self.assertEqual(statuses, ["Running: Stats", "Failed: Stats"])
        self.assertTrue(runner.run("AfterError", lambda: 9, lambda _r: None, lambda _e: None))
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))
        runner.drain_pending_completions()

    def test_tk_single_task_runner_shutdown_before_completion_skips_ui_callbacks(self):
        busy_states = []
        statuses = []
        results = []
        errors = []
        diagnostics = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=busy_states.append,
            set_status=statuses.append,
            diagnostic_sink=diagnostics.append,
        )
        started_event = threading.Event()
        release_event = threading.Event()

        def long_action():
            started_event.set()
            release_event.wait(timeout=1.0)
            return 5

        self.assertTrue(runner.run("ShutdownTask", long_action, results.append, errors.append))
        self.assertTrue(started_event.wait(timeout=1.0))

        runner.shutdown()
        release_event.set()

        self.assertTrue(wait_until(lambda: not runner._running))
        self.assertEqual(results, [])
        self.assertEqual(errors, [])
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: ShutdownTask"])
        self.assertTrue(
            any("TASKRUNNER_UI_COMPLETION_SKIPPED: ShutdownTask" in message for message in diagnostics)
        )

    def test_tk_single_task_runner_shutdown_drops_queued_completion_without_ui_callbacks(self):
        busy_states = []
        statuses = []
        results = []
        diagnostics = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=busy_states.append,
            set_status=statuses.append,
            diagnostic_sink=diagnostics.append,
        )

        self.assertTrue(runner.run("QueuedTask", lambda: 11, results.append, lambda _e: None))
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))

        runner.shutdown()

        self.assertEqual(runner._completion_queue.qsize(), 0)
        self.assertFalse(runner._running)
        self.assertEqual(results, [])
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: QueuedTask"])
        self.assertTrue(any("TASKRUNNER_UI_COMPLETION_SKIPPED: QueuedTask" in message for message in diagnostics))

    def test_tk_single_task_runner_logs_callback_errors_and_still_releases_busy(self):
        busy_states = []
        statuses = []
        diagnostics = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=busy_states.append,
            set_status=statuses.append,
            diagnostic_sink=diagnostics.append,
        )

        def bad_success(_result):
            raise RuntimeError("callback-boom")

        self.assertTrue(runner.run("CallbackTask", lambda: 3, bad_success, lambda _e: None))
        self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))

        runner.drain_pending_completions()

        self.assertEqual(busy_states, [True, False])
        self.assertEqual(statuses, ["Running: CallbackTask", "Done: CallbackTask"])
        self.assertFalse(runner._running)
        self.assertTrue(any("TASKRUNNER_UI_CALLBACK_ERROR: CallbackTask" in message for message in diagnostics))

    def test_tk_single_task_runner_calls_pythoncom_when_available(self):
        events = []
        runner = TkSingleTaskRunner(
            root=FakeRoot(),
            set_busy=lambda _value: None,
            set_status=lambda _value: None,
        )
        fake_pythoncom = types.SimpleNamespace(
            CoInitialize=lambda: events.append("init"),
            CoUninitialize=lambda: events.append("uninit"),
        )

        with patch.dict(sys.modules, {"pythoncom": fake_pythoncom}):
            self.assertTrue(
                runner.run(
                    "COM",
                    lambda: events.append("action"),
                    lambda _result: events.append("success"),
                    lambda _error: events.append("error"),
                )
            )
            self.assertTrue(wait_until(lambda: runner._completion_queue.qsize() == 1))
            runner.drain_pending_completions()

        self.assertEqual(events[:3], ["init", "action", "uninit"])
        self.assertIn("success", events)
        self.assertNotIn("error", events)


if __name__ == "__main__":
    unittest.main()
