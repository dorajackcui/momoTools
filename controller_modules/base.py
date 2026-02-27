from tkinter import filedialog
from ui.dialog_service import DialogService

class BaseController:
    def __init__(self, frame, dialog_service=None):
        self.frame = frame
        self.dialogs = dialog_service or DialogService()

    def _require_frame(self):
        if self.frame is None:
            raise RuntimeError("UI frame is not attached")
        return self.frame

    @staticmethod
    def _ask_excel_file(title):
        return filedialog.askopenfilename(
            title=title,
            filetypes=[("Excel 文件", "*.xlsx *.xls")],
        )

    @staticmethod
    def _ask_folder(title):
        return filedialog.askdirectory(title=title)

    @staticmethod
    def _ask_output_excel_file(title):
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
        )
