import os
import tempfile
import unittest
from unittest.mock import patch

from core.batch_config import (
    BatchConfigV1,
    BatchDefaultsReverse,
    BatchDefaultsSingle,
    BatchJobConfig,
    BatchRuntimeOptions,
    MODE_MASTER_TO_TARGET_SINGLE,
    MODE_TARGET_TO_MASTER_REVERSE,
)
from core.batch_runner import BatchRunner


class FakeSingleProcessor:
    def __init__(self, results=None):
        self.results = results or {}
        self.master_file = ""
        self.target_folder = ""
        self.target_cols = None
        self.master_cols = None
        self.fill_blank_only = None
        self.post_process_enabled = None
        self.calls = []
        self.cleanup_calls = 0

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
        value = self.results.get(self.target_folder, 0)
        if isinstance(value, Exception):
            raise value
        self.calls.append(
            {
                "master_file": self.master_file,
                "target_folder": self.target_folder,
                "target_cols": self.target_cols,
                "master_cols": self.master_cols,
                "fill_blank_only": self.fill_blank_only,
                "post_process_enabled": self.post_process_enabled,
            }
        )
        return value

    def cleanup_after_run(self):
        self.cleanup_calls += 1


class FakeReverseProcessor:
    def __init__(self, results=None):
        self.results = results or {}
        self.master_file = ""
        self.target_folder = ""
        self.target_cols = None
        self.master_cols = None
        self.fill_blank_only = None
        self.calls = []
        self.cleanup_calls = 0

    def set_master_file(self, path):
        self.master_file = path

    def set_target_folder(self, path):
        self.target_folder = path

    def set_target_columns(self, a, b, c):
        self.target_cols = (a, b, c)

    def set_master_columns(self, a, b, c):
        self.master_cols = (a, b, c)

    def set_fill_blank_only(self, enabled):
        self.fill_blank_only = enabled

    def process_files(self):
        value = self.results.get(self.target_folder, 0)
        if isinstance(value, Exception):
            raise value
        self.calls.append(
            {
                "master_file": self.master_file,
                "target_folder": self.target_folder,
                "target_cols": self.target_cols,
                "master_cols": self.master_cols,
                "fill_blank_only": self.fill_blank_only,
            }
        )
        return value

    def cleanup_after_run(self):
        self.cleanup_calls += 1


