import argparse
import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Callable, Optional

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.excel_processor import ExcelProcessor
from core.multi_column_processor import MultiColumnExcelProcessor
from core.reverse_excel_processor import ReverseExcelProcessor

FLAT_THRESHOLD_PERCENT = 1.0


def write_workbook(path: Path, rows: list[list[object]]) -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def run_master_to_target_single(work_dir: Path) -> int:
    master_path = work_dir / "master.xlsx"
    target_folder = work_dir / "targets_single"
    target_folder.mkdir()
    target_path = target_folder / "target.xlsx"

    write_workbook(
        master_path,
        [
            ["id", "key", "match", "value"],
            ["", "K1", "M1", "V1"],
        ],
    )
    write_workbook(
        target_path,
        [
            ["key", "match", "translation"],
            ["K1", "M1", ""],
            ["K1", "M1", "keep-me"],
        ],
    )

    processor = ExcelProcessor(log_callback=lambda _msg: None)
    processor.set_master_file(str(master_path))
    processor.set_target_folder(str(target_folder))
    processor.set_post_process_enabled(False)
    processor.set_fill_blank_only(True)
    return int(processor.process_files())


def run_master_to_target_multi(work_dir: Path) -> int:
    master_path = work_dir / "master_multi.xlsx"
    target_folder = work_dir / "targets_multi"
    target_folder.mkdir()
    target_path = target_folder / "target.xlsx"

    write_workbook(
        master_path,
        [
            ["id", "key", "match", "meta", "v1", "v2"],
            ["", "K1", "M1", "", "A1", "A2"],
        ],
    )
    write_workbook(
        target_path,
        [
            ["id", "key", "match", "meta", "out1", "out2"],
            ["", "K1", "M1", "", "", "old"],
        ],
    )

    processor = MultiColumnExcelProcessor(log_callback=lambda _msg: None)
    processor.set_master_file(str(master_path))
    processor.set_target_folder(str(target_folder))
    processor.set_column_count(2)
    processor.set_post_process_enabled(False)
    processor.set_fill_blank_only(False)
    return int(processor.process_files())


def run_target_to_master_reverse(work_dir: Path) -> int:
    master_path = work_dir / "master_reverse.xlsx"
    target_folder = work_dir / "targets_reverse"
    target_folder.mkdir()

    write_workbook(
        master_path,
        [
            ["id", "key", "match", "translation"],
            ["", "K1", "M1", ""],
        ],
    )
    write_workbook(
        target_folder / "a.xlsx",
        [
            ["key", "match", "translation"],
            ["K1", "M1", "from_a"],
        ],
    )
    write_workbook(
        target_folder / "b.xlsx",
        [
            ["key", "match", "translation"],
            ["K1", "M1", "from_b"],
        ],
    )

    processor = ReverseExcelProcessor(log_callback=lambda _msg: None)
    processor.set_master_file(str(master_path))
    processor.set_target_folder(str(target_folder))
    return int(processor.process_files())


def run_case(name: str, runner: Callable[[Path], int], iterations: int) -> dict:
    durations_s: list[float] = []
    last_updated_count = None
    error = ""
    for _ in range(iterations):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                started = time.perf_counter()
                last_updated_count = runner(root)
                elapsed = time.perf_counter() - started
                durations_s.append(elapsed)
        except Exception as exc:
            error = str(exc)
            break

    result = {
        "name": name,
        "iterations": iterations,
        "durations_s": durations_s,
        "mean_s": mean(durations_s) if durations_s else None,
        "min_s": min(durations_s) if durations_s else None,
        "max_s": max(durations_s) if durations_s else None,
        "last_updated_count": last_updated_count,
        "delta_percent": None,
        "trend": None,
        "error": error,
    }
    return result


def load_baseline_cases(path: Optional[Path]) -> dict[str, dict]:
    if path is None:
        return {}
    content = json.loads(path.read_text(encoding="utf-8"))
    cases = content.get("cases", [])
    return {case["name"]: case for case in cases}


def classify_trend(delta_percent: float) -> str:
    if delta_percent <= -FLAT_THRESHOLD_PERCENT:
        return "improved"
    if delta_percent >= FLAT_THRESHOLD_PERCENT:
        return "regressed"
    return "flat"


