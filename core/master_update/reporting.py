import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import openpyxl


DEFAULT_REPORT_STEM = "translation_unmatched_report"
DEFAULT_REPORT_SHEET = "unmatched_summary"


@dataclass(frozen=True)
class UnmatchedIdentityInfo:
    key_text: str
    match_text: str
    source_file: str
    content_values: tuple[Any, ...]


@dataclass(frozen=True)
class UnmatchedReportRow:
    key: str
    match: str
    source_file: str
    content_values: tuple[Any, ...]


def build_unmatched_report_path(update_folder: str, *, stem: str = DEFAULT_REPORT_STEM) -> str:
    normalized_folder = os.path.normpath(str(update_folder or "").strip())
    parent_folder = os.path.dirname(normalized_folder) or normalized_folder or "."
    extension = ".xlsx"
    output_path = os.path.join(parent_folder, f"{stem}{extension}")
    if not os.path.exists(output_path):
        return output_path

    index = 1
    while True:
        candidate = os.path.join(parent_folder, f"{stem} ({index}){extension}")
        if not os.path.exists(candidate):
            return candidate
        index += 1


def build_unmatched_report_rows(
    unmatched_by_identity: Mapping[str, UnmatchedIdentityInfo],
) -> list[UnmatchedReportRow]:
    return [
        UnmatchedReportRow(
            key=info.key_text,
            match=info.match_text,
            source_file=info.source_file,
            content_values=info.content_values,
        )
        for info in sorted(
            unmatched_by_identity.values(),
            key=lambda item: (item.key_text, item.match_text, item.source_file),
        )
    ]


def build_unmatched_report_headers(content_col_indexes: Sequence[int]) -> list[str]:
    return ["key", "match", "source_file"] + [
        f"content_col_{col_idx + 1}" for col_idx in content_col_indexes
    ]


def export_unmatched_report(
    output_path: str,
    rows: Iterable[UnmatchedReportRow],
    *,
    content_col_indexes: Sequence[int],
    sheet_name: str = DEFAULT_REPORT_SHEET,
) -> str:
    workbook = openpyxl.Workbook()
    try:
        worksheet = workbook.active
        worksheet.title = sheet_name
        worksheet.append(build_unmatched_report_headers(content_col_indexes))
        for row in rows:
            worksheet.append([row.key, row.match, row.source_file, *row.content_values])
        workbook.save(output_path)
    finally:
        workbook.close()
    return output_path
