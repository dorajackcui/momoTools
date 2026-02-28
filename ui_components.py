"""
Compatibility exports for legacy imports.

The concrete implementations now live under the `ui` package.
"""

from ui.views.base import BaseFrame
from ui.views.batch import BatchFrame
from ui.views.clearer import ClearerFrame
from ui.views.compatibility import CompatibilityFrame
from ui.views.deep_replace import DeepReplaceFrame
from ui.views.multi_column import MultiColumnFrame
from ui.views.reverse_updater import ReverseUpdaterFrame
from ui.views.untranslated_stats import UntranslatedStatsFrame
from ui.views.updater import UpdaterFrame
from ui.widgets.toggle_switch import ToggleSwitch

__all__ = [
    "ToggleSwitch",
    "BaseFrame",
    "BatchFrame",
    "UpdaterFrame",
    "UntranslatedStatsFrame",
    "ClearerFrame",
    "CompatibilityFrame",
    "DeepReplaceFrame",
    "MultiColumnFrame",
    "ReverseUpdaterFrame",
]
