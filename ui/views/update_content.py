from ui.views.master_update_base import BaseMasterUpdateFrame


class UpdateContentFrame(BaseMasterUpdateFrame):
    run_button_text = "Run Update Content"
    rule_hint_text = "Rule: combined key (key + match) + overwrite with non-blank values + existing keys only."
