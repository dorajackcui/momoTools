import json
import os
import tempfile
import unittest
from unittest.mock import patch

from controllers import BatchController, ClearerController, ReverseUpdaterController, UntranslatedStatsController, UpdaterController
from core.batch_config import (
    BatchConfigV1,
    BatchDefaultsSingle,
    BatchJobConfig,
    BatchRuntimeOptions,
    MODE_MASTER_TO_TARGET_SINGLE,
    dump_config,
    load_config,
    template_config,
)
from core.auto_fill_config import AutoFillConfig, AutoFillRule, load_auto_fill_config, save_auto_fill_config
from core.batch_runner import BatchJobResult, BatchRunSummary
from ui import strings
from ui.validators import ValidationError
from ui.view_models import (
    BatchDefaultsReverse,
    BatchDefaultsSingle as BatchDefaultsSingleView,
    BatchJobRow,
    BatchRuntimeOptions as BatchRuntimeOptionsView,
    BatchViewConfig,
    ClearerConfig,
    ReverseConfig,
    StatsConfig,
    UpdaterConfig,
)


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


class FakeStatsFrame:
    def __init__(self, config):
        self._config = config
        self.selected_folder = ""
        self.selected_output = ""

    def set_target_folder_label(self, path):
        self.selected_folder = path

    def set_output_file_label(self, path):
        self.selected_output = path

    def get_config(self):
        if isinstance(self._config, Exception):
            raise self._config
        return self._config


class FakeStatsProcessor:
    def __init__(self, process_results=None):
        self.target_folder = None
        self.columns = None
        self.stats_mode = None
        self.exported_path = None
        self.process_results = process_results if process_results is not None else [{"file_name": "a.xlsx"}]

    def set_target_folder(self, path):
        self.target_folder = path

    def set_columns(self, source_col, translation_col):
        self.columns = (source_col, translation_col)

    def set_stats_mode(self, mode):
        self.stats_mode = mode

    def process_files(self):
        return self.process_results

    def export_to_excel(self, output_path):
        self.exported_path = output_path
        return True


class FakeBatchFrame:
    def __init__(self, config, mode=MODE_MASTER_TO_TARGET_SINGLE):
        self._config = config
        self._mode = mode
        self.master_file = ""
        self.config_file = ""
        self.config_loaded = None
        self.job_folder_updates = []
        self.auto_folder_updates = []
        self.auto_fill_config_path = ""

    def set_master_file_label(self, path):
        self.master_file = path

    def set_config_file_label(self, path):
        self.config_file = path

    def get_config(self):
        if isinstance(self._config, Exception):
            raise self._config
        return self._config

    def get_config_path(self):
        return self.config_file

    def load_config(self, config):
        self.config_loaded = config
        self.master_file = config.master_file

    def get_mode(self):
        return self._mode

    def set_job_target_folder(self, index, folder):
        self.job_folder_updates.append((index, folder))

    def replace_jobs_from_auto_fill(self, folders):
        self.auto_folder_updates = list(folders)

    def set_auto_fill_config_path(self, path):
        self.auto_fill_config_path = path


class FakeBatchRunner:
    def __init__(self, precheck_errors=None, summary=None):
        self.precheck_errors = list(precheck_errors or [])
        self.summary = summary or BatchRunSummary(
            mode=MODE_MASTER_TO_TARGET_SINGLE,
            jobs_total=1,
            jobs_succeeded=1,
            jobs_failed=0,
            updated_total=3,
            results=(
                BatchJobResult(
                    job_index=1,
                    job_name="job-1",
                    status="success",
                    updated_count=3,
                    error="",
                    elapsed_ms=5,
                ),
            ),
            stopped_early=False,
            backup_path="",
        )
        self.precheck_calls = []
        self.run_calls = []

    def precheck(self, config):
        self.precheck_calls.append(config)
        return list(self.precheck_errors)

    def run(self, config):
        self.run_calls.append(config)
        return self.summary


