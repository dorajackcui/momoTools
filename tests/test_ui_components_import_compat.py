import unittest

import ui_components
from ui.views.source_translation_pipeline import SourceTranslationPipelineFrame


class UIComponentsImportCompatTestCase(unittest.TestCase):
    def test_source_translation_pipeline_frame_is_reexported(self):
        self.assertIs(
            ui_components.SourceTranslationPipelineFrame,
            SourceTranslationPipelineFrame,
        )


if __name__ == "__main__":
    unittest.main()
