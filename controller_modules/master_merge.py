from core.master_merge_processor import (
    CELL_WRITE_POLICY_FILL_BLANK_ONLY,
    KEY_ADMISSION_POLICY_ALLOW_NEW,
    PRIORITY_WINNER_POLICY_LAST_PROCESSED,
)
from .master_update_base import BaseMasterUpdateController


class MasterMergeController(BaseMasterUpdateController):
    cell_write_policy = CELL_WRITE_POLICY_FILL_BLANK_ONLY
    key_admission_policy = KEY_ADMISSION_POLICY_ALLOW_NEW
    priority_winner_policy = PRIORITY_WINNER_POLICY_LAST_PROCESSED
    task_name = "Merge Masters"
    summary_title = "Merged"
