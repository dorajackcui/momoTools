from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UpdaterConfig:
    target_key_col: int
    target_match_col: int
    target_update_start_col: int
    master_key_col: int
    master_match_col: int
    master_content_start_col: int
    column_count: int
    fill_blank_only: bool
    post_process_enabled: bool
    allow_blank_write: bool = False


@dataclass(frozen=True)
class ReverseConfig:
    target_key_col: int
    target_match_col: int
    target_content_col: int
    master_key_col: int
    master_match_col: int
    master_update_col: int
    fill_blank_only: bool
    allow_blank_write: bool = False


@dataclass(frozen=True)
class MultiColumnConfig:
    target_key_col: int
    target_match_col: int
    target_update_start_col: int
    master_key_col: int
    master_match_col: int
    master_start_col: int
    column_count: int
    fill_blank_only: bool
    post_process_enabled: bool
    allow_blank_write: bool = False


@dataclass(frozen=True)
class StatsConfig:
    source_col: int
    translation_col: int
    stats_mode: str


@dataclass(frozen=True)
class ClearerConfig:
    column_number: int


@dataclass(frozen=True)
class MasterUpdateConfig:
    key_col: int
    match_col: int
    priority_files: tuple[str, ...]
    last_update_col: int = 10
    use_combined_key: bool = True

# Backward compatibility for early Merge Masters rollout.
MergeMastersConfig = MasterUpdateConfig


@dataclass(frozen=True)
class SourceTranslationPipelineConfig:
    key_col: int
    match_col: int
    source_priority_files: tuple[str, ...]
    translation_priority_files: tuple[str, ...]
    last_update_col: int = 10


BatchMode = Literal["master_to_target_single", "target_to_master_reverse"]


@dataclass(frozen=True)
class BatchDefaultsSingle:
    target_key_col: int
    target_match_col: int
    target_update_start_col: int
    master_key_col: int
    master_match_col: int
    fill_blank_only: bool
    post_process_enabled: bool
    allow_blank_write: bool = False


@dataclass(frozen=True)
class BatchDefaultsReverse:
    target_key_col: int
    target_match_col: int
    target_content_col: int
    master_key_col: int
    master_match_col: int
    fill_blank_only: bool
    allow_blank_write: bool = False


@dataclass(frozen=True)
class BatchJobRow:
    name: str
    target_folder: str
    variable_column: int


@dataclass(frozen=True)
class BatchAutoFillRule:
    keyword: str
    variable_column: int


@dataclass(frozen=True)
class BatchRuntimeOptions:
    continue_on_error: bool


@dataclass(frozen=True)
class BatchViewConfig:
    mode: BatchMode
    master_file: str
    config_path: str
    defaults_single: BatchDefaultsSingle
    defaults_reverse: BatchDefaultsReverse
    jobs: tuple[BatchJobRow, ...]
    runtime: BatchRuntimeOptions
