from dataclasses import dataclass


@dataclass(frozen=True)
class MasterMergeResult:
    updated_cells: int
    added_rows: int
    merged_keys: int
    source_files: int
    overwritten_cells: int = 0
    filled_blank_cells: int = 0
    skipped_new_keys: int = 0
    unmatched_entries: int = 0
    unmatched_report_path: str = ""
