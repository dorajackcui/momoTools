import os

from core.kernel import iter_excel_files, safe_to_str

from .extractors import BaseExtractor


def discover_and_filter_excel_files(
    input_folder: str,
    extensions: tuple[str, ...],
    configured_files: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    discovered_paths = iter_excel_files(
        input_folder,
        extensions=extensions,
        include_temp_files=False,
        case_sensitive=False,
    )
    file_paths = filter_file_paths(discovered_paths, configured_files)
    return discovered_paths, file_paths


def filter_file_paths(file_paths: list[str], configured_files: tuple[str, ...]) -> list[str]:
    if not configured_files:
        return file_paths
    return [path for path in file_paths if is_configured_file(path, configured_files)]


def is_configured_file(file_path: str, configured_files: tuple[str, ...]) -> bool:
    base_name = os.path.basename(file_path).lower()
    stem = os.path.splitext(base_name)[0]

    for raw_token in configured_files:
        token = raw_token.strip().lower()
        if not token:
            continue
        token_stem, token_ext = os.path.splitext(token)
        if token_ext:
            if base_name == token:
                return True
        else:
            if stem == token or base_name == token:
                return True
            if token_stem and stem == token_stem:
                return True
    return False


def build_header_map(worksheet) -> dict[str, int]:
    header_row = next(worksheet.iter_rows(min_row=1, max_row=1), [])
    header_map: dict[str, int] = {}
    fallback_count = 0
    for index, cell in enumerate(header_row):
        raw = safe_to_str(cell.value if cell else None, strip=True)
        header = raw if raw else f"col_{index + 1}"
        if header in header_map:
            fallback_count += 1
            header = f"{header}_{fallback_count}"
        header_map[header] = index

        # Add a lowercase alias so rule/header matching is case-insensitive
        # (e.g. "Version" can satisfy required "version").
        alias = header.lower()
        if alias not in header_map:
            header_map[alias] = index
    return header_map


def ensure_required_columns(
    file_path: str,
    header_map: dict[str, int],
    extractors: list[BaseExtractor],
    global_versions: tuple[str, ...],
) -> None:
    required: set[str] = set()
    for extractor in extractors:
        required.update(extractor.required_columns())
    if global_versions:
        required.add("version")
    missing = sorted(col for col in required if col not in header_map)
    if missing:
        raise ValueError(
            f"Missing required columns in file {file_path}: {', '.join(missing)}"
        )
