import tkinter as tk
from tkinter import ttk

from core.batch_config import (
    MODE_MASTER_TO_TARGET_SINGLE,
    MODE_TARGET_TO_MASTER_REVERSE,
)
from ui import strings, theme
from ui.validators import ValidationError, parse_positive_int
from ui.view_models import (
    BatchDefaultsReverse,
    BatchDefaultsSingle,
    BatchJobRow,
    BatchRuntimeOptions,
    BatchViewConfig,
)
from ui.views.base import BaseFrame
from ui.widgets.factory import create_action_button, create_labeled_entry


class BatchFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.master_file_path = ""
        self.config_path = ""
        self.job_rows: list[dict[str, object]] = []
        self._json_advanced_visible = False
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

        input_frame = self.create_section_card("Batch Inputs", parent=self.page_body)
        self.master_label = self.create_picker_with_status(
            button_text="Select master file",
            command=self.controller.select_master_file,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=input_frame,
            button_pady=(0, theme.SPACING_XXS),
        )

        self.json_toggle_button = create_action_button(
            input_frame,
            text="Show JSON Config (Advanced)",
            command=self.toggle_json_config_section,
            button_style="Secondary.TButton",
            pady=(theme.SPACING_XS, 0),
        )

        self.json_advanced_frame = ttk.Frame(input_frame, style="Surface.TFrame")
        self.config_label = self.create_picker_with_status(
            button_text="Select batch config JSON",
            command=self.controller.select_config_file,
            default_text=strings.DEFAULT_FILE_TEXT,
            parent=self.json_advanced_frame,
            button_pady=(0, theme.SPACING_XXS),
        )
        input_action_row = ttk.Frame(self.json_advanced_frame, style="Surface.TFrame")
        input_action_row.pack(fill="x", pady=(theme.SPACING_XS, 0))
        create_action_button(
            input_action_row,
            text="Load JSON",
            command=self.controller.load_config_file,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            pady=0,
        )
        create_action_button(
            input_action_row,
            text="Save JSON",
            command=self.controller.save_config_file,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            pady=0,
        )
        create_action_button(
            input_action_row,
            text="Export Template",
            command=self.controller.export_template_file,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            pady=0,
        )

        mode_frame = self.create_section_card("Task Mode", parent=self.page_body)
        self.mode_var = tk.StringVar(value=MODE_MASTER_TO_TARGET_SINGLE)
        ttk.Label(mode_frame, text="Mode:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, theme.SPACING_XS),
            pady=(theme.SPACING_XXS, theme.SPACING_XXS),
        )
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            state="readonly",
            values=(MODE_MASTER_TO_TARGET_SINGLE, MODE_TARGET_TO_MASTER_REVERSE),
            width=32,
        )
        self.mode_combo.grid(
            row=0,
            column=1,
            sticky="w",
            pady=(theme.SPACING_XXS, theme.SPACING_XXS),
        )
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_changed)

        defaults_frame = self.create_section_card("Defaults", parent=self.page_body)
        self.target_key_col_var = tk.StringVar(value="1")
        self.target_match_col_var = tk.StringVar(value="2")
        self.target_update_start_col_var = tk.StringVar(value="3")
        self.target_content_col_var = tk.StringVar(value="3")
        self.master_key_col_var = tk.StringVar(value="2")
        self.master_match_col_var = tk.StringVar(value="3")
        create_labeled_entry(
            defaults_frame,
            row=0,
            column=0,
            label_text="Target key col:",
            variable=self.target_key_col_var,
            label_padx=(0, 0),
        )
        create_labeled_entry(
            defaults_frame,
            row=0,
            column=2,
            label_text="Target match col:",
            variable=self.target_match_col_var,
        )
        self.target_mode_col_label = ttk.Label(defaults_frame, text="Target update start col:")
        self.target_mode_col_label.grid(
            row=0,
            column=4,
            sticky="w",
            padx=(theme.SPACING_XS, 0),
            pady=(theme.SPACING_XXS, theme.SPACING_XXS),
        )
        self.target_mode_col_entry = ttk.Entry(
            defaults_frame,
            textvariable=self.target_update_start_col_var,
            width=5,
        )
        self.target_mode_col_entry.grid(
            row=0,
            column=5,
            pady=(theme.SPACING_XXS, theme.SPACING_XXS),
        )
        create_labeled_entry(
            defaults_frame,
            row=1,
            column=0,
            label_text="Master key col:",
            variable=self.master_key_col_var,
            label_padx=(0, 0),
        )
        create_labeled_entry(
            defaults_frame,
            row=1,
            column=2,
            label_text="Master match col:",
            variable=self.master_match_col_var,
        )

        toggle_frame = ttk.Frame(defaults_frame, style="Surface.TFrame")
        toggle_frame.grid(
            row=2,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(theme.SPACING_XS, 0),
        )
        self.fill_blank_var = tk.BooleanVar(value=False)
        self.create_toggle(
            text="Fill blank only",
            variable=self.fill_blank_var,
            parent=toggle_frame,
            pady=(0, theme.SPACING_XXS),
        )
        self.post_process_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="Enable post-process (single mode only)",
            variable=self.post_process_var,
            parent=toggle_frame,
            pady=(0, 0),
        )

        auto_fill_frame = self.create_section_card("Autofill config", parent=self.page_body)
        auto_help_row = ttk.Frame(auto_fill_frame, style="Surface.TFrame")
        auto_help_row.pack(fill="x", pady=(0, theme.SPACING_XXS))
        ttk.Label(auto_help_row, text="Rules source: config JSON", style="SurfaceMuted.TLabel").pack(
            side="left",
            padx=(0, theme.SPACING_XS),
        )
        ttk.Label(auto_help_row, text="Match: prefix, depth: 1-level", style="SurfaceMuted.TLabel").pack(side="left")
        self.auto_fill_config_path_label = ttk.Label(auto_fill_frame, text="", style="SurfaceMuted.TLabel")
        self.auto_fill_config_path_label.pack(fill="x", pady=(0, theme.SPACING_XXS))

        auto_actions = ttk.Frame(auto_fill_frame, style="Surface.TFrame")
        auto_actions.pack(fill="x")
        create_action_button(
            auto_actions,
            text="Select Config Path",
            command=self.controller.select_auto_fill_config_file,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            pady=0,
        )
        create_action_button(
            auto_actions,
            text="Open Config JSON",
            command=self.controller.open_auto_fill_config_file,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            pady=0,
        )
        create_action_button(
            auto_actions,
            text="Auto Fill From Parent",
            command=self.controller.auto_fill_jobs_from_mapping,
            button_style="Secondary.TButton",
            side="left",
            pady=0,
        )

        jobs_frame = self.create_section_card("Jobs", parent=self.page_body)
        jobs_header = ttk.Frame(jobs_frame, style="Surface.TFrame")
        jobs_header.pack(fill="x")
        ttk.Label(jobs_header, text="Target folder", style="SurfaceMuted.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, theme.SPACING_XS)
        )
        self.job_variable_header = ttk.Label(
            jobs_header,
            text="Master content start col",
            style="SurfaceMuted.TLabel",
        )
        self.job_variable_header.grid(
            row=0, column=1, sticky="w", padx=(0, theme.SPACING_XS)
        )
        ttk.Label(jobs_header, text="Action", style="SurfaceMuted.TLabel").grid(
            row=0, column=2, sticky="w"
        )

        self.jobs_canvas = tk.Canvas(
            jobs_frame,
            bg=theme.SURFACE_BG,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
            height=170,
        )
        self.jobs_canvas.pack(side="left", fill="both", expand=True, pady=(theme.SPACING_XXS, 0))
        jobs_scrollbar = ttk.Scrollbar(jobs_frame, orient="vertical", command=self.jobs_canvas.yview)
        jobs_scrollbar.pack(side="right", fill="y", pady=(theme.SPACING_XXS, 0))
        self.jobs_canvas.configure(yscrollcommand=jobs_scrollbar.set)

        self.jobs_inner = ttk.Frame(self.jobs_canvas, style="Surface.TFrame")
        self.jobs_inner_window = self.jobs_canvas.create_window((0, 0), window=self.jobs_inner, anchor="nw")
        self.jobs_inner.bind("<Configure>", self._on_jobs_inner_configure)
        self.jobs_canvas.bind("<Configure>", self._on_jobs_canvas_configure)

        job_action_row = ttk.Frame(jobs_frame, style="Surface.TFrame")
        job_action_row.pack(fill="x", pady=(theme.SPACING_XS, 0))
        create_action_button(
            job_action_row,
            text="Add Job",
            command=self.add_job_row,
            button_style="Secondary.TButton",
            side="left",
            pady=0,
        )

        run_frame = self.create_section_card("Run", parent=self.page_body)
        self.continue_on_error_var = tk.BooleanVar(value=True)
        self.create_toggle(
            text="Continue on error",
            variable=self.continue_on_error_var,
            parent=run_frame,
            pady=(0, theme.SPACING_XS),
        )

        run_action_row = ttk.Frame(run_frame, style="Surface.TFrame")
        run_action_row.pack(fill="x")
        create_action_button(
            run_action_row,
            text="Precheck",
            command=self.controller.precheck_batch,
            button_style="Secondary.TButton",
            side="left",
            padx=theme.SPACING_XS,
            processing_action=True,
            pady=(0, 0),
        )
        create_action_button(
            run_action_row,
            text="Run Batch",
            command=self.controller.process_files,
            button_style="Primary.TButton",
            side="left",
            processing_action=True,
            pady=(0, 0),
        )

        self.add_job_row()
        self._apply_mode_ui()
        self._set_json_config_visible(False)

    def toggle_json_config_section(self):
        self._set_json_config_visible(not self._json_advanced_visible)

    def _set_json_config_visible(self, visible: bool):
        self._json_advanced_visible = bool(visible)
        if self._json_advanced_visible:
            self.json_advanced_frame.pack(fill="x", pady=(theme.SPACING_XS, 0))
            self.json_toggle_button.config(text="Hide JSON Config (Advanced)")
        else:
            self.json_advanced_frame.pack_forget()
            self.json_toggle_button.config(text="Show JSON Config (Advanced)")

    def _on_mode_changed(self, _event=None):
        self._apply_mode_ui()

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

    def _apply_mode_ui(self):
        mode = self.mode_var.get()
        if mode == MODE_TARGET_TO_MASTER_REVERSE:
            self.target_mode_col_label.config(text="Target content col:")
            self.target_mode_col_entry.config(textvariable=self.target_content_col_var)
            self.job_variable_header.config(text="Master update col")
        else:
            self.target_mode_col_label.config(text="Target update start col:")
            self.target_mode_col_entry.config(textvariable=self.target_update_start_col_var)
            self.job_variable_header.config(text="Master content start col")

    def _on_jobs_inner_configure(self, _event=None):
        self.jobs_canvas.configure(scrollregion=self.jobs_canvas.bbox("all"))

    def _on_jobs_canvas_configure(self, event):
        self.jobs_canvas.itemconfigure(self.jobs_inner_window, width=event.width)

    def add_job_row(self, row_data: BatchJobRow | None = None):
        self.job_rows.append(
            {
                "target_folder_var": tk.StringVar(value=row_data.target_folder if row_data else ""),
                "variable_column_var": tk.StringVar(value=str(row_data.variable_column if row_data else 4)),
            }
        )
        self._render_job_rows()

    def remove_job_row(self, index: int):
        if len(self.job_rows) <= 1:
            return
        if 0 <= index < len(self.job_rows):
            self.job_rows.pop(index)
            self._render_job_rows()

    def _render_job_rows(self):
        for child in self.jobs_inner.winfo_children():
            child.destroy()

        for index, row in enumerate(self.job_rows):
            line = ttk.Frame(self.jobs_inner, style="Surface.TFrame")
            line.pack(fill="x", pady=(0, theme.SPACING_XXS))

            target_folder_var = row["target_folder_var"]
            variable_column_var = row["variable_column_var"]

            ttk.Entry(line, textvariable=target_folder_var, width=34).grid(
                row=0,
                column=0,
                sticky="ew",
                padx=(0, theme.SPACING_XS),
            )
            ttk.Entry(line, textvariable=variable_column_var, width=7).grid(
                row=0,
                column=1,
                sticky="w",
                padx=(0, theme.SPACING_XS),
            )

            action_row = ttk.Frame(line, style="Surface.TFrame")
            action_row.grid(row=0, column=2, sticky="w")
            create_action_button(
                action_row,
                text="Browse",
                command=lambda i=index: self.controller.select_job_folder(i),
                button_style="Secondary.TButton",
                side="left",
                pady=0,
                padx=theme.SPACING_XXS,
            )
            create_action_button(
                action_row,
                text="Delete",
                command=lambda i=index: self.remove_job_row(i),
                button_style="Danger.TButton",
                side="left",
                pady=0,
            )

            line.columnconfigure(0, weight=1)

        self._on_jobs_inner_configure()

    def set_master_file_label(self, file_path):
        self.master_file_path = file_path or ""
        self.set_selected_file_label(self.master_label, file_path)

    def set_config_file_label(self, file_path):
        self.config_path = file_path or ""
        self.set_selected_file_label(self.config_label, file_path)

    def set_auto_fill_config_path(self, file_path: str):
        normalized = str(file_path or "").strip()
        if not normalized:
            self.auto_fill_config_path_label.config(text="Rules config: (not set)")
            return
        self.auto_fill_config_path_label.config(text=f"Rules config: {normalized}")

    def get_config_path(self):
        return self.config_path

    def get_mode(self):
        return str(self.mode_var.get()).strip()

    def set_job_target_folder(self, index: int, folder_path: str):
        if index < 0 or index >= len(self.job_rows):
            return
        row = self.job_rows[index]
        folder_var = row["target_folder_var"]
        folder_var.set(folder_path)

    def replace_jobs_from_auto_fill(self, entries: list[dict[str, object]]):
        self.job_rows = []
        for item in entries:
            target_folder = str(item.get("target_folder", "")).strip()
            variable_column = item.get("variable_column", 1)
            try:
                parsed_col = int(variable_column)
            except Exception:
                parsed_col = 1
            self.job_rows.append(
                {
                    "target_folder_var": tk.StringVar(value=target_folder),
                    "variable_column_var": tk.StringVar(value=str(parsed_col)),
                }
            )
        if not self.job_rows:
            self.add_job_row()
            return
        self._render_job_rows()

    def load_config(self, config):
        self.mode_var.set(config.mode)
        self.set_master_file_label(config.master_file)
        self.continue_on_error_var.set(config.runtime.continue_on_error)

        if config.mode == MODE_MASTER_TO_TARGET_SINGLE:
            defaults = config.defaults
            self.target_key_col_var.set(str(defaults.target_key_col))
            self.target_match_col_var.set(str(defaults.target_match_col))
            self.target_update_start_col_var.set(str(defaults.target_update_start_col))
            self.master_key_col_var.set(str(defaults.master_key_col))
            self.master_match_col_var.set(str(defaults.master_match_col))
            self.fill_blank_var.set(bool(defaults.fill_blank_only))
            self.post_process_var.set(bool(defaults.post_process_enabled))
        else:
            defaults = config.defaults
            self.target_key_col_var.set(str(defaults.target_key_col))
            self.target_match_col_var.set(str(defaults.target_match_col))
            self.target_content_col_var.set(str(defaults.target_content_col))
            self.master_key_col_var.set(str(defaults.master_key_col))
            self.master_match_col_var.set(str(defaults.master_match_col))
            self.fill_blank_var.set(bool(defaults.fill_blank_only))

        self.job_rows = []
        for row in config.jobs:
            self.add_job_row(
                BatchJobRow(
                    name=row.name,
                    target_folder=row.target_folder,
                    variable_column=row.variable_column,
                )
            )
        if not config.jobs:
            self.add_job_row()

        self._apply_mode_ui()

    def get_config(self):
        mode = str(self.mode_var.get()).strip()
        errors: list[str] = []
        if mode not in {MODE_MASTER_TO_TARGET_SINGLE, MODE_TARGET_TO_MASTER_REVERSE}:
            errors.append("Invalid batch mode.")

        master_file = str(self.master_file_path).strip()
        if not master_file:
            errors.append("Master file is required.")

        target_key_col = self._parse_positive_int_or_default(
            self.target_key_col_var.get(),
            "Target key col",
            errors,
        )
        target_match_col = self._parse_positive_int_or_default(
            self.target_match_col_var.get(),
            "Target match col",
            errors,
        )
        target_update_start_col = self._parse_positive_int_or_default(
            self.target_update_start_col_var.get(),
            "Target update start col",
            errors,
        )
        target_content_col = self._parse_positive_int_or_default(
            self.target_content_col_var.get(),
            "Target content col",
            errors,
        )
        master_key_col = self._parse_positive_int_or_default(
            self.master_key_col_var.get(),
            "Master key col",
            errors,
        )
        master_match_col = self._parse_positive_int_or_default(
            self.master_match_col_var.get(),
            "Master match col",
            errors,
        )

        jobs: list[BatchJobRow] = []
        if not self.job_rows:
            errors.append("At least one job is required.")
        for index, row in enumerate(self.job_rows, start=1):
            target_folder = str(row["target_folder_var"].get()).strip()
            if not target_folder:
                errors.append(f"Job #{index} target folder is required.")
            variable_column = self._parse_positive_int_or_default(
                row["variable_column_var"].get(),
                f"Job #{index} variable column",
                errors,
            )
            jobs.append(
                BatchJobRow(
                    name="",
                    target_folder=target_folder,
                    variable_column=variable_column,
                )
            )

        if errors:
            raise ValidationError("\n".join(errors))

        return BatchViewConfig(
            mode=mode,
            master_file=master_file,
            config_path=self.config_path,
            defaults_single=BatchDefaultsSingle(
                target_key_col=target_key_col,
                target_match_col=target_match_col,
                target_update_start_col=target_update_start_col,
                master_key_col=master_key_col,
                master_match_col=master_match_col,
                fill_blank_only=bool(self.fill_blank_var.get()),
                post_process_enabled=bool(self.post_process_var.get()),
            ),
            defaults_reverse=BatchDefaultsReverse(
                target_key_col=target_key_col,
                target_match_col=target_match_col,
                target_content_col=target_content_col,
                master_key_col=master_key_col,
                master_match_col=master_match_col,
                fill_blank_only=bool(self.fill_blank_var.get()),
            ),
            jobs=tuple(jobs),
            runtime=BatchRuntimeOptions(
                continue_on_error=bool(self.continue_on_error_var.get()),
            ),
        )

    @staticmethod
    def _parse_positive_int_or_default(raw_value, field_name: str, errors: list[str], default: int = 1) -> int:
        try:
            return parse_positive_int(raw_value, field_name)
        except ValidationError as exc:
            errors.append(str(exc))
            return default
