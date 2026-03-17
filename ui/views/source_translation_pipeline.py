import tkinter as tk
from tkinter import ttk

from ui import strings, theme
from ui.validators import ValidationError, parse_column_1_based_to_0_based
from ui.view_models import SourceTranslationPipelineConfig
from ui.views.base import BaseFrame
from ui.widgets.factory import create_labeled_entry


class SourceTranslationPipelineFrame(BaseFrame):
    run_button_text = "Run Source+Translation"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.source_priority_files: list[str] = []
        self.translation_priority_files: list[str] = []
        self._drag_indexes = {"source": None, "translation": None}
        self._priority_listboxes = {}
        self._priority_count_labels = {}
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
        self.source_folder_label = self.create_picker_with_status(
            button_text="Select Source Text update folder",
            command=self.controller.select_source_update_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
            button_pady=theme.SPACING_SM,
        )
        self.translation_folder_label = self.create_picker_with_status(
            button_text="Select Translation update folder",
            command=self.controller.select_translation_update_folder,
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
        ttk.Label(
            params_frame,
            text="Pipeline order is fixed: Source Text first, Translation second.",
            style="SurfaceMuted.TLabel",
        ).grid(
            row=1,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(theme.SPACING_XXS, 0),
        )

        self._create_priority_section(
            title="Source Text Order (Top runs first)",
            description="Drag files to reorder Source Text processing order.",
            stage_key="source",
        )
        self._create_priority_section(
            title="Translation Order (Top runs first)",
            description="Drag files to reorder Translation processing order.",
            stage_key="translation",
        )

        self.create_primary_button(
            text=self.run_button_text,
            command=self.controller.process_files,
            parent=self.page_body,
        )

    def _create_priority_section(self, *, title: str, description: str, stage_key: str):
        priority_frame = self.create_section_card(title, parent=self.page_body)
        ttk.Label(
            priority_frame,
            text=description,
            style="SurfaceMuted.TLabel",
        ).pack(anchor="w", pady=(0, theme.SPACING_XXS))

        list_container = ttk.Frame(priority_frame, style="Surface.TFrame")
        list_container.pack(fill="x", expand=False)

        listbox = tk.Listbox(
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
        listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=listbox.yview)
        list_scrollbar.pack(side="right", fill="y")
        listbox.configure(yscrollcommand=list_scrollbar.set)

        listbox.bind("<ButtonPress-1>", lambda event, stage=stage_key: self._on_drag_start(stage, event))
        listbox.bind("<B1-Motion>", lambda event, stage=stage_key: self._on_drag_motion(stage, event))
        listbox.bind("<ButtonRelease-1>", lambda event, stage=stage_key: self._on_drag_stop(stage, event))

        count_label = ttk.Label(priority_frame, text="Files: 0", style="SurfaceMuted.TLabel")
        count_label.pack(anchor="w", pady=(theme.SPACING_XXS, 0))

        self._priority_listboxes[stage_key] = listbox
        self._priority_count_labels[stage_key] = count_label

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

    def set_source_update_folder_label(self, folder_path):
        self.set_selected_path_label(self.source_folder_label, folder_path)

    def set_translation_update_folder_label(self, folder_path):
        self.set_selected_path_label(self.translation_folder_label, folder_path)

    def set_source_priority_files(self, file_paths: list[str]):
        self.source_priority_files = list(file_paths)
        self._refresh_priority_list("source")

    def set_translation_priority_files(self, file_paths: list[str]):
        self.translation_priority_files = list(file_paths)
        self._refresh_priority_list("translation")

    def _get_priority_files(self, stage_key: str) -> list[str]:
        if stage_key == "source":
            return self.source_priority_files
        return self.translation_priority_files

    def _refresh_priority_list(self, stage_key: str):
        priority_files = self._get_priority_files(stage_key)
        listbox = self._priority_listboxes[stage_key]
        listbox.delete(0, tk.END)
        for index, path in enumerate(priority_files, start=1):
            listbox.insert(tk.END, f"{index}. {self.basename(path)}")
        self._priority_count_labels[stage_key].configure(text=f"Files: {len(priority_files)}")

    def _on_drag_start(self, stage_key: str, event):
        priority_files = self._get_priority_files(stage_key)
        if not priority_files:
            self._drag_indexes[stage_key] = None
            return
        listbox = self._priority_listboxes[stage_key]
        index = listbox.nearest(event.y)
        if index < 0 or index >= len(priority_files):
            self._drag_indexes[stage_key] = None
            return
        self._drag_indexes[stage_key] = index
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(index)

    def _on_drag_motion(self, stage_key: str, event):
        current_index = self._drag_indexes[stage_key]
        if current_index is None:
            return
        priority_files = self._get_priority_files(stage_key)
        listbox = self._priority_listboxes[stage_key]
        new_index = listbox.nearest(event.y)
        if new_index < 0 or new_index >= len(priority_files) or new_index == current_index:
            return

        moved = priority_files.pop(current_index)
        priority_files.insert(new_index, moved)
        self._drag_indexes[stage_key] = new_index
        self._refresh_priority_list(stage_key)
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(new_index)

    def _on_drag_stop(self, stage_key: str, _event):
        self._drag_indexes[stage_key] = None

    def get_config(self):
        if not self.source_priority_files:
            raise ValidationError("Please select a Source Text update folder with at least one Excel file.")
        if not self.translation_priority_files:
            raise ValidationError("Please select a Translation update folder with at least one Excel file.")
        return SourceTranslationPipelineConfig(
            key_col=parse_column_1_based_to_0_based(self.key_col_var.get(), "Key col"),
            match_col=parse_column_1_based_to_0_based(self.match_col_var.get(), "Match col"),
            source_priority_files=tuple(self.source_priority_files),
            translation_priority_files=tuple(self.translation_priority_files),
            last_update_col=parse_column_1_based_to_0_based(
                self.last_update_col_var.get(),
                "Last update col",
            ),
        )
