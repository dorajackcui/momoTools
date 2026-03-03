from core.master_update.executors.update_master import UpdateMasterExecutor
from core.master_update.policies import ROW_KEY_POLICY_COMBINED


class UpdateContentExecutor(UpdateMasterExecutor):
    """Overwrite existing master keys only (no new-row append)."""

    required_row_key_policy = ROW_KEY_POLICY_COMBINED
