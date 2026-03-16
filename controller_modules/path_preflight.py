import hashlib
import os
from dataclasses import dataclass
from typing import Sequence


MASTER_FAILURE_MISSING = "missing"
MASTER_FAILURE_LOCKED_OR_DENIED = "locked_or_denied"
MASTER_FAILURE_UNREADABLE = "unreadable"


@dataclass(frozen=True)
class MasterFileProbeResult:
    ok: bool
    warning_message: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class ExcelFolderProbeResult:
    file_paths: tuple[str, ...]
    sampled_file: str = ""
    sample_writable: bool | None = None
    warning_message: str = ""


def probe_master_file(path: str) -> MasterFileProbeResult:
    normalized_path = str(path or "").strip()
    if not normalized_path:
        return MasterFileProbeResult(
            ok=False,
            warning_message="Please select a master file first.",
            failure_reason=MASTER_FAILURE_MISSING,
        )
    if not os.path.isfile(normalized_path):
        return MasterFileProbeResult(
            ok=False,
            warning_message=f"Master file not found:\n{normalized_path}",
            failure_reason=MASTER_FAILURE_MISSING,
        )
    try:
        with open(normalized_path, "a+b"):
            return MasterFileProbeResult(ok=True)
    except PermissionError:
        return MasterFileProbeResult(
            ok=False,
            warning_message=(
                "Master file may still be open in Excel,\n"
                "or is locked by another program,\n"
                "or you do not have write permission.\n"
                "Please close the file and retry."
            ),
            failure_reason=MASTER_FAILURE_LOCKED_OR_DENIED,
        )
    except OSError as exc:
        return MasterFileProbeResult(
            ok=False,
            warning_message=f"Unable to access master file:\n{normalized_path}\n{exc}",
            failure_reason=MASTER_FAILURE_UNREADABLE,
        )


def select_sample_file(file_paths: Sequence[str], seed_key: str) -> str:
    normalized_paths = [str(path or "").strip() for path in file_paths if str(path or "").strip()]
    if not normalized_paths:
        return ""
    digest = hashlib.sha1(
        f"{seed_key}|{'|'.join(normalized_paths)}".encode("utf-8", errors="ignore")
    ).digest()
    index = int.from_bytes(digest[:4], byteorder="big", signed=False) % len(normalized_paths)
    return normalized_paths[index]


def probe_excel_file_writable(path: str) -> tuple[bool, str]:
    normalized_path = str(path or "").strip()
    if not normalized_path:
        return False, "No Excel file available for writable check."
    if not os.path.isfile(normalized_path):
        return False, f"Excel file not found:\n{normalized_path}"
    try:
        with open(normalized_path, "a+b"):
            return True, ""
    except PermissionError:
        return (
            False,
            (
                "Sampled target file is read-only, open in Excel, or not writable.\n"
                f"File: {normalized_path}"
            ),
        )
    except OSError as exc:
        return False, f"Unable to access sampled target file:\n{normalized_path}\n{exc}"


def probe_excel_folder(
    file_paths: Sequence[str],
    *,
    require_writable_sample: bool = False,
    sample_seed_key: str = "",
) -> ExcelFolderProbeResult:
    normalized_paths = tuple(str(path or "").strip() for path in file_paths if str(path or "").strip())
    if not normalized_paths:
        return ExcelFolderProbeResult(
            file_paths=tuple(),
            warning_message="No Excel files found in the selected folder.",
        )

    if not require_writable_sample:
        return ExcelFolderProbeResult(file_paths=normalized_paths)

    sampled_file = select_sample_file(normalized_paths, seed_key=sample_seed_key)
    sample_writable, warning_message = probe_excel_file_writable(sampled_file)
    return ExcelFolderProbeResult(
        file_paths=normalized_paths,
        sampled_file=sampled_file,
        sample_writable=sample_writable,
        warning_message=warning_message,
    )


def build_preview_items(file_paths: Sequence[str], root_folder: str) -> list[str]:
    preview_items: list[str] = []
    normalized_root = os.path.abspath(str(root_folder or "").strip()) if root_folder else ""
    for path in file_paths:
        normalized_path = str(path or "").strip()
        if not normalized_path:
            continue
        try:
            if normalized_root:
                relative_path = os.path.relpath(normalized_path, normalized_root)
                preview_items.append(relative_path)
                continue
        except ValueError:
            pass
        preview_items.append(os.path.basename(normalized_path) or normalized_path)
    return preview_items
