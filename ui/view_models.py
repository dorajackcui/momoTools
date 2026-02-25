from dataclasses import dataclass


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


@dataclass(frozen=True)
class ReverseConfig:
    target_key_col: int
    target_match_col: int
    target_content_col: int
    master_key_col: int
    master_match_col: int
    master_update_col: int
    fill_blank_only: bool


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


@dataclass(frozen=True)
class StatsConfig:
    source_col: int
    translation_col: int
    stats_mode: str


@dataclass(frozen=True)
class ClearerConfig:
    column_number: int
