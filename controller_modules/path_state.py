import json
import os

class TerminologyPathStateStore:
    """Persist terminology UI paths under user profile."""

    STATE_KEY_RULE_CONFIG_PATH = "terminology_rule_config_path"

    def __init__(self, state_path=None):
        self.state_path = state_path or self._default_state_path()

    @staticmethod
    def _default_state_path():
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base_dir, "TM_builder", "ui_state.json")

    def load(self):
        if not os.path.exists(self.state_path):
            return {}
        try:
            with open(self.state_path, "r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, state):
        if not isinstance(state, dict):
            return
        try:
            folder = os.path.dirname(self.state_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(self.state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2)
        except Exception:
            return
