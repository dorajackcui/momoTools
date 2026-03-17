import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import ValidationError, parse_column_1_based_to_0_based
from ui.view_models import MasterUpdateConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_labeled_entry


class BaseMasterUpdateFrame(BaseFrame):
    run_button_text = "Run"
    rule_hint_text = ""
    show_combined_key_option = False

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.priority_files: list[str] = []
        self._drag_index: int | None = None
        self.init_ui()

    def init_ui(self):
        self.page_canvas = tk.Canvas(
            self,
            bg=theme.APP_BG,
            highlightthickness=0,
            bd=0,
        )
        self.page_canvas.pack(side="left", fill="both", expand=True)
        self.page_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.page_canvas.yview)
        self.page_scrollbar.pack(side="right", fill="y")
        self.page_canvas.configure(yscrollcommand=self.page_scrollbar.set)

        self.page_body = ttk.Frame(self.page_canvas, style="App.TFrame")
        self.page_body_window = self.page_canvas.create_window((0, 0), window=self.page_body, anchor="nw")
        self.page_body.bind("<Configure>", self._on_page_body_configure)
        self.page_canvas.bind("<Configure>", self._on_page_canvas_configure)
        self.page_canvas.bind("<Enter>", self._bind_page_mousewheel)
        self.page_canvas.bind("<Leave>", self._unbind_page_mousewheel)

        input_frame = self.create_section_card("Input", parent=self.page_body)
        self.master_label = self.create_picker_with_status(
            button_text="Select master file",
            command=self.controller.select_master_file,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )
        self.folder_label = self.create_picker_with_status(
            button_text="Select update folder",
            command=self.controller.select_update_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=theme.SPACING_SM,
        )

        params_frame = self.create_section_card("Columns", parent=self.page_body)
        self.key_col_var = tk.StringVar(value="2")
        self.match_col_var = tk.StringVar(value="3")
        self.last_update_col_var = tk.StringVar(value="11")
        create_labeled_entry(
            params_frame,
            row=0,
            column=0,
            label_text="Key col:",
            variable=self.key_col_var,
            label_padx=(0, 0),
        )
        create_labeled_entry(
            params_frame,
            row=0,
            column=2,
            label_text="Match col:",
            variable=self.match_col_var,
        )
        create_labeled_entry(
            params_frame,
            row=0,
            column=4,
            label_text="Last update col:",
            variable=self.last_update_col_var,
        )
        self.use_combined_key_var = tk.BooleanVar(value=True)
        if self.show_combined_key_option:
            ttk.Checkbutton(
                params_frame,
                text="Use combined key (key + match)",
                variable=self.use_combined_key_var,
            ).grid(
                row=1,
                column=0,
                columnspan=6,
                sticky="w",
                pady=(theme.SPACING_XXS, 0),
            )
        if self.rule_hint_text:
            ttk.Label(
                params_frame,
                text=self.rule_hint_text,
                style="SurfaceMuted.TLabel",
            ).grid(
                row=2 if self.show_combined_key_option else 1,
                column=0,
                columnspan=6,
                sticky="w",
                pady=(theme.SPACING_XXS, 0),
            )

        priority_frame = self.create_section_card("Processing Order (Top runs first)", parent=self.page_body)
        ttk.Label(
            priority_frame,
            text="Drag files to reorder processing order. Top row is processed first.",
            style="SurfaceMuted.TLabel",
        ).pack(anchor="w", pady=(0, theme.SPACING_XXS))

        list_container = ttk.Frame(priority_frame, style="Surface.TFrame")
        list_container.pack(fill="x", expand=False)

        self.priority_listbox = tk.Listbox(
            list_container,
            height=6,
            activestyle="none",
            selectmode=tk.BROWSE,
            exportselection=False,
            bg=theme.SURFACE_BG,
            fg=theme.TEXT_PRIMARY,
            selectbackground=theme.SECONDARY_HOVER,
            selectforeground=theme.TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
            font=theme.FONT_DEFAULT,
        )
        self.priority_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.priority_listbox.yview)
        list_scrollbar.pack(side="right", fill="y")
        self.priority_listbox.configure(yscrollcommand=list_scrollbar.set)

        self.priority_listbox.bind("<ButtonPress-1>", self._on_drag_start)
        self.priority_listbox.bind("<B1-Motion>", self._on_drag_motion)
        self.priority_listbox.bind("<ButtonRelease-1>", self._on_drag_stop)

        self.priority_count_label = ttk.Label(priority_frame, text="Files: 0", style="SurfaceMuted.TLabel")
        self.priority_count_label.pack(anchor="w", pady=(theme.SPACING_XXS, 0))

        self.create_primary_button(
            text=self.run_button_text,
            command=self.controller.process_files,
            parent=self.page_body,
        )

    def _on_page_body_configure(self, _event=None):
        self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

    def _on_page_canvas_configure(self, event):
        self.page_canvas.itemconfigure(self.page_body_window, width=event.width)

    def _bind_page_mousewheel(self, _event=None):
        self.page_canvas.bind_all("<MouseWheel>", self._on_page_mousewheel)

    def _unbind_page_mousewheel(self, _event=None):
        self.page_canvas.unbind_all("<MouseWheel>")

    def _on_page_mousewheel(self, event):
        delta = event.delta
        if delta == 0:
            return
        self.page_canvas.yview_scroll(int(-1 * (delta / 120)), "units")

    def set_master_file_label(self, file_path):
        self.set_selected_file_label(self.master_label, file_path)

    def set_update_folder_label(self, folder_path):
        self.set_selected_path_label(self.folder_label, folder_path)

    def set_priority_files(self, file_paths: list[str]):
        self.priority_files = list(file_paths)
        self._refresh_priority_list()

    def _refresh_priority_list(self):
        self.priority_listbox.delete(0, tk.END)
        for index, path in enumerate(self.priority_files, start=1):
            file_name = self.basename(path)
            self.priority_listbox.insert(tk.END, f"{index}. {file_name}")
        self.priority_count_label.configure(text=f"Files: {len(self.priority_files)}")

    def _on_drag_start(self, event):
        if not self.priority_files:
            self._drag_index = None
            return
        index = self.priority_listbox.nearest(event.y)
        if index < 0 or index >= len(self.priority_files):
            self._drag_index = None
            return
        self._drag_index = index
        self.priority_listbox.selection_clear(0, tk.END)
        self.priority_listbox.selection_set(index)

    def _on_drag_motion(self, event):
        if self._drag_index is None:
            return
        new_index = self.priority_listbox.nearest(event.y)
        if new_index < 0 or new_index >= len(self.priority_files):
            return
        if new_index == self._drag_index:
            return

        moved = self.priority_files.pop(self._drag_index)
        self.priority_files.insert(new_index, moved)
        self._drag_index = new_index

        self._refresh_priority_list()
        self.priority_listbox.selection_clear(0, tk.END)
        self.priority_listbox.selection_set(new_index)

    def _on_drag_stop(self, _event):
        self._drag_index = None

    def get_config(self):
        if not self.priority_files:
            raise ValidationError("Please select an update folder with at least one Excel file.")
        return MasterUpdateConfig(
            key_col=parse_column_1_based_to_0_based(self.key_col_var.get(), "Key col"),
            match_col=parse_column_1_based_to_0_based(self.match_col_var.get(), "Match col"),
            priority_files=tuple(self.priority_files),
            last_update_col=parse_column_1_based_to_0_based(
                self.last_update_col_var.get(),
                "Last update col",
            ),
            use_combined_key=bool(
                self.use_combined_key_var.get() if hasattr(self, "use_combined_key_var") else True
            ),
        )
