from ui import strings
from .base import BaseController


class ClearerController(BaseController):
    def __init__(self, frame, clearer, dialog_service=None, task_runner=None):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.clearer = clearer
        self.target_folder = ""

    def select_clearer_folder(self):
        folder_path = self._ask_folder("Select target folder")
        if not folder_path:
            return
        probe_result = self._confirm_excel_folder_selection(
            folder_path=folder_path,
            list_files=self.clearer.list_target_files,
            dialog_title="Confirm target files",
            require_writable_sample=True,
            sample_seed_key=f"clearer|{folder_path}",
        )
        if probe_result is None:
            return
        self.target_folder = folder_path
        self._require_frame().set_target_folder_label(folder_path)
        self.clearer.set_folder_path(folder_path)

    def _with_column_config(self, action, success_template, confirm_message=None):
        if not self._ensure_required_values([(self.target_folder, strings.REQUIRE_TARGET_FOLDER)]):
            return

        config = self._get_config_or_notify(validation_prefix=strings.VALIDATION_COLUMN_PREFIX)
        if config is None:
            return
        self.clearer.set_column_number(config.column_number)

        if confirm_message:
            if not self.dialogs.confirm(strings.CONFIRM_TITLE, confirm_message.format(column_number=config.column_number)):
                return

        self._run_action_or_notify(
            action,
            on_success=lambda processed_files: self.dialogs.info(
                strings.SUCCESS_TITLE,
                success_template.format(processed_files=processed_files),
            ),
            task_name="Column Clear",
        )

    def clear_column(self):
        self._with_column_config(
            action=self.clearer.clear_column_in_files,
            success_template="Processed {processed_files} file(s).",
        )

    def insert_column(self):
        self._with_column_config(
            action=self.clearer.insert_column_in_files,
            success_template="Processed {processed_files} file(s).",
        )

    def delete_column(self):
        self._with_column_config(
            action=self.clearer.delete_column_in_files,
            success_template="Processed {processed_files} file(s).",
            confirm_message=(
                "Delete column {column_number} in all Excel files?\n"
                "This action cannot be undone."
            ),
        )
