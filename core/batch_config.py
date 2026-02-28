import json
import os
from dataclasses import dataclass
from typing import Any, Literal


BATCH_SCHEMA_VERSION = 1
MODE_MASTER_TO_TARGET_SINGLE = "master_to_target_single"
MODE_TARGET_TO_MASTER_REVERSE = "target_to_master_reverse"
VALID_BATCH_MODES = {
    MODE_MASTER_TO_TARGET_SINGLE,
    MODE_TARGET_TO_MASTER_REVERSE,
}

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


@dataclass(frozen=True)
class BatchDefaultsReverse:
    target_key_col: int
    target_match_col: int
    target_content_col: int
    master_key_col: int
    master_match_col: int
    fill_blank_only: bool


@dataclass(frozen=True)
class BatchJobConfig:
    name: str
    target_folder: str
    variable_column: int


@dataclass(frozen=True)
class BatchRuntimeOptions:
    continue_on_error: bool = True


@dataclass(frozen=True)
class BatchLegacyAutoFillRule:
    keyword: str
    variable_column: int


@dataclass(frozen=True)
class BatchConfigV1:
    schema_version: int
    mode: BatchMode
    master_file: str
    defaults: BatchDefaultsSingle | BatchDefaultsReverse
    jobs: tuple[BatchJobConfig, ...]
    runtime: BatchRuntimeOptions
    legacy_auto_fill_rules: tuple[BatchLegacyAutoFillRule, ...] = tuple()


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def validate_config(payload: Any, *, check_paths: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Config must be a JSON object."]

    schema_version = payload.get("schema_version")
    if schema_version != BATCH_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BATCH_SCHEMA_VERSION}.")

    mode = payload.get("mode")
    if mode not in VALID_BATCH_MODES:
        errors.append(
            "mode must be one of: "
            f"{MODE_MASTER_TO_TARGET_SINGLE}, {MODE_TARGET_TO_MASTER_REVERSE}."
        )

    master_file = str(payload.get("master_file", "")).strip()
    if not master_file:
        errors.append("master_file is required.")
    elif check_paths and not os.path.isfile(master_file):
        errors.append(f"master_file not found: {master_file}")

    defaults = payload.get("defaults")
    if not isinstance(defaults, dict):
        errors.append("defaults must be an object.")
        defaults = {}

    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object.")
        runtime = {}
    else:
        continue_on_error = runtime.get("continue_on_error")
        if not isinstance(continue_on_error, bool):
            errors.append("runtime.continue_on_error must be a boolean.")

    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        errors.append("jobs must be an array.")
        jobs = []
    elif len(jobs) == 0:
        errors.append("jobs must contain at least one item.")

    if mode == MODE_MASTER_TO_TARGET_SINGLE:
        errors.extend(_validate_single_defaults(defaults))
    elif mode == MODE_TARGET_TO_MASTER_REVERSE:
        errors.extend(_validate_reverse_defaults(defaults))

    variable_key = _job_variable_key(mode)
    for index, item in enumerate(jobs, start=1):
        prefix = f"jobs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        target_folder = str(item.get("target_folder", "")).strip()
        if not target_folder:
            errors.append(f"{prefix}.target_folder is required.")
        elif check_paths and not os.path.isdir(target_folder):
            errors.append(f"{prefix}.target_folder not found: {target_folder}")

        value = item.get(variable_key)
        if not _is_positive_int(value):
            errors.append(f"{prefix}.{variable_key} must be a positive integer.")

    return errors


def _validate_single_defaults(defaults: dict[str, Any]) -> list[str]:
    required_cols = (
        "target_key_col",
        "target_match_col",
        "target_update_start_col",
        "master_key_col",
        "master_match_col",
    )
    errors: list[str] = []
    for key in required_cols:
        if not _is_positive_int(defaults.get(key)):
            errors.append(f"defaults.{key} must be a positive integer.")

    if not isinstance(defaults.get("fill_blank_only"), bool):
        errors.append("defaults.fill_blank_only must be a boolean.")
    if not isinstance(defaults.get("post_process_enabled"), bool):
        errors.append("defaults.post_process_enabled must be a boolean.")
    return errors


def _validate_reverse_defaults(defaults: dict[str, Any]) -> list[str]:
    required_cols = (
        "target_key_col",
        "target_match_col",
        "target_content_col",
        "master_key_col",
        "master_match_col",
    )
    errors: list[str] = []
    for key in required_cols:
        if not _is_positive_int(defaults.get(key)):
            errors.append(f"defaults.{key} must be a positive integer.")

    if not isinstance(defaults.get("fill_blank_only"), bool):
        errors.append("defaults.fill_blank_only must be a boolean.")
    return errors


def _job_variable_key(mode: Any) -> str:
    if mode == MODE_MASTER_TO_TARGET_SINGLE:
        return "master_content_start_col"
    return "master_update_col"


