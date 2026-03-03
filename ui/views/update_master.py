from ui.views.master_update_base import BaseMasterUpdateFrame


class UpdateMasterFrame(BaseMasterUpdateFrame):
    run_button_text = "Run Update Master"
    rule_hint_text = "Rule: key-only match + overwrite with non-blank values + allow new keys (match is updatable content)."
