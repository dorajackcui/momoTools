from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "tests" / "manual_data" / "update_master_samples"

HEADERS = [
    "ID",
    "Key",
    "Source Text",
    "Context",
    "Comment",
    "Translation",
    "Status",
    "Reviewer",
    "Notes",
    "Extra",
    "Last Update",
]


def write_workbook(
    path: Path,
    rows: list[list[object]],
    *,
    cell_formats: dict[tuple[int, int], str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sheet1"
    for row in rows:
        worksheet.append(row)
    for (row_idx, col_idx), number_format in (cell_formats or {}).items():
        worksheet.cell(row=row_idx, column=col_idx).number_format = number_format
    workbook.save(path)
    workbook.close()


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def stringify_expected_content(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def build_source_text_samples(base_dir: Path) -> None:
    case_dir = base_dir / "source_text"
    updates_dir = case_dir / "updates"
    expected_dir = case_dir / "expected"
    reset_directory(case_dir)
    updates_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    master_rows = [
        HEADERS,
        [1001, "K001", "Old source 1", "UI", "master-comment-1", "旧译文1", "draft", "Alice", "master-note-1", "A1", "2026-03-01"],
        [1002, "K002", "Old source 2", "UI", "master-comment-2", "旧译文2", "review", "Bob", "master-note-2", "A2", "2026-03-01"],
        [1003, "K003", "Old source 3", "Battle", "master-comment-3", "旧译文3", "done", "Cathy", "master-note-3", "A3", "2026-03-01"],
    ]
    update_a_rows = [
        HEADERS,
        [1001, "K001", "Source from vendor A", "UI", "vendor-a-comment", "供应商A译文", "draft", "VendorA", "picked-a", "B1", "2026-03-10"],
        [1003, "K003", "Source A for K003", "Battle", "vendor-a-k003", "A版译文3", "review", "VendorA", "candidate-a", "B3", "2026-03-10"],
        [1004, "K004", "Brand new source", "Shop", "new-key-a", "新增译文4", "new", "VendorA", "new-row", "B4", "2026-03-10"],
    ]
    update_b_rows = [
        HEADERS,
        [1001, "K001", "Final source from vendor B", "Menu", "", "", "approved", "VendorB", "picked-b", "", "2026-03-12"],
        [1003, "K003", "Final source for K003", "Battle", "vendor-b-k003", "最终译文3", "approved", "VendorB", "", "C3", "2026-03-12"],
    ]
    expected_rows = [
        HEADERS,
        [1001, "K001", "Final source from vendor B", "Menu", "", "", "approved", "VendorB", "picked-b", "", "2026-03-12"],
        [1002, "K002", "Old source 2", "UI", "master-comment-2", "旧译文2", "review", "Bob", "master-note-2", "A2", "2026-03-01"],
        [1003, "K003", "Final source for K003", "Battle", "vendor-b-k003", "最终译文3", "approved", "VendorB", "", "C3", "2026-03-12"],
        [1004, "K004", "Brand new source", "Shop", "new-key-a", "新增译文4", "new", "VendorA", "new-row", "B4", "2026-03-10"],
    ]

    write_workbook(case_dir / "master.xlsx", master_rows)
    write_workbook(updates_dir / "01_vendor_a.xlsx", update_a_rows)
    write_workbook(updates_dir / "02_vendor_b.xlsx", update_b_rows)
    write_workbook(expected_dir / "master_after_run.xlsx", expected_rows)


def build_translation_samples(base_dir: Path) -> None:
    case_dir = base_dir / "translation"
    updates_dir = case_dir / "updates"
    expected_dir = case_dir / "expected"
    reset_directory(case_dir)
    updates_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    master_rows = [
        HEADERS,
        [2001, "T001", "Play", "Button", "master-comment-1", "玩", "draft", "Luna", "master-note-1", "X1", "2026-03-01"],
        [2002, "T002", "Exit", "Button", "master-comment-2", "退出程序", "review", "Ming", "master-note-2", "X2", "2026-03-01"],
        [2003, "T003", "Options", "Menu", "master-comment-3", "", "todo", "Nora", "", "X3", "2026-03-01"],
    ]
    update_a_rows = [
        HEADERS,
        [2001, "T001", "Play", "Button", "lqa-a", "游玩", "lqa", "QA_A", "candidate-a", "Y1", "2026-03-08"],
        [2002, "T002", "Exit", "Button", "lqa-a-2", "", "", "QA_A", "", "", "2026-03-08"],
        [2004, "T004", "Credits", "Menu", "new-key", "制作名单", "new", "QA_A", "should-skip", "Y4", "2026-03-08"],
    ]
    update_b_rows = [
        HEADERS,
        [2001, "T001", "Play", "Button", "", "开始游戏", "approved", "QA_B", "", "Z1", "2026-03-12"],
        [2002, "T002", "Exit", "Button", "", "退出", "", "QA_B", "final-b", "", "2026-03-12"],
        [2003, "T003", "Options", "Menu", "final-k003", "选项", "approved", "QA_B", "", "Z3", "2026-03-12"],
        [2001, "T001", "Play now", "Button", "mismatch-source", "立即开始", "approved", "QA_B", "should-skip", "Z9", "2026-03-12"],
    ]
    expected_rows = [
        HEADERS,
        [2001, "T001", "Play", "Button", "lqa-a", "开始游戏", "approved", "QA_B", "candidate-a", "Z1", "2026-03-12"],
        [2002, "T002", "Exit", "Button", "lqa-a-2", "退出", "review", "QA_B", "final-b", "X2", "2026-03-12"],
        [2003, "T003", "Options", "Menu", "final-k003", "选项", "approved", "QA_B", "", "Z3", "2026-03-12"],
    ]

    write_workbook(case_dir / "master.xlsx", master_rows)
    write_workbook(updates_dir / "01_lqa_round.xlsx", update_a_rows)
    write_workbook(updates_dir / "02_final_round.xlsx", update_b_rows)
    write_workbook(expected_dir / "master_after_run.xlsx", expected_rows)


def build_source_text_content_corner_samples(base_dir: Path) -> None:
    case_dir = base_dir / "source_text_content_corners"
    updates_dir = case_dir / "updates"
    expected_dir = case_dir / "expected"
    reset_directory(case_dir)
    updates_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    master_rows = [
        HEADERS,
        [3001, "C001", "Source None", "UI", "master", "OLD_NONE", "draft", "Alice", "master-note", "M1", "2026-03-01"],
        [3002, "C002", "Source NaN", "UI", "master", "OLD_NAN", "draft", "Alice", "master-note", "M2", "2026-03-01"],
        [3003, "C003", "Source Zero", "UI", "master", "OLD_ZERO", "draft", "Alice", "master-note", "M3", "2026-03-01"],
        [3004, "C004", "Source Zero Float", "UI", "master", "OLD_ZERO_FLOAT", "draft", "Alice", "master-note", "M4", "2026-03-01"],
        [3005, "C005", "Source Blank", "UI", "master", "OLD_BLANK", "draft", "Alice", "master-note", "M5", "2026-03-01"],
        [3006, "C006", "Source Spaces", "UI", "master", "OLD_SPACES", "draft", "Alice", "master-note", "M6", "2026-03-01"],
        [3011, "C011", "Source Fraction", "UI", "master", "OLD_FRACTION", "draft", "Alice", "master-note", "M11", "2026-03-01"],
    ]
    update_rows = [
        HEADERS,
        [3001, "C001", "Source None", "UI", "literal-none", "None", "approved", "Vendor", "expect literal None", "U1", "2026-03-15"],
        [3002, "C002", "Source NaN", "UI", "literal-nan", "NaN", "approved", "Vendor", "expect literal NaN", "U2", "2026-03-15"],
        [3003, "C003", "Source Zero", "UI", "numeric-zero", 0, "approved", "Vendor", "expect numeric zero", "U3", "2026-03-15"],
        [3004, "C004", "Source Zero Float", "UI", "numeric-zero-float", 0.0, "approved", "Vendor", "0.0 round-trips as numeric zero", "U4", "2026-03-15"],
        [3005, "C005", "Source Blank", "UI", "blank-clears", None, "approved", "Vendor", "expect cleared cell", "U5", "2026-03-15"],
        [3006, "C006", "Source Spaces", "UI", "spaces-preserved", "   ", "approved", "Vendor", "expect spaces preserved", "U6", "2026-03-15"],
        [3007, "C007", "Brand New Literal", "UI", "append-none", "None", "new", "Vendor", "new row keeps literal None", "U7", "2026-03-15"],
        [3008, "C008", "Source Decimal", "UI", "decimal-value", 12.34, "approved", "Vendor", "expect decimal value", "U8", "2026-03-15"],
        [3009, "C009", "Source Percent", "UI", "percent-value", 0.25, "approved", "Vendor", "expect 25% with percent format", "U9", "2026-03-15"],
        [3010, "C010", "Source Date", "UI", "date-value", date(2026, 3, 16), "approved", "Vendor", "expect Excel date value", "U10", "2026-03-15"],
        [3011, "C011", "Source Fraction", "UI", "fraction-value", 1 / 3, "approved", "Vendor", "expect 1/3 with fraction format", "U11", "2026-03-15"],
    ]
    expected_rows = [
        HEADERS,
        [3001, "C001", "Source None", "UI", "literal-none", "None", "approved", "Vendor", "expect literal None", "U1", "2026-03-15"],
        [3002, "C002", "Source NaN", "UI", "literal-nan", "NaN", "approved", "Vendor", "expect literal NaN", "U2", "2026-03-15"],
        [3003, "C003", "Source Zero", "UI", "numeric-zero", stringify_expected_content(0), "approved", "Vendor", "expect text 0", "U3", "2026-03-15"],
        [3004, "C004", "Source Zero Float", "UI", "numeric-zero-float", stringify_expected_content(0.0), "approved", "Vendor", "expect text 0.0", "U4", "2026-03-15"],
        [3005, "C005", "Source Blank", "UI", "blank-clears", stringify_expected_content(None), "approved", "Vendor", "expect cleared cell", "U5", "2026-03-15"],
        [3006, "C006", "Source Spaces", "UI", "spaces-preserved", "   ", "approved", "Vendor", "expect spaces preserved", "U6", "2026-03-15"],
        [3007, "C007", "Brand New Literal", "UI", "append-none", "None", "new", "Vendor", "new row keeps literal None", "U7", "2026-03-15"],
        [3008, "C008", "Source Decimal", "UI", "decimal-value", stringify_expected_content(12.34), "approved", "Vendor", "expect text 12.34", "U8", "2026-03-15"],
        [3009, "C009", "Source Percent", "UI", "percent-value", stringify_expected_content(0.25), "approved", "Vendor", "expect text 0.25", "U9", "2026-03-15"],
        [3010, "C010", "Source Date", "UI", "date-value", "2026-03-16 00:00:00", "approved", "Vendor", "expect text from str(value)", "U10", "2026-03-15"],
        [3011, "C011", "Source Fraction", "UI", "fraction-value", stringify_expected_content(1 / 3), "approved", "Vendor", "expect text 0.3333333333333333", "U11", "2026-03-15"],
    ]
    content_formats = {
        (9, 6): "0.00",
        (10, 6): "0%",
        (11, 6): "yyyy-mm-dd",
        (12, 6): "# ?/?",
    }

    write_workbook(case_dir / "master.xlsx", master_rows)
    write_workbook(updates_dir / "01_content_corner_cases.xlsx", update_rows, cell_formats=content_formats)
    write_workbook(expected_dir / "master_after_run.xlsx", expected_rows)


def build_translation_content_corner_samples(base_dir: Path) -> None:
    case_dir = base_dir / "translation_content_corners"
    updates_dir = case_dir / "updates"
    expected_dir = case_dir / "expected"
    reset_directory(case_dir)
    updates_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    master_rows = [
        HEADERS,
        [4001, "D001", "Source None", "UI", "master", "OLD_NONE", "draft", "Luna", "master-note", "T1", "2026-03-01"],
        [4002, "D002", "Source NaN", "UI", "master", "OLD_NAN", "draft", "Luna", "master-note", "T2", "2026-03-01"],
        [4003, "D003", "Source Zero", "UI", "master", "OLD_ZERO", "draft", "Luna", "master-note", "T3", "2026-03-01"],
        [4004, "D004", "Source Zero Float", "UI", "master", "OLD_ZERO_FLOAT", "draft", "Luna", "0.0 round-trips as numeric zero", "T4", "2026-03-01"],
        [4005, "D005", "Source Blank", "UI", "master", "KEEP_BLANK", "draft", "Luna", "master-note", "T5", "2026-03-01"],
        [4006, "D006", "Source Spaces", "UI", "master", "KEEP_SPACES", "draft", "Luna", "master-note", "T6", "2026-03-01"],
        [4007, "D007", "Source Decimal", "UI", "master", "OLD_DECIMAL", "draft", "Luna", "master-note", "T7", "2026-03-01"],
        [4008, "D008", "Source Percent", "UI", "master", "OLD_PERCENT", "draft", "Luna", "master-note", "T8", "2026-03-01"],
        [4009, "D009", "Source Date", "UI", "master", "OLD_DATE", "draft", "Luna", "master-note", "T9", "2026-03-01"],
        [4010, "D010", "Source Fraction", "UI", "master", "OLD_FRACTION", "draft", "Luna", "master-note", "T10", "2026-03-01"],
    ]
    update_rows = [
        HEADERS,
        [4001, "D001", "Source None", "UI", "literal-none", "None", "approved", "QA", "expect literal None", "V1", "2026-03-15"],
        [4002, "D002", "Source NaN", "UI", "literal-nan", "NaN", "approved", "QA", "expect literal NaN", "V2", "2026-03-15"],
        [4003, "D003", "Source Zero", "UI", "numeric-zero", 0, "approved", "QA", "expect numeric zero", "V3", "2026-03-15"],
        [4004, "D004", "Source Zero Float", "UI", "numeric-zero-float", 0.0, "approved", "QA", "0.0 round-trips as numeric zero", "V4", "2026-03-15"],
        [4005, "D005", "Source Blank", "UI", "blank-skipped", None, "approved", "QA", "blank should not overwrite", "V5", "2026-03-15"],
        [4006, "D006", "Source Spaces", "UI", "spaces-skipped", "   ", "approved", "QA", "spaces should not overwrite", "V6", "2026-03-15"],
        [4007, "D007", "Source Decimal", "UI", "decimal-value", 12.34, "approved", "QA", "expect decimal value", "V7", "2026-03-15"],
        [4008, "D008", "Source Percent", "UI", "percent-value", 0.25, "approved", "QA", "expect 25% with percent format", "V8", "2026-03-15"],
        [4009, "D009", "Source Date", "UI", "date-value", date(2026, 3, 16), "approved", "QA", "expect Excel date value", "V9", "2026-03-15"],
        [4010, "D010", "Source Fraction", "UI", "fraction-value", 1 / 3, "approved", "QA", "expect 1/3 with fraction format", "V10", "2026-03-15"],
    ]
    expected_rows = [
        HEADERS,
        [4001, "D001", "Source None", "UI", "literal-none", "None", "approved", "QA", "expect literal None", "V1", "2026-03-15"],
        [4002, "D002", "Source NaN", "UI", "literal-nan", "NaN", "approved", "QA", "expect literal NaN", "V2", "2026-03-15"],
        [4003, "D003", "Source Zero", "UI", "numeric-zero", stringify_expected_content(0), "approved", "QA", "expect text 0", "V3", "2026-03-15"],
        [4004, "D004", "Source Zero Float", "UI", "numeric-zero-float", stringify_expected_content(0.0), "approved", "QA", "expect text 0.0", "V4", "2026-03-15"],
        [4005, "D005", "Source Blank", "UI", "blank-skipped", "KEEP_BLANK", "approved", "QA", "blank should not overwrite", "V5", "2026-03-15"],
        [4006, "D006", "Source Spaces", "UI", "spaces-skipped", "KEEP_SPACES", "approved", "QA", "spaces should not overwrite", "V6", "2026-03-15"],
        [4007, "D007", "Source Decimal", "UI", "decimal-value", stringify_expected_content(12.34), "approved", "QA", "expect text 12.34", "V7", "2026-03-15"],
        [4008, "D008", "Source Percent", "UI", "percent-value", stringify_expected_content(0.25), "approved", "QA", "expect text 0.25", "V8", "2026-03-15"],
        [4009, "D009", "Source Date", "UI", "date-value", "2026-03-16 00:00:00", "approved", "QA", "expect text from str(value)", "V9", "2026-03-15"],
        [4010, "D010", "Source Fraction", "UI", "fraction-value", stringify_expected_content(1 / 3), "approved", "QA", "expect text 0.3333333333333333", "V10", "2026-03-15"],
    ]
    content_formats = {
        (8, 6): "0.00",
        (9, 6): "0%",
        (10, 6): "yyyy-mm-dd",
        (11, 6): "# ?/?",
    }

    write_workbook(case_dir / "master.xlsx", master_rows, cell_formats=content_formats)
    write_workbook(updates_dir / "01_content_corner_cases.xlsx", update_rows, cell_formats=content_formats)
    write_workbook(expected_dir / "master_after_run.xlsx", expected_rows)


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    build_source_text_samples(OUTPUT_ROOT)
    build_translation_samples(OUTPUT_ROOT)
    build_source_text_content_corner_samples(OUTPUT_ROOT)
    build_translation_content_corner_samples(OUTPUT_ROOT)
    print(f"Generated manual sample workbooks under: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
