import json
import tempfile
import unittest
from pathlib import Path

from scripts import run_perf_baseline


class PerfBaselineScriptTestCase(unittest.TestCase):
    def test_build_report_and_write_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = run_perf_baseline.build_report(iterations=1, baseline_json=None)
            report_dir = Path(temp_dir) / "reports"
            md_path, json_path = run_perf_baseline.write_report_files(report, report_dir)

            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("timestamp", payload)
            self.assertIn("cases", payload)
            self.assertIn("summary", payload)
            self.assertEqual(len(payload["cases"]), 3)

    def test_apply_baseline_comparison_sets_delta_and_trend(self):
        cases = [
            {"name": "a", "mean_s": 1.20, "delta_percent": None, "trend": None},
            {"name": "b", "mean_s": 0.95, "delta_percent": None, "trend": None},
            {"name": "c", "mean_s": 1.00, "delta_percent": None, "trend": None},
        ]
        baseline = {
            "a": {"name": "a", "mean_s": 1.00},
            "b": {"name": "b", "mean_s": 1.00},
            "c": {"name": "c", "mean_s": 1.00},
        }

        run_perf_baseline.apply_baseline_comparison(cases, baseline)

        self.assertGreater(cases[0]["delta_percent"], 0)
        self.assertEqual(cases[0]["trend"], "regressed")
        self.assertLess(cases[1]["delta_percent"], 0)
        self.assertEqual(cases[1]["trend"], "improved")
        self.assertEqual(cases[2]["trend"], "flat")


if __name__ == "__main__":
    unittest.main()