def apply_baseline_comparison(cases: list[dict], baseline_cases: dict[str, dict]) -> None:
    for case in cases:
        baseline = baseline_cases.get(case["name"])
        current_mean = case.get("mean_s")
        if baseline is None or current_mean is None:
            continue
        baseline_mean = baseline.get("mean_s")
        if baseline_mean is None or baseline_mean <= 0:
            continue

        delta_percent = ((current_mean - baseline_mean) / baseline_mean) * 100.0
        case["delta_percent"] = delta_percent
        case["trend"] = classify_trend(delta_percent)


def build_summary(cases: list[dict]) -> dict:
    regressed = [case["name"] for case in cases if case.get("trend") == "regressed"]
    improved = [case["name"] for case in cases if case.get("trend") == "improved"]
    failed = [case["name"] for case in cases if case.get("error")]
    return {
        "case_count": len(cases),
        "improved_cases": improved,
        "regressed_cases": regressed,
        "failed_cases": failed,
    }


def generate_markdown_report(report: dict) -> str:
    lines = [
        "# Performance Baseline Report",
        "",
        f"- Time: {report['timestamp']}",
        f"- Iterations: {report['iterations']}",
    ]
    baseline_json = report.get("baseline_json")
    if baseline_json:
        lines.append(f"- Baseline JSON: `{baseline_json}`")
    lines.extend(
        [
            "",
            "| Case | mean_s | min_s | max_s | last_updated_count | delta_percent | trend | error |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for case in report["cases"]:
        delta = case["delta_percent"]
        delta_text = f"{delta:.2f}%" if isinstance(delta, float) else "-"
        mean_text = f"{case['mean_s']:.6f}" if isinstance(case["mean_s"], float) else "-"
        min_text = f"{case['min_s']:.6f}" if isinstance(case["min_s"], float) else "-"
        max_text = f"{case['max_s']:.6f}" if isinstance(case["max_s"], float) else "-"
        count_text = str(case["last_updated_count"]) if case["last_updated_count"] is not None else "-"
        trend_text = case["trend"] or "-"
        error_text = case["error"] or "-"
        lines.append(
            f"| {case['name']} | {mean_text} | {min_text} | {max_text} | "
            f"{count_text} | {delta_text} | {trend_text} | {error_text} |"
        )

    lines.append("")
    lines.append("## Summary")
    summary = report["summary"]
    lines.append(f"- Case count: {summary['case_count']}")
    lines.append(f"- Improved: {', '.join(summary['improved_cases']) or 'None'}")
    lines.append(f"- Regressed: {', '.join(summary['regressed_cases']) or 'None'}")
    lines.append(f"- Failed: {', '.join(summary['failed_cases']) or 'None'}")
    return "\n".join(lines)


def build_report(iterations: int, baseline_json: Optional[Path]) -> dict:
    case_specs: list[tuple[str, Callable[[Path], int]]] = [
        ("master_to_target_single", run_master_to_target_single),
        ("master_to_target_multi", run_master_to_target_multi),
        ("target_to_master_reverse", run_target_to_master_reverse),
    ]

    cases = [run_case(name, runner, iterations=iterations) for name, runner in case_specs]
    baseline_cases = load_baseline_cases(baseline_json) if baseline_json else {}
    apply_baseline_comparison(cases, baseline_cases)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "iterations": iterations,
        "baseline_json": str(baseline_json) if baseline_json else "",
        "cases": cases,
        "summary": build_summary(cases),
    }


def write_report_files(report: dict, report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    json_path = report_dir / f"{stem}.json"
    md_path = report_dir / f"{stem}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(generate_markdown_report(report), encoding="utf-8")
    return md_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lightweight performance baseline.")
    parser.add_argument("--iterations", type=int, default=3, help="Repeat count per case.")
    parser.add_argument(
        "--report-dir",
        default="tests/perf/reports",
        help="Directory to write markdown/json reports.",
    )
    parser.add_argument(
        "--baseline-json",
        default="",
        help="Optional previous JSON report path for delta comparison.",
    )
    args = parser.parse_args()

    iterations = max(1, int(args.iterations))
    baseline_path = Path(args.baseline_json) if args.baseline_json else None
    report = build_report(iterations=iterations, baseline_json=baseline_path)
    md_path, json_path = write_report_files(report, Path(args.report_dir))

    print(f"Performance report written: {md_path}")
    print(f"Performance data written: {json_path}")


if __name__ == "__main__":
    main()
