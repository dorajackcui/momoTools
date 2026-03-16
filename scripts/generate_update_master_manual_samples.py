from __future__ import annotations

import shutil
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


def write_workbook(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sheet1"
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


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


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    build_source_text_samples(OUTPUT_ROOT)
    build_translation_samples(OUTPUT_ROOT)
    print(f"Generated manual sample workbooks under: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
