from typing import Sequence

from core.master_update.executors.update_master import UpdateMasterExecutor
from core.master_update.policies import ROW_KEY_POLICY_COMBINED


class UpdateContentExecutor(UpdateMasterExecutor):
    """Overwrite existing master keys only (no new-row append)."""

    required_row_key_policy = ROW_KEY_POLICY_COMBINED

    def run(self, source_files: Sequence[str]):
        self.processor.row_key_policy = self.required_row_key_policy
        return self._run_sparse_overwrite(source_files, mode_name="Update Content")
