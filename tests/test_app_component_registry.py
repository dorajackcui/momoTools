import unittest
from contextlib import ExitStack
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


class RecordingBatchController(RecordingController):
    instances = []

    def __init__(self, frame, *args, **kwargs):
        super().__init__(frame, *args, **kwargs)
        self.restore_calls = []

    def restore_persisted_paths(self):
        self.restore_calls.append(self.frame is not None)


class RecordingClearerController(RecordingController):
    instances = []


class RecordingCompatibilityController(RecordingController):
    instances = []


class RecordingDeepReplaceController(RecordingController):
    instances = []


class RecordingMasterMergeController(RecordingController):
    instances = []


class RecordingUpdateMasterController(RecordingController):
    instances = []


class RecordingUpdateContentController(RecordingController):
    instances = []


class RecordingSourceTranslationPipelineController(RecordingController):
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


class RecordingBatchFrame(RecordingFrame):
    instances = []


class RecordingClearerFrame(RecordingFrame):
    instances = []


class RecordingCompatibilityFrame(RecordingFrame):
    instances = []


class RecordingDeepReplaceFrame(RecordingFrame):
    instances = []


class RecordingMasterMergeFrame(RecordingFrame):
    instances = []


class RecordingUpdateMasterFrame(RecordingFrame):
    instances = []


class RecordingUpdateContentFrame(RecordingFrame):
    instances = []


class RecordingSourceTranslationPipelineFrame(RecordingFrame):
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
            RecordingBatchController,
            RecordingClearerController,
            RecordingCompatibilityController,
            RecordingDeepReplaceController,
            RecordingMasterMergeController,
            RecordingUpdateMasterController,
            RecordingUpdateContentController,
            RecordingSourceTranslationPipelineController,
            RecordingStatsController,
            RecordingTerminologyController,
            RecordingUpdaterFrame,
            RecordingReverseFrame,
            RecordingBatchFrame,
            RecordingClearerFrame,
            RecordingCompatibilityFrame,
            RecordingDeepReplaceFrame,
            RecordingMasterMergeFrame,
            RecordingUpdateMasterFrame,
            RecordingUpdateContentFrame,
            RecordingSourceTranslationPipelineFrame,
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
        instance.master_merge_processor = object()
        instance.untranslated_stats_processor = object()
        instance.terminology_processor = object()
        instance.task_runner = object()

        main_group_frame = MagicMock(name="main_group_frame")
        utilities_group_frame = MagicMock(name="utilities_group_frame")
        update_master_group_frame = MagicMock(name="update_master_group_frame")
        main_notebook = MagicMock(name="main_notebook")
        utilities_notebook = MagicMock(name="utilities_notebook")
        update_master_notebook = MagicMock(name="update_master_notebook")

        with ExitStack() as stack:
            stack.enter_context(
                patch(
                    "app.ttk.Frame",
                    side_effect=[main_group_frame, utilities_group_frame, update_master_group_frame],
                )
            )
            stack.enter_context(
                patch(
                    "app.ttk.Notebook",
                    side_effect=[main_notebook, utilities_notebook, update_master_notebook],
                )
            )
            stack.enter_context(patch("app.UpdaterController", RecordingUpdaterController))
            stack.enter_context(patch("app.ReverseUpdaterController", RecordingReverseController))
            stack.enter_context(patch("app.BatchController", RecordingBatchController))
            stack.enter_context(patch("app.BatchFrame", RecordingBatchFrame))
            stack.enter_context(patch("app.ClearerController", RecordingClearerController))
            stack.enter_context(patch("app.CompatibilityController", RecordingCompatibilityController))
            stack.enter_context(patch("app.DeepReplaceController", RecordingDeepReplaceController))
            stack.enter_context(patch("app.MasterMergeController", RecordingMasterMergeController))
            stack.enter_context(patch("app.UpdateMasterController", RecordingUpdateMasterController))
            stack.enter_context(patch("app.UpdateContentController", RecordingUpdateContentController))
            stack.enter_context(
                patch(
                    "app.SourceTranslationPipelineController",
                    RecordingSourceTranslationPipelineController,
                )
            )
            stack.enter_context(patch("app.UntranslatedStatsController", RecordingStatsController))
            stack.enter_context(patch("app.TerminologyExtractorController", RecordingTerminologyController))
            stack.enter_context(patch("app.UpdaterFrame", RecordingUpdaterFrame))
            stack.enter_context(patch("app.ReverseUpdaterFrame", RecordingReverseFrame))
            stack.enter_context(patch("app.ClearerFrame", RecordingClearerFrame))
            stack.enter_context(patch("app.CompatibilityFrame", RecordingCompatibilityFrame))
            stack.enter_context(patch("app.DeepReplaceFrame", RecordingDeepReplaceFrame))
            stack.enter_context(patch("app.MergeMastersFrame", RecordingMasterMergeFrame))
            stack.enter_context(patch("app.UpdateMasterFrame", RecordingUpdateMasterFrame))
            stack.enter_context(patch("app.UpdateContentFrame", RecordingUpdateContentFrame))
            stack.enter_context(
                patch(
                    "app.SourceTranslationPipelineFrame",
                    RecordingSourceTranslationPipelineFrame,
                )
            )
            stack.enter_context(patch("app.UntranslatedStatsFrame", RecordingStatsFrame))
            stack.enter_context(patch("app.TerminologyExtractorFrame", RecordingTerminologyFrame))
            instance.init_components()

        self.assertEqual(
            [call.kwargs["text"] for call in instance.notebook.add.call_args_list],
            ["Content Sync", "Utilities", "Master Update"],
        )
        self.assertEqual(
            [call.kwargs["text"] for call in main_notebook.add.call_args_list],
            ["Master->Target", "Target->Master", "Batch"],
        )
        self.assertEqual(
            [call.kwargs["text"] for call in utilities_notebook.add.call_args_list],
            ["Column Clear", "Compatibility", "Deep Replace", "Untranslated Stats", "Term Extractor"],
        )
        self.assertEqual(
            [call.kwargs["text"] for call in update_master_notebook.add.call_args_list],
            ["Merge Masters", "Source Text", "Translation", "Source+Translation"],
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
        self.assertEqual(len(RecordingBatchController.instances), 1)
        batch_controller = RecordingBatchController.instances[0]
        self.assertIs(batch_controller.kwargs["task_runner"], instance.task_runner)
        self.assertEqual(batch_controller.restore_calls, [True])
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
        self.assertEqual(len(RecordingMasterMergeController.instances), 1)
        self.assertIs(
            RecordingMasterMergeController.instances[0].args[0],
            instance.master_merge_processor,
        )
        self.assertIs(
            RecordingMasterMergeController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingUpdateMasterController.instances), 1)
        self.assertIs(
            RecordingUpdateMasterController.instances[0].args[0],
            instance.master_merge_processor,
        )
        self.assertIs(
            RecordingUpdateMasterController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingUpdateContentController.instances), 1)
        self.assertIs(
            RecordingUpdateContentController.instances[0].args[0],
            instance.master_merge_processor,
        )
        self.assertIs(
            RecordingUpdateContentController.instances[0].kwargs["task_runner"],
            instance.task_runner,
        )
        self.assertEqual(len(RecordingSourceTranslationPipelineController.instances), 1)
        self.assertIs(
            RecordingSourceTranslationPipelineController.instances[0].args[0],
            instance.master_merge_processor,
        )
        self.assertIs(
            RecordingSourceTranslationPipelineController.instances[0].kwargs["task_runner"],
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
