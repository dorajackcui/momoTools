import unittest

from ui import strings
from ui.views.base import BaseFrame


class FakeTooltip:
    def __init__(self):
        self.text = None

    def set_text(self, text):
        self.text = text


class FakeLabel:
    def __init__(self):
        self.text = ""
        self._path_tooltip = FakeTooltip()
        self._full_path = ""

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]


class PathLabelTestCase(unittest.TestCase):
    def test_set_selected_path_label_shows_short_name_and_full_path_tooltip(self):
        label = FakeLabel()
        path = r"C:\very\long\folder\master.xlsx"

        BaseFrame.set_selected_file_label(label, path)

        self.assertEqual(label.text, strings.selected_path_text(path))
        self.assertEqual(label._full_path, path)
        self.assertEqual(label._path_tooltip.text, path)

    def test_set_selected_path_label_empty_path_clears_tooltip(self):
        label = FakeLabel()

        BaseFrame.set_selected_path_label(label, "")

        self.assertEqual(label.text, strings.DEFAULT_FOLDER_TEXT)
        self.assertEqual(label._full_path, "")
        self.assertEqual(label._path_tooltip.text, "")


if __name__ == "__main__":
    unittest.main()
