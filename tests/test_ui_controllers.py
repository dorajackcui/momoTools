import unittest
from unittest.mock import patch

from controllers import ClearerController, ReverseUpdaterController, UpdaterController
from ui.validators import ValidationError
from ui.view_models import ClearerConfig, ReverseConfig, UpdaterConfig


class FakeDialogs:
    def __init__(self, confirm_result=True):
        self.errors = []
        self.infos = []
        self.warnings = []
        self.confirms = []
        self.confirm_result = confirm_result

    def info(self, title, message):
        self.infos.append((title, message))

    def error(self, title, message):
        self.errors.append((title, message))

    def warning(self, title, message):
        self.warnings.append((title, message))

    def confirm(self, title, message):
        self.confirms.append((title, message))
        return self.confirm_result


class FakeUpdaterFrame:
    def __init__(self, config):
        self._config = config
        self.selected_master = ""
        self.selected_folder = ""

    def set_master_file_label(self, path):
        self.selected_master = path

    def set_target_folder_label(self, path):
        self.selected_folder = path

    def get_config(self):
        if isinstance(self._config, Exception):
            raise self._config
        return self._config


class FakeSingleUpdaterProcessor:
    def __init__(self):
        self.master_file = None
        self.target_folder = None
        self.target_cols = None
        self.master_cols = None
        self.fill_blank_only = None
        self.post_process_enabled = None
        self.processed = False

    def set_master_file(self, path):
        self.master_file = path

    def set_target_folder(self, path):
        self.target_folder = path

    def set_target_column(self, a, b, c):
        self.target_cols = (a, b, c)

    def set_master_column(self, a, b, c):
        self.master_cols = (a, b, c)

    def set_fill_blank_only(self, enabled):
        self.fill_blank_only = enabled

    def set_post_process_enabled(self, enabled):
        self.post_process_enabled = enabled

    def process_files(self):
        self.processed = True
        return 11


class FakeMultiUpdaterProcessor:
    def __init__(self):
        self.master_file = None
        self.target_folder = None
        self.target_key = None
        self.target_match = None
        self.target_update_start = None
        self.master_key = None
        self.master_match = None
        self.master_start = None
        self.column_count = None
        self.fill_blank_only = None
        self.post_process_enabled = None
        self.processed = False

    def set_master_file(self, path):
        self.master_file = path

    def set_target_folder(self, path):
        self.target_folder = path

    def set_target_key_column(self, value):
        self.target_key = value

    def set_match_column(self, value):
        self.target_match = value

    def set_update_start_column(self, value):
        self.target_update_start = value

    def set_master_key_column(self, value):
        self.master_key = value

    def set_master_match_column(self, value):
        self.master_match = value

    def set_start_column(self, value):
        self.master_start = value

    def set_column_count(self, value):
        self.column_count = value

    def set_fill_blank_only(self, enabled):
        self.fill_blank_only = enabled

    def set_post_process_enabled(self, enabled):
        self.post_process_enabled = enabled

    def process_files(self):
        self.processed = True
        return 27


class FakeReverseProcessor:
    def __init__(self):
        self.target_cols = None
        self.master_cols = None
        self.fill_blank_only = None

    def set_master_file(self, _path):
        pass

    def set_target_folder(self, _path):
        pass

    def set_target_columns(self, a, b, c):
        self.target_cols = (a, b, c)

    def set_master_columns(self, a, b, c):
        self.master_cols = (a, b, c)

    def set_fill_blank_only(self, enabled):
        self.fill_blank_only = enabled

    def process_files(self):
        return 3


class FakeClearerFrame:
    def __init__(self, config):
        self._config = config
        self.selected_folder = ""

    def set_target_folder_label(self, path):
        self.selected_folder = path

    def get_config(self):
        return self._config


class FakeClearerProcessor:
    def __init__(self):
        self.folder_path = None
        self.column_number = None
        self.deleted_called = False

    def set_folder_path(self, path):
        self.folder_path = path

    def set_column_number(self, number):
        self.column_number = number

    def clear_column_in_files(self):
        return 1

    def insert_column_in_files(self):
        return 1

    def delete_column_in_files(self):
        self.deleted_called = True
        return 1