def load_config(path: str) -> BatchConfigV1:
    with open(path, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    errors = validate_config(payload, check_paths=False)
    if errors:
        raise ValueError("\n".join(errors))
    return _parse_payload(payload)


def dump_config(config: BatchConfigV1, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(to_payload(config), handle, ensure_ascii=False, indent=2)


def to_payload(config: BatchConfigV1) -> dict[str, Any]:
    defaults_payload: dict[str, Any]
    jobs_payload: list[dict[str, Any]] = []

    if config.mode == MODE_MASTER_TO_TARGET_SINGLE:
        defaults = config.defaults
        assert isinstance(defaults, BatchDefaultsSingle)
        defaults_payload = {
            "target_key_col": defaults.target_key_col,
            "target_match_col": defaults.target_match_col,
            "target_update_start_col": defaults.target_update_start_col,
            "master_key_col": defaults.master_key_col,
            "master_match_col": defaults.master_match_col,
            "fill_blank_only": defaults.fill_blank_only,
            "post_process_enabled": defaults.post_process_enabled,
        }
        for job in config.jobs:
            jobs_payload.append(
                {
                    "name": job.name,
                    "target_folder": job.target_folder,
                    "master_content_start_col": job.variable_column,
                }
            )
    else:
        defaults = config.defaults
        assert isinstance(defaults, BatchDefaultsReverse)
        defaults_payload = {
            "target_key_col": defaults.target_key_col,
            "target_match_col": defaults.target_match_col,
            "target_content_col": defaults.target_content_col,
            "master_key_col": defaults.master_key_col,
            "master_match_col": defaults.master_match_col,
            "fill_blank_only": defaults.fill_blank_only,
        }
        for job in config.jobs:
            jobs_payload.append(
                {
                    "name": job.name,
                    "target_folder": job.target_folder,
                    "master_update_col": job.variable_column,
                }
            )

    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "mode": config.mode,
        "master_file": config.master_file,
        "defaults": defaults_payload,
        "jobs": jobs_payload,
        "runtime": {
            "continue_on_error": config.runtime.continue_on_error,
        },
    }


def validate_config_object(config: BatchConfigV1, *, check_paths: bool = False) -> list[str]:
    return validate_config(to_payload(config), check_paths=check_paths)


def template_config(mode: str) -> BatchConfigV1:
    if mode == MODE_MASTER_TO_TARGET_SINGLE:
        defaults: BatchDefaultsSingle | BatchDefaultsReverse = BatchDefaultsSingle(
            target_key_col=1,
            target_match_col=2,
            target_update_start_col=3,
            master_key_col=2,
            master_match_col=3,
            fill_blank_only=False,
            post_process_enabled=True,
        )
        jobs = (BatchJobConfig(name="job-1", target_folder="<target_folder_path>", variable_column=4),)
    else:
        defaults = BatchDefaultsReverse(
            target_key_col=1,
            target_match_col=2,
            target_content_col=3,
            master_key_col=2,
            master_match_col=3,
            fill_blank_only=False,
        )
        jobs = (BatchJobConfig(name="job-1", target_folder="<target_folder_path>", variable_column=4),)

    return BatchConfigV1(
        schema_version=BATCH_SCHEMA_VERSION,
        mode=mode,  # type: ignore[arg-type]
        master_file="<master_file_path>",
        defaults=defaults,
        jobs=jobs,
        runtime=BatchRuntimeOptions(continue_on_error=True),
    )


def _parse_payload(payload: dict[str, Any]) -> BatchConfigV1:
    mode = payload["mode"]
    defaults_payload = payload["defaults"]
    jobs_payload = payload["jobs"]
    runtime_payload = payload["runtime"]

    if mode == MODE_MASTER_TO_TARGET_SINGLE:
        defaults: BatchDefaultsSingle | BatchDefaultsReverse = BatchDefaultsSingle(
            target_key_col=int(defaults_payload["target_key_col"]),
            target_match_col=int(defaults_payload["target_match_col"]),
            target_update_start_col=int(defaults_payload["target_update_start_col"]),
            master_key_col=int(defaults_payload["master_key_col"]),
            master_match_col=int(defaults_payload["master_match_col"]),
            fill_blank_only=bool(defaults_payload["fill_blank_only"]),
            post_process_enabled=bool(defaults_payload["post_process_enabled"]),
        )
        variable_key = "master_content_start_col"
    else:
        defaults = BatchDefaultsReverse(
            target_key_col=int(defaults_payload["target_key_col"]),
            target_match_col=int(defaults_payload["target_match_col"]),
            target_content_col=int(defaults_payload["target_content_col"]),
            master_key_col=int(defaults_payload["master_key_col"]),
            master_match_col=int(defaults_payload["master_match_col"]),
            fill_blank_only=bool(defaults_payload["fill_blank_only"]),
        )
        variable_key = "master_update_col"

    jobs: list[BatchJobConfig] = []
    for index, item in enumerate(jobs_payload, start=1):
        name = str(item.get("name", "")).strip() or f"job-{index}"
        jobs.append(
            BatchJobConfig(
                name=name,
                target_folder=str(item["target_folder"]).strip(),
                variable_column=int(item[variable_key]),
            )
        )

    return BatchConfigV1(
        schema_version=int(payload["schema_version"]),
        mode=mode,
        master_file=str(payload["master_file"]).strip(),
        defaults=defaults,
        jobs=tuple(jobs),
        runtime=BatchRuntimeOptions(
            continue_on_error=bool(runtime_payload["continue_on_error"]),
        ),
        legacy_auto_fill_rules=_parse_legacy_auto_fill_rules(payload.get("auto_fill")),
    )


def _parse_legacy_auto_fill_rules(payload: Any) -> tuple[BatchLegacyAutoFillRule, ...]:
    if not isinstance(payload, dict):
        return tuple()
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list):
        return tuple()

    rules: list[BatchLegacyAutoFillRule] = []
    for item in raw_rules:
        if not isinstance(item, dict):
            continue
        keyword = str(item.get("keyword", "")).strip()
        variable_column = item.get("variable_column")
        if not keyword or not _is_positive_int(variable_column):
            continue
        rules.append(
            BatchLegacyAutoFillRule(
                keyword=keyword,
                variable_column=int(variable_column),
            )
        )
    return tuple(rules)
