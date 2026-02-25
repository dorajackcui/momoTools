from tkinter import messagebox


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

