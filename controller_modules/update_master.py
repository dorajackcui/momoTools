from core.master_merge_processor import (
    CELL_WRITE_POLICY_OVERWRITE_NON_BLANK,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
    ROW_KEY_POLICY_KEY_ONLY,
)
from .master_update_base import BaseMasterUpdateController


class UpdateMasterController(BaseMasterUpdateController):
    cell_write_policy = CELL_WRITE_POLICY_OVERWRITE_NON_BLANK
    key_admission_policy = KEY_ADMISSION_POLICY_ALLOW_NEW
    priority_winner_policy = PRIORITY_WINNER_POLICY_LAST_PROCESSED
    row_key_policy_override = ROW_KEY_POLICY_KEY_ONLY
    task_name = "Update Master"
    summary_title = "Updated master using"
