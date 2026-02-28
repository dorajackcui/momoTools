import os
from tkinter import filedialog

from ui import strings
from .base import BaseController
from .path_state import TerminologyPathStateStore


class TerminologyExtractorController(BaseController):
    def __init__(self, frame, processor, dialog_service=None, state_store=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.processor = processor
        self.state_store = state_store or TerminologyPathStateStore()
        self.input_folder = ""
        self.rule_config_path = ""
        self.output_file = ""
        self.restore_persisted_paths()

    def restore_persisted_paths(self):
        state = self.state_store.load()
        persisted_path = str(state.get(TerminologyPathStateStore.STATE_KEY_RULE_CONFIG_PATH, "")).strip()
        if not persisted_path or not os.path.isfile(persisted_path):
            return
        self.rule_config_path = persisted_path
        if self.frame is not None:
            self._require_frame().set_rule_config_label(persisted_path)
        self.processor.set_rule_config(persisted_path)

    def _persist_rule_config_path(self):
        state = self.state_store.load()
        state[TerminologyPathStateStore.STATE_KEY_RULE_CONFIG_PATH] = self.rule_config_path
        self.state_store.save(state)

    def select_input_folder(self):
        folder_path = self._ask_folder("Select input folder")
        if not folder_path:
            return
        self.input_folder = folder_path
        self._require_frame().set_input_folder_label(folder_path)
        self.processor.set_input_folder(folder_path)

    def select_rule_config(self):
        initial_dir = ""
        if self.rule_config_path:
            initial_dir = os.path.dirname(self.rule_config_path)
        file_path = filedialog.askopenfilename(
            title="Select rule config",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir or None,
        )
        if not file_path:
            return
        self.rule_config_path = file_path
        self._require_frame().set_rule_config_label(file_path)
        self.processor.set_rule_config(file_path)
        self._persist_rule_config_path()

    def select_output_file(self):
        file_path = self._ask_output_excel_file("Select output file")
        if not file_path:
            return
        self.output_file = file_path
        self._require_frame().set_output_file_label(file_path)
        self.processor.set_output_file(file_path)

    def process_files(self):
        if not self._ensure_required_values(
            [(self.input_folder and self.rule_config_path and self.output_file, strings.REQUIRE_TERMINOLOGY_INPUT)]
        ):
            return

        def run():
            return self.processor.process_files()

        def on_success(result):
            self.dialogs.info(
                strings.SUCCESS_TITLE,
                (
                    "Terminology extraction completed.\n"
                    f"Files: {result['files_succeeded']}/{result['files_total']}\n"
                    f"Candidates: {result['candidates_count']}\n"
                    f"Terms: {result['terms_count']}\n"
                    f"Relations: {result['relations_count']}\n"
                    f"Review: {result['review_count']}"
                ),
            )

        self._run_action_or_notify(run, on_success=on_success, task_name="Term Extractor")
