from tkinter import messagebox

from ui.widgets.file_list_confirm_dialog import FileListConfirmDialog


class DialogService:
    """Messagebox adapter to make UI notifications testable."""

    def info(self, title, message):
        messagebox.showinfo(title, message)

    def error(self, title, message):
        messagebox.showerror(title, message)

    def warning(self, title, message):
        messagebox.showwarning(title, message)

    def confirm(self, title, message):
        return messagebox.askyesno(title, message)

    def confirm_file_list(self, parent, title, file_paths, summary_lines, warning_message=None):
        dialog = FileListConfirmDialog(
            parent,
            title=title,
            file_paths=list(file_paths),
            summary_lines=list(summary_lines),
            warning_message=warning_message,
        )
        return dialog.show()
