import tkinter as tk


def create_action_button(parent, text, command, button_style, pady=10):
    button = tk.Button(parent, text=text, command=command, **button_style)
    button.pack(pady=pady)
    return button


def create_status_label(parent, text, label_style):
    label = tk.Label(parent, text=text, **label_style)
    label.pack()
    return label


def create_labeled_entry(parent, row, column, label_text, variable, width=5, label_padx=(10, 0)):
    tk.Label(parent, text=label_text).grid(row=row, column=column, sticky="w", padx=label_padx)
    entry = tk.Entry(parent, textvariable=variable, width=width)
    entry.grid(row=row, column=column + 1)
    return entry

