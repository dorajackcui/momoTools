from ui import strings, theme
from ui.views.base import BaseFrame


class TerminologyExtractorFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("Input Files")
        self.input_folder_label = self.create_picker_with_status(
            button_text="Select input folder",
            command=self.controller.select_input_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        rule_frame = self.create_section_card("Rule Config")
        self.rule_config_label = self.create_picker_with_status(
            button_text="Select rule JSON",
            command=self.controller.select_rule_config,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=rule_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        output_frame = self.create_section_card("Output")
        self.output_file_label = self.create_picker_with_status(
            button_text="Select output xlsx",
            command=self.controller.select_output_file,
            default_text=strings.DEFAULT_OUTPUT_TEXT,
            parent=output_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        self.create_primary_button(
            text="Run terminology extraction",
            command=self.controller.process_files,
            pady=theme.SPACING_LG,
        )

    def set_input_folder_label(self, folder_path):
        self.set_selected_path_label(self.input_folder_label, folder_path)

    def set_rule_config_label(self, file_path):
        self.set_selected_file_label(self.rule_config_label, file_path)

    def set_output_file_label(self, output_path):
        self.set_output_path_label(self.output_file_label, output_path)