class BatchRunnerTestCase(unittest.TestCase):
    def test_single_mode_multi_jobs_parameter_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            folder1 = os.path.join(temp_dir, "pkg1")
            folder2 = os.path.join(temp_dir, "pkg2")
            os.makedirs(folder1)
            os.makedirs(folder2)
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            single = FakeSingleProcessor(results={folder1: 11, folder2: 22})
            reverse = FakeReverseProcessor()
            runner = BatchRunner(single, reverse)
            config = BatchConfigV1(
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
                jobs=(
                    BatchJobConfig(name="job-1", target_folder=folder1, variable_column=4),
                    BatchJobConfig(name="job-2", target_folder=folder2, variable_column=5),
                ),
                runtime=BatchRuntimeOptions(continue_on_error=True),
            )

            summary = runner.run(config)

        self.assertEqual(summary.updated_total, 33)
        self.assertEqual(summary.jobs_succeeded, 2)
        self.assertEqual(single.calls[0]["target_cols"], (0, 1, 2))
        self.assertEqual(single.calls[0]["master_cols"], (1, 2, 3))
        self.assertEqual(single.calls[1]["master_cols"], (1, 2, 4))

    def test_reverse_mode_order_and_cumulative_master(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            folder1 = os.path.join(temp_dir, "pkg1")
            folder2 = os.path.join(temp_dir, "pkg2")
            os.makedirs(folder1)
            os.makedirs(folder2)
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            single = FakeSingleProcessor()
            reverse = FakeReverseProcessor(results={folder1: 3, folder2: 5})
            runner = BatchRunner(single, reverse)
            config = BatchConfigV1(
                schema_version=1,
                mode=MODE_TARGET_TO_MASTER_REVERSE,
                master_file=master_path,
                defaults=BatchDefaultsReverse(
                    target_key_col=1,
                    target_match_col=2,
                    target_content_col=3,
                    master_key_col=2,
                    master_match_col=3,
                    fill_blank_only=False,
                ),
                jobs=(
                    BatchJobConfig(name="job-1", target_folder=folder1, variable_column=10),
                    BatchJobConfig(name="job-2", target_folder=folder2, variable_column=11),
                ),
                runtime=BatchRuntimeOptions(continue_on_error=True),
            )

            summary = runner.run(config)

        self.assertEqual(summary.updated_total, 8)
        self.assertEqual([item["target_folder"] for item in reverse.calls], [folder1, folder2])
        self.assertEqual(reverse.calls[0]["master_file"], master_path)
        self.assertEqual(reverse.calls[0]["master_cols"], (1, 2, 9))
        self.assertEqual(reverse.calls[1]["master_cols"], (1, 2, 10))
        self.assertTrue(summary.backup_path)
        self.assertTrue(os.path.basename(summary.backup_path).startswith("master.batch_backup."))

    def test_continue_on_error_true_keeps_running(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            folder1 = os.path.join(temp_dir, "pkg1")
            folder2 = os.path.join(temp_dir, "pkg2")
            folder3 = os.path.join(temp_dir, "pkg3")
            for path in (folder1, folder2, folder3):
                os.makedirs(path)
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            single = FakeSingleProcessor(
                results={folder1: 1, folder2: RuntimeError("boom"), folder3: 2}
            )
            runner = BatchRunner(single, FakeReverseProcessor())
            config = BatchConfigV1(
                schema_version=1,
                mode=MODE_MASTER_TO_TARGET_SINGLE,
                master_file=master_path,
                defaults=BatchDefaultsSingle(1, 2, 3, 2, 3, False, True),
                jobs=(
                    BatchJobConfig(name="job-1", target_folder=folder1, variable_column=4),
                    BatchJobConfig(name="job-2", target_folder=folder2, variable_column=5),
                    BatchJobConfig(name="job-3", target_folder=folder3, variable_column=6),
                ),
                runtime=BatchRuntimeOptions(continue_on_error=True),
            )

            summary = runner.run(config)

        self.assertEqual(summary.jobs_total, 3)
        self.assertEqual(summary.jobs_failed, 1)
        self.assertFalse(summary.stopped_early)
        self.assertEqual(len(summary.results), 3)
        self.assertEqual(summary.updated_total, 3)
        self.assertEqual(single.cleanup_calls, 3)

    def test_continue_on_error_false_stops_early(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            folder1 = os.path.join(temp_dir, "pkg1")
            folder2 = os.path.join(temp_dir, "pkg2")
            folder3 = os.path.join(temp_dir, "pkg3")
            for path in (folder1, folder2, folder3):
                os.makedirs(path)
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            single = FakeSingleProcessor(
                results={folder1: 1, folder2: RuntimeError("boom"), folder3: 2}
            )
            runner = BatchRunner(single, FakeReverseProcessor())
            config = BatchConfigV1(
                schema_version=1,
                mode=MODE_MASTER_TO_TARGET_SINGLE,
                master_file=master_path,
                defaults=BatchDefaultsSingle(1, 2, 3, 2, 3, False, True),
                jobs=(
                    BatchJobConfig(name="job-1", target_folder=folder1, variable_column=4),
                    BatchJobConfig(name="job-2", target_folder=folder2, variable_column=5),
                    BatchJobConfig(name="job-3", target_folder=folder3, variable_column=6),
                ),
                runtime=BatchRuntimeOptions(continue_on_error=False),
            )

            summary = runner.run(config)

        self.assertEqual(summary.jobs_failed, 1)
        self.assertTrue(summary.stopped_early)
        self.assertEqual(len(summary.results), 2)
        self.assertEqual(summary.updated_total, 1)
        self.assertEqual(single.cleanup_calls, 2)

    def test_reverse_backup_failure_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = os.path.join(temp_dir, "master.xlsx")
            folder1 = os.path.join(temp_dir, "pkg1")
            os.makedirs(folder1)
            with open(master_path, "w", encoding="utf-8") as handle:
                handle.write("placeholder")

            runner = BatchRunner(FakeSingleProcessor(), FakeReverseProcessor(results={folder1: 3}))
            config = BatchConfigV1(
                schema_version=1,
                mode=MODE_TARGET_TO_MASTER_REVERSE,
                master_file=master_path,
                defaults=BatchDefaultsReverse(1, 2, 3, 2, 3, False),
                jobs=(BatchJobConfig(name="job-1", target_folder=folder1, variable_column=9),),
                runtime=BatchRuntimeOptions(continue_on_error=True),
            )

            with patch("core.batch_runner.shutil.copy2", side_effect=OSError("copy failed")):
                with self.assertRaises(OSError):
                    runner.run(config)


if __name__ == "__main__":
    unittest.main()
