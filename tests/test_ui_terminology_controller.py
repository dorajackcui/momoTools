import tempfile
import unittest
from unittest.mock import patch

from controllers import TerminologyExtractorController
from ui import strings


class FakeDialogs:
    def __init__(self):
        self.errors = []
        self.infos = []

    def error(self, title, message):
        self.errors.append((title, message))

    def info(self, title, message):
        self.infos.append((title, message))


class FakeFrame:
    def __init__(self):
        self.input_folder = ""
        self.rule_config_path = ""
        self.output_file = ""

    def set_input_folder_label(self, path):
        self.input_folder = path

    def set_rule_config_label(self, path):
        self.rule_config_path = path

    def set_output_file_label(self, path):
        self.output_file = path


class FakeProcessor:
    def __init__(self):
        self.input_folder = None
        self.rule_config = None
        self.output_file = None
        self.process_called = False

    def set_input_folder(self, path):
        self.input_folder = path

    def set_rule_config(self, path):
        self.rule_config = path

    def set_output_file(self, path):
        self.output_file = path

    def process_files(self):
        self.process_called = True
        return {
            "files_total": 3,
            "files_succeeded": 2,
            "files_failed": 1,
            "candidates_count": 10,
            "terms_count": 5,
            "relations_count": 4,
            "review_count": 2,
        }


class FakeStateStore:
    def __init__(self, initial_state=None):
        self.state = dict(initial_state or {})

    def load(self):
        return dict(self.state)

    def save(self, state):
        self.state = dict(state)


class TerminologyControllerTestCase(unittest.TestCase):
    def test_requires_all_inputs(self):
        frame = FakeFrame()
        dialogs = FakeDialogs()
        processor = FakeProcessor()
        controller = TerminologyExtractorController(
            frame,
            processor,
            dialog_service=dialogs,
            state_store=FakeStateStore(),
        )

        controller.process_files()

        self.assertFalse(processor.process_called)
        self.assertEqual(dialogs.errors[0][1], strings.REQUIRE_TERMINOLOGY_INPUT)

    def test_select_paths_and_process_success(self):
        frame = FakeFrame()
        dialogs = FakeDialogs()
        processor = FakeProcessor()
        state_store = FakeStateStore()
        controller = TerminologyExtractorController(
            frame,
            processor,
            dialog_service=dialogs,
            state_store=state_store,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_folder = temp_dir
            rule_config = f"{temp_dir}/rules.json"
            output_file = f"{temp_dir}/result.xlsx"

            with patch("controllers.filedialog.askdirectory", return_value=input_folder):
                controller.select_input_folder()
            with patch("controllers.filedialog.askopenfilename", return_value=rule_config):
                controller.select_rule_config()
            with patch("controllers.filedialog.asksaveasfilename", return_value=output_file):
                controller.select_output_file()

            controller.process_files()

        self.assertEqual(frame.input_folder, input_folder)
        self.assertEqual(frame.rule_config_path, rule_config)
        self.assertEqual(frame.output_file, output_file)
        self.assertTrue(processor.process_called)
        self.assertTrue(dialogs.infos)
        self.assertEqual(state_store.state.get("terminology_rule_config_path"), rule_config)

    def test_restores_persisted_rule_config_path(self):
        frame = FakeFrame()
        dialogs = FakeDialogs()
        processor = FakeProcessor()
        persisted = {"terminology_rule_config_path": __file__}
        controller = TerminologyExtractorController(
            frame,
            processor,
            dialog_service=dialogs,
            state_store=FakeStateStore(persisted),
        )

        self.assertEqual(controller.rule_config_path, __file__)
        self.assertEqual(frame.rule_config_path, __file__)
        self.assertEqual(processor.rule_config, __file__)


if __name__ == "__main__":
    unittest.main()
