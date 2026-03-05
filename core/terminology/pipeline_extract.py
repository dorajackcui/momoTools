import os
from dataclasses import dataclass
from typing import Any

from core.kernel import open_workbook, safe_to_str

from .extractors import BaseExtractor, ExtractContext
from .pipeline_discovery import build_header_map, ensure_required_columns
from .types import Candidate


@dataclass(frozen=True)
class FileExtractionResult:
    candidates: list[Candidate]
    rows_scanned: int
    rows_skipped_by_version: int


def extract_file_candidates(
    file_path: str,
    extractors: list[BaseExtractor],
    global_versions: tuple[str, ...],
) -> FileExtractionResult:
    with open_workbook(file_path, read_only=True, data_only=True) as workbook:
        worksheet = workbook.active
        header_map = build_header_map(worksheet)
        ensure_required_columns(file_path, header_map, extractors, global_versions)

        candidates: list[Candidate] = []
        rows_scanned = 0
        rows_skipped_by_version = 0

        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            row_values: dict[str, Any] = {}
            row_cells_text: dict[str, str] = {}
            for header, col_index in header_map.items():
                if col_index < len(row):
                    cell = row[col_index]
                    value = cell.value if cell else None
                else:
                    value = None
                row_values[header] = value
                row_cells_text[header] = safe_to_str(value, strip=False)

            if global_versions:
                version_value = safe_to_str(row_values.get("version"), strip=True)
                if version_value not in global_versions:
                    rows_scanned += 1
                    rows_skipped_by_version += 1
                    continue

            context = ExtractContext(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                sheet_name=worksheet.title,
                row_index=row_idx,
                row_values=row_values,
                row_cells_text=row_cells_text,
                header_map=header_map,
            )
            for extractor in extractors:
                candidates.extend(extractor.extract(context))
            rows_scanned += 1

        return FileExtractionResult(
            candidates=candidates,
            rows_scanned=rows_scanned,
            rows_skipped_by_version=rows_skipped_by_version,
        )