class ControllersTestCase(unittest.TestCase):
    def test_updater_controller_single_path_success(self):
        config = UpdaterConfig(0, 1, 2, 1, 2, 3, 1, True, False)
        frame = FakeUpdaterFrame(config)
        single = FakeSingleUpdaterProcessor()
        multi = FakeMultiUpdaterProcessor()
        dialogs = FakeDialogs()
        controller = UpdaterController(frame, single, multi, dialog_service=dialogs)
        controller.master_file_path = "master.xlsx"
        controller.target_folder = "targets"

        controller.process_files()

        self.assertTrue(single.processed)
        self.assertFalse(multi.processed)
        self.assertEqual(single.target_cols, (0, 1, 2))
        self.assertEqual(single.master_cols, (1, 2, 3))
        self.assertTrue(single.fill_blank_only)
        self.assertFalse(single.post_process_enabled)
        self.assertIn("共更新 11 处数据。", dialogs.infos[0][1])

    def test_updater_controller_multi_path_success(self):
        config = UpdaterConfig(0, 1, 2, 1, 2, 3, 3, False, True)
        frame = FakeUpdaterFrame(config)
        single = FakeSingleUpdaterProcessor()
        multi = FakeMultiUpdaterProcessor()
        dialogs = FakeDialogs()
        controller = UpdaterController(frame, single, multi, dialog_service=dialogs)
        controller.master_file_path = "master.xlsx"
        controller.target_folder = "targets"

        controller.process_files()

        self.assertFalse(single.processed)
        self.assertTrue(multi.processed)
        self.assertEqual(multi.target_key, 0)
        self.assertEqual(multi.target_match, 1)
        self.assertEqual(multi.target_update_start, 2)
        self.assertEqual(multi.master_key, 1)
        self.assertEqual(multi.master_match, 2)
        self.assertEqual(multi.master_start, 3)
        self.assertEqual(multi.column_count, 3)
        self.assertFalse(multi.fill_blank_only)
        self.assertTrue(multi.post_process_enabled)
        self.assertIn("共更新 27 处数据。", dialogs.infos[0][1])

    def test_updater_controller_validation_error(self):
        frame = FakeUpdaterFrame(ValidationError("更新列数必须大于0"))
        single = FakeSingleUpdaterProcessor()
        multi = FakeMultiUpdaterProcessor()
        dialogs = FakeDialogs()
        controller = UpdaterController(frame, single, multi, dialog_service=dialogs)
        controller.master_file_path = "master.xlsx"
        controller.target_folder = "targets"

        controller.process_files()

        self.assertFalse(single.processed)
        self.assertFalse(multi.processed)
        self.assertTrue(dialogs.errors)
        self.assertIn("列配置错误", dialogs.errors[0][1])

    def test_reverse_controller_success(self):
        config = ReverseConfig(0, 1, 2, 1, 2, 3, False)
        frame = FakeUpdaterFrame(config)
        processor = FakeReverseProcessor()
        dialogs = FakeDialogs()
        controller = ReverseUpdaterController(frame, processor, dialog_service=dialogs)
        controller.master_file_path = "master.xlsx"
        controller.target_folder = "targets"

        controller.process_files()

        self.assertEqual(processor.target_cols, (0, 1, 2))
        self.assertEqual(processor.master_cols, (1, 2, 3))
        self.assertFalse(processor.fill_blank_only)
        self.assertIn("共更新 3 行。", dialogs.infos[0][1])

    def test_clearer_delete_requires_confirm(self):
        frame = FakeClearerFrame(ClearerConfig(column_number=5))
        processor = FakeClearerProcessor()
        dialogs = FakeDialogs(confirm_result=False)
        controller = ClearerController(frame, processor, dialog_service=dialogs)
        controller.target_folder = "targets"

        controller.delete_column()

        self.assertEqual(processor.column_number, 5)
        self.assertFalse(processor.deleted_called)
        self.assertTrue(dialogs.confirms)

    @patch("controllers.filedialog.askopenfilename", return_value="C:/tmp/master.xlsx")
    def test_updater_select_master_file(self, _mock_dialog):
        frame = FakeUpdaterFrame(
            UpdaterConfig(0, 1, 2, 1, 2, 3, 1, False, True),
        )
        single = FakeSingleUpdaterProcessor()
        multi = FakeMultiUpdaterProcessor()
        controller = UpdaterController(frame, single, multi, dialog_service=FakeDialogs())

        controller.select_master_file()

        self.assertEqual(controller.master_file_path, "C:/tmp/master.xlsx")
        self.assertEqual(frame.selected_master, "C:/tmp/master.xlsx")
        self.assertEqual(single.master_file, "C:/tmp/master.xlsx")
        self.assertEqual(multi.master_file, "C:/tmp/master.xlsx")


if __name__ == "__main__":
    unittest.main()

