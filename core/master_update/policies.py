CELL_WRITE_POLICY_FILL_BLANK_ONLY = "fill_blank_only"
CELL_WRITE_POLICY_OVERWRITE_NON_BLANK = "overwrite_non_blank"

KEY_ADMISSION_POLICY_ALLOW_NEW = "allow_new_key"
KEY_ADMISSION_POLICY_EXISTING_ONLY = "existing_key_only"

PRIORITY_WINNER_POLICY_LAST_PROCESSED = "last_processed"

ROW_KEY_POLICY_COMBINED = "combined_key"
ROW_KEY_POLICY_KEY_ONLY = "key_only"


def validate_cell_write_policy(value: str) -> str:
    if value not in {
        CELL_WRITE_POLICY_FILL_BLANK_ONLY,
        CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    }:
        raise ValueError(f"Unsupported cell_write_policy: {value}")
    return value


def validate_key_admission_policy(value: str) -> str:
    if value not in {
        KEY_ADMISSION_POLICY_ALLOW_NEW,
        KEY_ADMISSION_POLICY_EXISTING_ONLY,
    }:
        raise ValueError(f"Unsupported key_admission_policy: {value}")
    return value


def validate_priority_winner_policy(value: str) -> str:
    if value not in {PRIORITY_WINNER_POLICY_LAST_PROCESSED}:
        raise ValueError(f"Unsupported priority_winner_policy: {value}")
    return value


def validate_row_key_policy(value: str) -> str:
    if value not in {
        ROW_KEY_POLICY_COMBINED,
        ROW_KEY_POLICY_KEY_ONLY,
    }:
        raise ValueError(f"Unsupported row_key_policy: {value}")
    return value
