from core.master_merge_processor import (
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_EXISTING_ONLY,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_COMBINED,
)
from .master_update_base import BaseMasterUpdateController


class UpdateContentController(BaseMasterUpdateController):
    cell_write_policy = CELL_WRITE_POLICY_OVERWRITE_NON_BLANK
    key_admission_policy = KEY_ADMISSION_POLICY_EXISTING_ONLY
    priority_winner_policy = PRIORITY_WINNER_POLICY_LAST_PROCESSED
    row_key_policy_override = ROW_KEY_POLICY_COMBINED
    task_name = "Update Content"
    summary_title = "Updated content using"
