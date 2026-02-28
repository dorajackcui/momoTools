import unittest
from unittest.mock import patch

from scripts import run_regression_suite


class RegressionSuitePerfOptionTestCase(unittest.TestCase):
    def test_without_with_perf_does_not_run_perf_step(self):
        with patch("scripts.run_regression_suite.run_step") as mock_run_step, patch(
            "sys.argv",
            ["run_regression_suite.py"],
        ):
            run_regression_suite.main()

        labels = [call.args[0] for call in mock_run_step.call_args_list]
        self.assertIn("syntax", labels)
        self.assertIn("unittest", labels)
        self.assertNotIn("perf", labels)

    def test_with_perf_runs_perf_step_and_forwards_baseline(self):
        with patch("scripts.run_regression_suite.run_step") as mock_run_step, patch(
            "sys.argv",
            [
                "run_regression_suite.py",
                "--with-perf",
                "--perf-baseline-json",
                "tests/perf/reports/old.json",
            ],
        ):
            run_regression_suite.main()

        perf_calls = [call for call in mock_run_step.call_args_list if call.args[0] == "perf"]
        self.assertEqual(len(perf_calls), 1)
        perf_command = perf_calls[0].args[1]
        self.assertIn("scripts/run_perf_baseline.py", perf_command)
        self.assertIn("--baseline-json", perf_command)
        self.assertIn("tests/perf/reports/old.json", perf_command)


if __name__ == "__main__":
    unittest.main()
