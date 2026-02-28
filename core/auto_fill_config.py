import json
import os
from dataclasses import dataclass
from typing import Any


AUTO_FILL_MATCH_RULE_PREFIX = "prefix"
AUTO_FILL_SCAN_DEPTH = 1


@dataclass(frozen=True)
class AutoFillRule:
    keyword: str
    variable_column: int


@dataclass(frozen=True)
class AutoFillConfig:
    rules: tuple[AutoFillRule, ...] = tuple()
    match_rule: str = AUTO_FILL_MATCH_RULE_PREFIX
    scan_depth: int = AUTO_FILL_SCAN_DEPTH


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def validate_payload(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["auto_fill config must be a JSON object."]

    match_rule = str(payload.get("match_rule", AUTO_FILL_MATCH_RULE_PREFIX)).strip()
    if match_rule != AUTO_FILL_MATCH_RULE_PREFIX:
        errors.append(f"match_rule must be '{AUTO_FILL_MATCH_RULE_PREFIX}'.")

    scan_depth = payload.get("scan_depth", AUTO_FILL_SCAN_DEPTH)
    if scan_depth != AUTO_FILL_SCAN_DEPTH:
        errors.append(f"scan_depth must be {AUTO_FILL_SCAN_DEPTH}.")

    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        errors.append("rules must be an array.")
        return errors

    for index, item in enumerate(rules, start=1):
        prefix = f"rules[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        keyword = str(item.get("keyword", "")).strip()
        if not keyword:
            errors.append(f"{prefix}.keyword is required.")
        if not _is_positive_int(item.get("variable_column")):
            errors.append(f"{prefix}.variable_column must be a positive integer.")

    return errors


def parse_payload(payload: Any, *, strict: bool = True) -> AutoFillConfig:
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        if strict:
            raise ValueError("auto_fill config must be a JSON object.")
        payload = {}

    if strict:
        errors = validate_payload(payload)
        if errors:
            raise ValueError("\n".join(errors))

    rules_payload = payload.get("rules", [])
    rules: list[AutoFillRule] = []
    if isinstance(rules_payload, list):
        for item in rules_payload:
            if not isinstance(item, dict):
                continue
            keyword = str(item.get("keyword", "")).strip()
            variable_column = item.get("variable_column")
            if not keyword or not _is_positive_int(variable_column):
                continue
            rules.append(
                AutoFillRule(
                    keyword=keyword,
                    variable_column=int(variable_column),
                )
            )

    match_rule = str(payload.get("match_rule", AUTO_FILL_MATCH_RULE_PREFIX)).strip() or AUTO_FILL_MATCH_RULE_PREFIX
    scan_depth = payload.get("scan_depth", AUTO_FILL_SCAN_DEPTH)
    if not isinstance(scan_depth, int):
        scan_depth = AUTO_FILL_SCAN_DEPTH

    if match_rule != AUTO_FILL_MATCH_RULE_PREFIX:
        match_rule = AUTO_FILL_MATCH_RULE_PREFIX
    if scan_depth != AUTO_FILL_SCAN_DEPTH:
        scan_depth = AUTO_FILL_SCAN_DEPTH

    return AutoFillConfig(
        rules=tuple(rules),
        match_rule=match_rule,
        scan_depth=scan_depth,
    )


def to_payload(config: AutoFillConfig) -> dict[str, Any]:
    return {
        "rules": [
            {
                "keyword": rule.keyword,
                "variable_column": rule.variable_column,
            }
            for rule in config.rules
        ],
        "match_rule": config.match_rule,
        "scan_depth": config.scan_depth,
    }


def load_auto_fill_config(path: str) -> AutoFillConfig:
    if not path or not os.path.isfile(path):
        return AutoFillConfig()
    with open(path, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return parse_payload(payload, strict=False)


def save_auto_fill_config(config: AutoFillConfig, path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(to_payload(config), handle, ensure_ascii=False, indent=2)