class FakeStateStore:
    def __init__(self, initial_state=None):
        self.state = dict(initial_state or {})

    def load(self):
        return dict(self.state)

    def save(self, state):
        self.state = dict(state)


class FakeNoopProcessor:
    def __init__(self):
        self.log_callback = None


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

    def test_stats_select_target_folder_auto_output_parent_level(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        frame = FakeStatsFrame(config)
        processor = FakeStatsProcessor()
        controller = UntranslatedStatsController(frame, processor, dialog_service=FakeDialogs())

        with tempfile.TemporaryDirectory() as temp_dir:
            target_folder = os.path.join(temp_dir, "small_tables")
            os.makedirs(target_folder)
            expected_output = os.path.join(temp_dir, "未翻译统计.xlsx")

            with patch("controllers.filedialog.askdirectory", return_value=target_folder):
                controller.select_target_folder()

        self.assertEqual(controller.target_folder, target_folder)
        self.assertEqual(processor.target_folder, target_folder)
        self.assertEqual(controller.output_file, expected_output)
        self.assertEqual(frame.selected_output, expected_output)

    def test_stats_select_target_folder_auto_output_conflict_increment(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        frame = FakeStatsFrame(config)
        processor = FakeStatsProcessor()
        controller = UntranslatedStatsController(frame, processor, dialog_service=FakeDialogs())

        with tempfile.TemporaryDirectory() as temp_dir:
            target_folder = os.path.join(temp_dir, "small_tables")
            os.makedirs(target_folder)

            open(os.path.join(temp_dir, "未翻译统计.xlsx"), "a", encoding="utf-8").close()
            open(os.path.join(temp_dir, "未翻译统计 (1).xlsx"), "a", encoding="utf-8").close()
            expected_output = os.path.join(temp_dir, "未翻译统计 (2).xlsx")

            with patch("controllers.filedialog.askdirectory", return_value=target_folder):
                controller.select_target_folder()

        self.assertEqual(controller.output_file, expected_output)
        self.assertEqual(frame.selected_output, expected_output)

    def test_stats_manual_output_then_change_folder_resets_to_auto_output(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        frame = FakeStatsFrame(config)
        processor = FakeStatsProcessor()
        controller = UntranslatedStatsController(frame, processor, dialog_service=FakeDialogs())

        with tempfile.TemporaryDirectory() as temp_dir:
            parent_a = os.path.join(temp_dir, "A")
            parent_b = os.path.join(temp_dir, "B")
            folder_a = os.path.join(parent_a, "small_tables")
            folder_b = os.path.join(parent_b, "small_tables")
            os.makedirs(folder_a)
            os.makedirs(folder_b)

            with patch("controllers.filedialog.askdirectory", return_value=folder_a):
                controller.select_target_folder()

            manual_output = os.path.join(temp_dir, "custom_output.xlsx")
            with patch("controllers.filedialog.asksaveasfilename", return_value=manual_output):
                controller.select_output_file()

            self.assertEqual(controller.output_file, manual_output)

            with patch("controllers.filedialog.askdirectory", return_value=folder_b):
                controller.select_target_folder()

            expected_output = os.path.join(parent_b, "未翻译统计.xlsx")

        self.assertEqual(controller.output_file, expected_output)
        self.assertEqual(frame.selected_output, expected_output)

    def test_stats_process_without_manual_output_uses_auto_output(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        frame = FakeStatsFrame(config)
        dialogs = FakeDialogs()
        processor = FakeStatsProcessor(process_results=[{"file_name": "file.xlsx"}])
        controller = UntranslatedStatsController(frame, processor, dialog_service=dialogs)

        with tempfile.TemporaryDirectory() as temp_dir:
            target_folder = os.path.join(temp_dir, "small_tables")
            os.makedirs(target_folder)
            expected_output = os.path.join(temp_dir, "未翻译统计.xlsx")

            with patch("controllers.filedialog.askdirectory", return_value=target_folder):
                controller.select_target_folder()

            controller.output_file = ""
            frame.selected_output = ""
            controller.process_stats()

        self.assertEqual(processor.columns, (1, 2))
        self.assertEqual(processor.stats_mode, "chinese_chars")
        self.assertEqual(processor.exported_path, expected_output)
        self.assertEqual(controller.output_file, expected_output)
        self.assertEqual(frame.selected_output, expected_output)
        self.assertTrue(dialogs.infos)

    def test_stats_process_requires_target_folder(self):
        config = StatsConfig(source_col=1, translation_col=2, stats_mode="chinese_chars")
        frame = FakeStatsFrame(config)
        dialogs = FakeDialogs()
        processor = FakeStatsProcessor()
        controller = UntranslatedStatsController(frame, processor, dialog_service=dialogs)

        controller.process_stats()

        self.assertTrue(dialogs.errors)
        self.assertEqual(dialogs.errors[0][1], strings.REQUIRE_STATS_FOLDER)
        self.assertIsNone(processor.exported_path)

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

    def _build_batch_view_config(self):
        return BatchViewConfig(
            mode=MODE_MASTER_TO_TARGET_SINGLE,
            master_file="C:/tmp/master.xlsx",
            config_path="",
            defaults_single=BatchDefaultsSingleView(
                target_key_col=1,
                target_match_col=2,
                target_update_start_col=3,
                master_key_col=2,
                master_match_col=3,
                fill_blank_only=False,
                post_process_enabled=True,
            ),
            defaults_reverse=BatchDefaultsReverse(
                target_key_col=1,
                target_match_col=2,
                target_content_col=3,
                master_key_col=2,
                master_match_col=3,
                fill_blank_only=False,
            ),
            jobs=(
                BatchJobRow(name="job-1", target_folder="C:/tmp/p1", variable_column=4),
                BatchJobRow(name="job-2", target_folder="C:/tmp/p2", variable_column=5),
            ),
            runtime=BatchRuntimeOptionsView(continue_on_error=True),
        )

    def test_batch_controller_precheck_and_run_summary(self):
        config = self._build_batch_view_config()
        frame = FakeBatchFrame(config)
        dialogs = FakeDialogs()
        runner = FakeBatchRunner()
        controller = BatchController(
            frame,
            FakeNoopProcessor(),
            FakeNoopProcessor(),
            dialog_service=dialogs,
            state_store=FakeStateStore(),
            runner=runner,
        )

        controller.precheck_batch()
        controller.process_files()

        self.assertEqual(len(runner.precheck_calls), 2)
        self.assertEqual(len(runner.run_calls), 1)
        self.assertTrue(dialogs.infos)
        self.assertIn("Batch finished", dialogs.infos[-1][1])

    def test_batch_controller_precheck_fail_blocks_run(self):
        config = self._build_batch_view_config()
        frame = FakeBatchFrame(config)
        dialogs = FakeDialogs()
        runner = FakeBatchRunner(precheck_errors=["missing folder"])
        controller = BatchController(
            frame,
            FakeNoopProcessor(),
            FakeNoopProcessor(),
            dialog_service=dialogs,
            state_store=FakeStateStore(),
            runner=runner,
        )

        controller.process_files()

        self.assertEqual(len(runner.run_calls), 0)
        self.assertTrue(dialogs.errors)
        self.assertIn("Batch precheck failed", dialogs.errors[0][1])

    def test_batch_controller_load_and_export_json(self):
        frame = FakeBatchFrame(self._build_batch_view_config())
        dialogs = FakeDialogs()
        state_store = FakeStateStore()
        controller = BatchController(
            frame,
            FakeNoopProcessor(),
            FakeNoopProcessor(),
            dialog_service=dialogs,
            state_store=state_store,
            runner=FakeBatchRunner(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            loaded_path = os.path.join(temp_dir, "batch.json")
            loaded_config = BatchConfigV1(
                schema_version=1,
                mode=MODE_MASTER_TO_TARGET_SINGLE,
                master_file=master_path,
                defaults=BatchDefaultsSingle(
                    target_key_col=1,
                    target_match_col=2,
                    target_update_start_col=3,
                    master_key_col=2,
                    master_match_col=3,
                    fill_blank_only=False,
                    post_process_enabled=True,
                ),
                jobs=(BatchJobConfig(name="job-1", target_folder=temp_dir, variable_column=4),),
                runtime=BatchRuntimeOptions(continue_on_error=True),
            )
            dump_config(loaded_config, loaded_path)

            frame.set_config_file_label(loaded_path)
            controller.load_config_file()
            self.assertIsNotNone(frame.config_loaded)
            self.assertEqual(frame.master_file, master_path)

            template_path = os.path.join(temp_dir, "template.json")
            with patch("controller_modules.batch.filedialog.asksaveasfilename", return_value=template_path):
                controller.export_template_file()
            exported = load_config(template_path)
            self.assertEqual(exported.mode, MODE_MASTER_TO_TARGET_SINGLE)

    def test_batch_controller_restore_persisted_config_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "persisted.json")
            dump_config(template_config(MODE_MASTER_TO_TARGET_SINGLE), config_path)
            auto_fill_path = os.path.join(temp_dir, "rules.json")
            frame = FakeBatchFrame(self._build_batch_view_config())
            store = FakeStateStore(
                {
                    "batch_config_path": config_path,
                    "auto_fill_config_path": auto_fill_path,
                }
            )
            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=FakeDialogs(),
                state_store=store,
                runner=FakeBatchRunner(),
            )

            controller.restore_persisted_paths()

        self.assertEqual(frame.config_file, config_path)
        self.assertEqual(frame.auto_fill_config_path, auto_fill_path)

    def test_batch_controller_select_auto_fill_config_file_persists_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            selected = os.path.join(temp_dir, "my_rules.json")
            frame = FakeBatchFrame(self._build_batch_view_config())
            store = FakeStateStore()
            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=FakeDialogs(),
                state_store=store,
                runner=FakeBatchRunner(),
            )
            with patch("controller_modules.batch.filedialog.asksaveasfilename", return_value=selected):
                controller.select_auto_fill_config_file()

        self.assertEqual(controller.auto_fill_config_path, selected)
        self.assertEqual(frame.auto_fill_config_path, selected)
        self.assertEqual(store.state.get("auto_fill_config_path"), selected)

    def test_batch_controller_auto_fill_jobs_from_mapping_one_level(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_fill_path = os.path.join(temp_dir, "auto_fill_rules.json")
            frame = FakeBatchFrame(self._build_batch_view_config())
            dialogs = FakeDialogs()
            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=dialogs,
                state_store=FakeStateStore(),
                runner=FakeBatchRunner(),
                auto_fill_config_path=auto_fill_path,
            )
            fr_dir = os.path.join(temp_dir, "[fr]2.1.2")
            de_dir = os.path.join(temp_dir, "[de]2.1.2")
            nested_fr = os.path.join(fr_dir, "[fr]child")
            os.makedirs(fr_dir)
            os.makedirs(de_dir)
            os.makedirs(nested_fr)
            os.makedirs(os.path.join(temp_dir, "misc"))
            save_auto_fill_config(
                AutoFillConfig(
                    rules=(
                        AutoFillRule(keyword="[fr]", variable_column=6),
                        AutoFillRule(keyword="[de]", variable_column=7),
                    )
                ),
                auto_fill_path,
            )
            with patch("controllers.filedialog.askdirectory", return_value=temp_dir):
                controller.auto_fill_jobs_from_mapping()

        self.assertEqual(
            frame.auto_folder_updates,
            [
                {"target_folder": fr_dir, "variable_column": 6},
                {"target_folder": de_dir, "variable_column": 7},
            ],
        )
        self.assertTrue(dialogs.infos)
        self.assertFalse(dialogs.errors)

    def test_batch_controller_auto_fill_jobs_from_mapping_no_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_fill_path = os.path.join(temp_dir, "auto_fill_rules.json")
            frame = FakeBatchFrame(self._build_batch_view_config())
            dialogs = FakeDialogs()
            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=dialogs,
                state_store=FakeStateStore(),
                runner=FakeBatchRunner(),
                auto_fill_config_path=auto_fill_path,
            )
            os.makedirs(os.path.join(temp_dir, "[jp]2.1.2"))
            save_auto_fill_config(
                AutoFillConfig(
                    rules=(
                        AutoFillRule(keyword="[fr]", variable_column=6),
                        AutoFillRule(keyword="[de]", variable_column=7),
                    )
                ),
                auto_fill_path,
            )
            with patch("controllers.filedialog.askdirectory", return_value=temp_dir):
                controller.auto_fill_jobs_from_mapping()

        self.assertFalse(frame.auto_folder_updates)
        self.assertTrue(dialogs.warnings)

    def test_batch_controller_open_auto_fill_config_file_creates_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_fill_path = os.path.join(temp_dir, "auto_fill_rules.json")
            frame = FakeBatchFrame(self._build_batch_view_config())
            dialogs = FakeDialogs()
            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=dialogs,
                state_store=FakeStateStore(),
                runner=FakeBatchRunner(),
                auto_fill_config_path=auto_fill_path,
            )
            with patch("controller_modules.batch.os.startfile", create=True):
                controller.open_auto_fill_config_file()
            loaded = load_auto_fill_config(auto_fill_path)

        self.assertEqual(len(loaded.rules), 0)
        self.assertFalse(dialogs.errors)

    def test_batch_controller_load_old_json_migrates_legacy_auto_fill(self):
        frame = FakeBatchFrame(self._build_batch_view_config())
        dialogs = FakeDialogs()
        state_store = FakeStateStore()

        with tempfile.TemporaryDirectory() as temp_dir:
            auto_fill_path = os.path.join(temp_dir, "auto_fill_rules.json")
            master_path = os.path.join(temp_dir, "master.xlsx")
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            old_json_path = os.path.join(temp_dir, "legacy_batch.json")
            legacy_payload = {
                "schema_version": 1,
                "mode": MODE_MASTER_TO_TARGET_SINGLE,
                "master_file": master_path,
                "defaults": {
                    "target_key_col": 1,
                    "target_match_col": 2,
                    "target_update_start_col": 3,
                    "master_key_col": 2,
                    "master_match_col": 3,
                    "fill_blank_only": False,
                    "post_process_enabled": True,
                },
                "jobs": [
                    {
                        "name": "job-1",
                        "target_folder": temp_dir,
                        "master_content_start_col": 4,
                    }
                ],
                "runtime": {"continue_on_error": True},
                "auto_fill": {
                    "rules": [
                        {"keyword": "[fr]", "variable_column": 6},
                        {"keyword": "[de]", "variable_column": 7},
                    ]
                },
            }
            with open(old_json_path, "w", encoding="utf-8") as handle:
                json.dump(legacy_payload, handle, ensure_ascii=False, indent=2)

            controller = BatchController(
                frame,
                FakeNoopProcessor(),
                FakeNoopProcessor(),
                dialog_service=dialogs,
                state_store=state_store,
                runner=FakeBatchRunner(),
                auto_fill_config_path=auto_fill_path,
            )
            frame.set_config_file_label(old_json_path)
            controller.load_config_file()
            loaded = load_auto_fill_config(auto_fill_path)

        self.assertEqual(len(loaded.rules), 2)
        self.assertEqual(frame.master_file, master_path)


if __name__ == "__main__":
    unittest.main()
