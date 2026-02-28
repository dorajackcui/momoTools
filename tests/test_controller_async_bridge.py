import unittest

from controller_modules.base import BaseController
from ui import strings


class FakeDialogs:
    def __init__(self):
        self.infos = []
        self.errors = []
        self.warnings = []

    def info(self, title, message):
        self.infos.append((title, message))

    def error(self, title, message):
        self.errors.append((title, message))

    def warning(self, title, message):
        self.warnings.append((title, message))


class BusyRunner:
    def run(self, task_name, action, on_success, on_error):
        return False


class SyncRunner:
    def __init__(self):
        self.task_names = []

    def run(self, task_name, action, on_success, on_error):
        self.task_names.append(task_name)
        try:
            on_success(action())
        except Exception as exc:
            on_error(exc)
        return True


class ControllerAsyncBridgeTestCase(unittest.TestCase):
    def test_run_action_warns_when_task_is_already_running(self):
        dialogs = FakeDialogs()
        controller = BaseController(frame=object(), dialog_service=dialogs, task_runner=BusyRunner())

        result = controller._run_action_or_notify(lambda: 1, task_name="Any")

        self.assertIsNone(result)
        self.assertEqual(
            dialogs.warnings,
            [(strings.WARNING_TITLE, strings.TASK_ALREADY_RUNNING)],
        )

    def test_run_action_keeps_success_callback_behavior(self):
        dialogs = FakeDialogs()
        runner = SyncRunner()
        controller = BaseController(frame=object(), dialog_service=dialogs, task_runner=runner)

        result = controller._run_action_or_notify(
            lambda: 5,
            on_success=lambda value: dialogs.info(strings.SUCCESS_TITLE, f"updated={value}"),
            task_name="Master->Target",
        )

        self.assertEqual(result, 5)
        self.assertEqual(runner.task_names, ["Master->Target"])
        self.assertEqual(dialogs.infos, [(strings.SUCCESS_TITLE, "updated=5")])
        self.assertEqual(dialogs.errors, [])

    def test_run_action_keeps_custom_error_title(self):
        dialogs = FakeDialogs()
        runner = SyncRunner()
        controller = BaseController(frame=object(), dialog_service=dialogs, task_runner=runner)

        def bad_action():
            raise RuntimeError("boom")

        result = controller._run_action_or_notify(
            bad_action,
            error_title="处理失败",
            task_name="Target->Master",
        )

        self.assertIsNone(result)
        self.assertEqual(runner.task_names, ["Target->Master"])
        self.assertEqual(dialogs.errors, [("处理失败", "boom")])


if __name__ == "__main__":
    unittest.main()
