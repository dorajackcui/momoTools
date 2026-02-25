from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class ColumnSpec:
    key_col: int
    match_col: int
    value_col: Optional[int] = None
    value_start_col: Optional[int] = None
    count: Optional[int] = None


@dataclass(frozen=True)
class ModeIOContract:
    mode_name: str
    skip_header: bool
    extensions: Tuple[str, ...] = (".xlsx", ".xls")
    key_separator: str = "|"


@dataclass
class ErrorEvent:
    code: str
    message: str
    file_path: str = ""
    row: Optional[int] = None
    col: Optional[int] = None
    exception: Optional[BaseException] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def as_log_line(self) -> str:
        parts = [f"[{self.code}]", self.message]
        if self.file_path:
            parts.append(f"file={self.file_path}")
        if self.row is not None:
            parts.append(f"row={self.row}")
        if self.col is not None:
            parts.append(f"col={self.col}")
        if self.context:
            context_text = ", ".join(f"{k}={v}" for k, v in sorted(self.context.items()))
            parts.append(f"context={context_text}")
        if self.exception is not None:
            parts.append(f"error={self.exception}")
        return " | ".join(parts)


@dataclass
class ProcessingStats:
    files_total: int = 0
    files_succeeded: int = 0
    files_failed: int = 0
    rows_scanned: int = 0
    cells_updated: int = 0
    errors: list[ErrorEvent] = field(default_factory=list)

    def add_error(self, event: ErrorEvent) -> None:
        self.errors.append(event)

