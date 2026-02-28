import unittest

from controller_modules.base import BaseController
from ui import strings
from ui.validators import ValidationError


class FakeDialogs:
    def __init__(self):
        self.errors = []

    def error(self, title, message):
        self.errors.append((title, message))


class FakeFrame:
    def __init__(self, config=None):
        self._config = config

    def get_config(self):
        if isinstance(self._config, Exception):
            raise self._config
        return self._config


class BaseControllerTemplateTestCase(unittest.TestCase):
    def test_ensure_required_values_reports_error(self):
        dialogs = FakeDialogs()
        controller = BaseController(FakeFrame(), dialog_service=dialogs)

        ok = controller._ensure_required_values([(False, "missing required value")])

        self.assertFalse(ok)
        self.assertEqual(dialogs.errors[0], (strings.ERROR_TITLE, "missing required value"))

    def test_get_config_or_notify_validation_error_prefix(self):
        dialogs = FakeDialogs()
        controller = BaseController(
            FakeFrame(ValidationError("bad config")),
            dialog_service=dialogs,
        )

        config = controller._get_config_or_notify()

        self.assertIsNone(config)
        self.assertEqual(dialogs.errors[0][0], strings.ERROR_TITLE)
        self.assertIn(strings.VALIDATION_CONFIG_PREFIX, dialogs.errors[0][1])

    def test_run_action_or_notify_uses_custom_error_title(self):
        dialogs = FakeDialogs()
        controller = BaseController(FakeFrame(), dialog_service=dialogs)

        def bad_action():
            raise RuntimeError("boom")

        result = controller._run_action_or_notify(bad_action, error_title="处理失败")

        self.assertIsNone(result)
        self.assertEqual(dialogs.errors[0], ("处理失败", "boom"))

    def test_run_action_or_notify_calls_success_callback(self):
        dialogs = FakeDialogs()
        controller = BaseController(FakeFrame(), dialog_service=dialogs)
        seen = []

        def on_success(value):
            seen.append(value)

        result = controller._run_action_or_notify(lambda: 42, on_success=on_success)

        self.assertEqual(result, 42)
        self.assertEqual(seen, [42])
        self.assertEqual(dialogs.errors, [])


if __name__ == "__main__":
    unittest.main()
