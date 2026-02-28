import unittest
from unittest.mock import MagicMock, patch

import app


class RecordingController:
    instances = []

    def __init__(self, frame, *args, **kwargs):
        self.frame = frame
        self.args = args
        self.kwargs = kwargs
        type(self).instances.append(self)


class RecordingUpdaterController(RecordingController):
    instances = []


class RecordingReverseController(RecordingController):
    instances = []


class RecordingClearerController(RecordingController):
    instances = []


class RecordingCompatibilityController(RecordingController):
    instances = []


class RecordingDeepReplaceController(RecordingController):
    instances = []


class RecordingStatsController(RecordingController):
    instances = []


class RecordingTerminologyController(RecordingController):
    instances = []

    def __init__(self, frame, *args, **kwargs):
        super().__init__(frame, *args, **kwargs)
        self.restore_calls = []

    def restore_persisted_paths(self):
        self.restore_calls.append(self.frame is not None)


class RecordingFrame:
    instances = []

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        type(self).instances.append(self)


class RecordingUpdaterFrame(RecordingFrame):
    instances = []


class RecordingReverseFrame(RecordingFrame):
    instances = []


class RecordingClearerFrame(RecordingFrame):
    instances = []


class RecordingCompatibilityFrame(RecordingFrame):
    instances = []


class RecordingDeepReplaceFrame(RecordingFrame):
    instances = []


class RecordingStatsFrame(RecordingFrame):
    instances = []


class RecordingTerminologyFrame(RecordingFrame):
    instances = []


class AppComponentRegistryTestCase(unittest.TestCase):
    def setUp(self):
        for cls in [
            RecordingUpdaterController,
            RecordingReverseController,
            RecordingClearerController,
            RecordingCompatibilityController,
            RecordingDeepReplaceController,
            RecordingStatsController,
            RecordingTerminologyController,
            RecordingUpdaterFrame,
            RecordingReverseFrame,
            RecordingClearerFrame,
            RecordingCompatibilityFrame,
            RecordingDeepReplaceFrame,
            RecordingStatsFrame,
            RecordingTerminologyFrame,
        ]:
            cls.instances = []

    def test_init_components_mounts_registry_in_expected_order(self):
        instance = app.ExcelUpdaterApp.__new__(app.ExcelUpdaterApp)
        instance.notebook = MagicMock(name="outer_notebook")
        instance.excel_processor = object()
        instance.multi_processor = object()
        instance.reverse_excel_processor = object()
        instance.clearer = object()
        instance.compatibility_processor = object()
        instance.deep_replace_processor = object()
        instance.untranslated_stats_processor = object()
        instance.terminology_processor = object()
        instance.task_runner = object()

        main_group_frame = MagicMock(name="main_group_frame")
        utilities_group_frame = MagicMock(name="utilities_group_frame")
        main_notebook = MagicMock(name="main_notebook")
        utilities_notebook = MagicMock(name="utilities_notebook")

        with patch("app.ttk.Frame", side_effect=[main_group_frame, utilities_group_frame]), patch(
            "app.ttk.Notebook", side_effect=[main_notebook, utilities_notebook]
        ), patch("app.UpdaterController", RecordingUpdaterController), patch(
            "app.ReverseUpdaterController", RecordingReverseController
        ), patch("app.ClearerController", RecordingClearerController), patch(
            "app.CompatibilityController", RecordingCompatibilityController
        ), patch("app.DeepReplaceController", RecordingDeepReplaceController), patch(
            "app.UntranslatedStatsController", RecordingStatsController
        ), patch("app.TerminologyExtractorController", RecordingTerminologyController), patch(
            "app.UpdaterFrame", RecordingUpdaterFrame
        ), patch("app.ReverseUpdaterFrame", RecordingReverseFrame), patch(
            "app.ClearerFrame", RecordingClearerFrame
        ), patch("app.CompatibilityFrame", RecordingCompatibilityFrame), patch(
            "app.DeepReplaceFrame", RecordingDeepReplaceFrame
        ), patch("app.UntranslatedStatsFrame", RecordingStatsFrame), patch(
            "app.TerminologyExtractorFrame", RecordingTerminologyFrame
        ):
            instance.init_components()

        self.assertEqual(
            [call.kwargs["text"] for call in instance.notebook.add.call_args_list],
            ["Main Tools", "Utilities"],
        )
        self.assertEqual(
            [call.kwargs["text"] for call in main_notebook.add.call_args_list],
            ["Master->Target", "Target->Master"],
        )
        self.assertEqual(
            [call.kwargs["text"] for call in utilities_notebook.add.call_args_list],
            ["Column Clear", "Compatibility", "Deep Replace", "Untranslated Stats", "Term Extractor"],
        )

        self.assertEqual(len(RecordingUpdaterController.instances), 1)
        updater_controller = RecordingUpdaterController.instances[0]
        self.assertIs(updater_controller.args[0], instance.excel_processor)
        self.assertIs(updater_controller.args[1], instance.multi_processor)
        self.assertIs(updater_controller.kwargs["task_runner"], instance.task_runner)
        self.assertIsNotNone(updater_controller.frame)

        self.assertEqual(len(RecordingReverseController.instances), 1)
        self.assertIs(
            RecordingReverseController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingClearerController.instances), 1)
        self.assertIs(
            RecordingClearerController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingCompatibilityController.instances), 1)
        self.assertIs(
            RecordingCompatibilityController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingDeepReplaceController.instances), 1)
        self.assertIs(
            RecordingDeepReplaceController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingStatsController.instances), 1)
        self.assertIs(
            RecordingStatsController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingTerminologyController.instances), 1)
        terminology_controller = RecordingTerminologyController.instances[0]
        self.assertIs(terminology_controller.kwargs["task_runner"], instance.task_runner)
        self.assertEqual(terminology_controller.restore_calls, [True])


if __name__ == "__main__":
    unittest.main()
