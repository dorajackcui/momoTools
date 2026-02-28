import unittest
from pathlib import Path

from scripts.run_golden_regression import run_manifest


class GoldenRegressionSampleTestCase(unittest.TestCase):
    def test_sample_manifest_has_passing_case(self):
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "tests" / "golden" / "manifest.sample.json"

        results = run_manifest(manifest_path)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertEqual(results[0].diff_count, 0)


if __name__ == "__main__":
    unittest.main()
