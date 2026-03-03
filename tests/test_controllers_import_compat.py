import unittest

import controllers
import controller_modules


class ControllersImportCompatTestCase(unittest.TestCase):
    def test_reexported_controller_symbols_are_identical(self):
        self.assertIs(controllers.BaseController, controller_modules.BaseController)
        self.assertIs(
            controllers.TerminologyPathStateStore,
            controller_modules.TerminologyPathStateStore,
        )
        self.assertIs(controllers.UpdaterController, controller_modules.UpdaterController)
        self.assertIs(controllers.ClearerController, controller_modules.ClearerController)
        self.assertIs(
            controllers.CompatibilityController,
            controller_modules.CompatibilityController,
        )
        self.assertIs(
            controllers.DeepReplaceController,
            controller_modules.DeepReplaceController,
        )
        self.assertIs(
            controllers.BaseMasterUpdateController,
            controller_modules.BaseMasterUpdateController,
        )
        self.assertIs(
            controllers.MasterMergeController,
            controller_modules.MasterMergeController,
        )
        self.assertIs(
            controllers.UpdateMasterController,
            controller_modules.UpdateMasterController,
        )
        self.assertIs(
            controllers.UpdateContentController,
            controller_modules.UpdateContentController,
        )
        self.assertIs(
            controllers.MultiColumnController,
            controller_modules.MultiColumnController,
        )
        self.assertIs(
            controllers.ReverseUpdaterController,
            controller_modules.ReverseUpdaterController,
        )
        self.assertIs(
            controllers.UntranslatedStatsController,
            controller_modules.UntranslatedStatsController,
        )
        self.assertIs(
            controllers.TerminologyExtractorController,
            controller_modules.TerminologyExtractorController,
        )

    def test_controllers_module_exposes_filedialog_symbol(self):
        self.assertTrue(hasattr(controllers, "filedialog"))
        self.assertTrue(hasattr(controllers.filedialog, "askopenfilename"))


if __name__ == "__main__":
    unittest.main()
