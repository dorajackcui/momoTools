from ui.views.master_update_base import BaseMasterUpdateFrame


class MergeMastersFrame(BaseMasterUpdateFrame):
    run_button_text = "Run Merge"
    show_combined_key_option = True
    rule_hint_text = "Rule: fill blank only + allow new keys. Key mode can switch between combined and key-only."
