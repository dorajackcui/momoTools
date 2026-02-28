import argparse
import subprocess
import sys
from pathlib import Path


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"[RUN] {label}: {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run project regression checks.")
    parser.add_argument(
        "--with-golden",
        action="store_true",
        help="Also run golden workbook regression.",
    )
    parser.add_argument(
        "--golden-manifest",
        default="tests/golden/manifest.sample.json",
        help="Manifest used by golden regression when --with-golden is enabled.",
    )
    parser.add_argument(
        "--with-perf",
        action="store_true",
        help="Also run lightweight performance baseline and emit report files.",
    )
    parser.add_argument(
        "--perf-baseline-json",
        default="",
        help="Optional previous perf JSON report path for delta comparison.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    py = sys.executable

    run_step(
        "syntax",
        [py, "-m", "py_compile", "app.py", "controllers.py", "ui_components.py"],
        cwd=root,
    )
    run_step(
        "unittest",
        [py, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=root,
    )

    if args.with_golden:
        run_step(
            "golden",
            [py, "scripts/run_golden_regression.py", "--manifest", args.golden_manifest],
            cwd=root,
        )

    if args.with_perf:
        perf_command = [py, "scripts/run_perf_baseline.py"]
        if args.perf_baseline_json:
            perf_command.extend(["--baseline-json", args.perf_baseline_json])
        run_step("perf", perf_command, cwd=root)

    print("[OK] Regression suite finished.")


if __name__ == "__main__":
    main()
