import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

from controller_modules.task_runner import InlineTaskRunner, TkSingleTaskRunner


class FakeRoot:
    def __init__(self):
        self._callbacks = []
        self._lock = threading.Lock()

    def after(self, _delay_ms, callback):
        with self._lock:
            self._callbacks.append(callback)

    def callback_count(self):
        with self._lock:
            return len(self._callbacks)

    def flush_callbacks(self):
        while True:
            with self._lock:
                if not self._callbacks:
                    return
                callback = self._callbacks.pop(0)
            callback()


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

    def test_tk_single_task_runner_runs_in_background_and_dispatches_back(self):
        root = FakeRoot()
        busy_states = []
        statuses = []
        results = []
        errors = []
        runner = TkSingleTaskRunner(
            root=root,
            set_busy=busy_states.append,
            set_status=statuses.append,
        )

        started = runner.run("Master->Target", lambda: 7, results.append, errors.append)
        self.assertTrue(started)
        self.assertEqual(busy_states, [True])
        self.assertEqual(statuses, ["Running: Master->Target"])

        self.assertTrue(wait_until(lambda: root.callback_count() > 0))
        root.flush_callbacks()

        self.assertEqual(results, [7])
        self.assertEqual(errors, [])
        self.assertEqual(busy_states, [True, False])
        self.assertEqual(statuses, ["Running: Master->Target", "Done: Master->Target"])

    def test_tk_single_task_runner_busy_lock_blocks_second_task(self):
        root = FakeRoot()
        runner = TkSingleTaskRunner(
            root=root,
            set_busy=lambda _value: None,
            set_status=lambda _value: None,
        )
        started_event = threading.Event()
        release_event = threading.Event()

        def long_action():
            started_event.set()
            release_event.wait(timeout=1.0)
            return 1

        self.assertTrue(runner.run("Task A", long_action, lambda _r: None, lambda _e: None))
        self.assertTrue(started_event.wait(timeout=1.0))
        self.assertFalse(runner.run("Task B", lambda: 2, lambda _r: None, lambda _e: None))

        release_event.set()
        self.assertTrue(wait_until(lambda: root.callback_count() > 0))
        root.flush_callbacks()

        self.assertTrue(runner.run("Task C", lambda: 3, lambda _r: None, lambda _e: None))
        self.assertTrue(wait_until(lambda: root.callback_count() > 0))
        root.flush_callbacks()

    def test_tk_single_task_runner_exception_still_releases_busy(self):
        root = FakeRoot()
        busy_states = []
        statuses = []
        errors = []
        runner = TkSingleTaskRunner(
            root=root,
            set_busy=busy_states.append,
            set_status=statuses.append,
        )

        def bad_action():
            raise ValueError("x")

        self.assertTrue(runner.run("Stats", bad_action, lambda _r: None, errors.append))
        self.assertTrue(wait_until(lambda: root.callback_count() > 0))
        root.flush_callbacks()

        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "x")
        self.assertEqual(busy_states, [True, False])
        self.assertEqual(statuses, ["Running: Stats", "Failed: Stats"])

        # Busy state must be released after failure.
        self.assertTrue(runner.run("AfterError", lambda: 9, lambda _r: None, lambda _e: None))
        self.assertTrue(wait_until(lambda: root.callback_count() > 0))
        root.flush_callbacks()

    def test_tk_single_task_runner_calls_pythoncom_when_available(self):
        root = FakeRoot()
        events = []
        runner = TkSingleTaskRunner(
            root=root,
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
            self.assertTrue(wait_until(lambda: root.callback_count() > 0))
            root.flush_callbacks()

        self.assertEqual(events[:3], ["init", "action", "uninit"])
        self.assertIn("success", events)
        self.assertNotIn("error", events)


if __name__ == "__main__":
    unittest.main()
