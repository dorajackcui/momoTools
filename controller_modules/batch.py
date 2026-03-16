import os
import webbrowser
from tkinter import filedialog

from core.auto_fill_config import (
    AUTO_FILL_MATCH_RULE_PREFIX,
    AUTO_FILL_SCAN_DEPTH,
    AutoFillConfig,
    AutoFillRule,
    load_auto_fill_config,
    save_auto_fill_config,
)
from core.batch_config import (
    BATCH_SCHEMA_VERSION,
    BatchConfigV1,
    BatchDefaultsReverse,
    BatchDefaultsSingle,
    BatchJobConfig,
    BatchRuntimeOptions,
    MODE_MASTER_TO_TARGET_SINGLE,
    dump_config,
    load_config,
    template_config,
)
from core.batch_runner import BatchRunner, BatchRunSummary
from ui import strings
from ui.validators import ValidationError
from .base import BaseController
from .path_preflight import probe_excel_folder
from .path_state import TerminologyPathStateStore


class BatchController(BaseController):
    def __init__(
        self,
        frame,
        single_processor,
        reverse_processor,
        dialog_service=None,
        state_store=None,
        runner=None,
        task_runner=None,
        auto_fill_config_path=None,
    ):
        super().__init__(frame, dialog_service=dialog_service, task_runner=task_runner)
        self.single_processor = single_processor
        self.reverse_processor = reverse_processor
        self.state_store = state_store or TerminologyPathStateStore()
        shared_log = getattr(single_processor, "log_callback", None) or getattr(
            reverse_processor,
            "log_callback",
            None,
        )
        self.runner = runner or BatchRunner(
            single_processor=single_processor,
            reverse_processor=reverse_processor,
            log_callback=shared_log,
        )
        self.master_file_path = ""
        self.config_file_path = ""
        self.auto_fill_config_path = auto_fill_config_path or TerminologyPathStateStore.default_auto_fill_rules_path()

    def restore_persisted_paths(self):
        state = self.state_store.load()
        persisted_path = str(state.get(TerminologyPathStateStore.STATE_KEY_BATCH_CONFIG_PATH, "")).strip()
        if not persisted_path or not os.path.isfile(persisted_path):
            self.config_file_path = ""
        else:
            self.config_file_path = persisted_path
            if self.frame is not None:
                self._require_frame().set_config_file_label(persisted_path)
        persisted_auto_fill_path = str(state.get(TerminologyPathStateStore.STATE_KEY_AUTO_FILL_CONFIG_PATH, "")).strip()
        if persisted_auto_fill_path:
            self.auto_fill_config_path = persisted_auto_fill_path
        if self.frame is not None:
            self._require_frame().set_auto_fill_config_path(self.auto_fill_config_path)

    def _persist_config_path(self):
        if not self.config_file_path:
            return
        state = self.state_store.load()
        state[TerminologyPathStateStore.STATE_KEY_BATCH_CONFIG_PATH] = self.config_file_path
        self.state_store.save(state)

    def _persist_auto_fill_config_path(self):
        if not self.auto_fill_config_path:
            return
        state = self.state_store.load()
        state[TerminologyPathStateStore.STATE_KEY_AUTO_FILL_CONFIG_PATH] = self.auto_fill_config_path
        self.state_store.save(state)

    def select_auto_fill_config_file(self):
        initial_dir = os.path.dirname(self.auto_fill_config_path) if self.auto_fill_config_path else ""
        initial_file = os.path.basename(self.auto_fill_config_path) if self.auto_fill_config_path else "auto_fill_rules.json"
        file_path = filedialog.asksaveasfilename(
            title="Select auto fill config JSON path",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir or None,
            initialfile=initial_file or "auto_fill_rules.json",
        )
        if not file_path:
            return
        self.auto_fill_config_path = file_path
        self._persist_auto_fill_config_path()
        if self.frame is not None:
            self._require_frame().set_auto_fill_config_path(self.auto_fill_config_path)

    def open_auto_fill_config_file(self):
        try:
            config = load_auto_fill_config(self.auto_fill_config_path)
            save_auto_fill_config(config, self.auto_fill_config_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Open auto fill config failed:\n{exc}")
            return
        self._persist_auto_fill_config_path()
        if self.frame is not None:
            self._require_frame().set_auto_fill_config_path(self.auto_fill_config_path)
        try:
            if hasattr(os, "startfile"):
                os.startfile(self.auto_fill_config_path)  # type: ignore[attr-defined]
            else:
                webbrowser.open(self.auto_fill_config_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Open auto fill config failed:\n{exc}")

    def _load_auto_fill_config_or_notify(self):
        try:
            config = load_auto_fill_config(self.auto_fill_config_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Load auto fill rules failed:\n{exc}")
            return None
        if not config.rules:
            self.dialogs.error(
                strings.ERROR_TITLE,
                (
                    "Auto fill rules are empty.\n"
                    "Click 'Open Config JSON' to configure keywords and columns first.\n"
                    f"Config: {self.auto_fill_config_path}"
                ),
            )
            return None
        return config

    def save_auto_fill_rules(self):
        # Backward compatibility entry; rules are now edited in external JSON.
        self.open_auto_fill_config_file()

    def select_master_file(self):
        file_path = self._ask_excel_file("Select Master file")
        if not file_path:
            return
        self.master_file_path = file_path
        self._require_frame().set_master_file_label(file_path)
        self._notify_master_file_probe(file_path)

    def select_config_file(self):
        initial_dir = ""
        if self.config_file_path:
            initial_dir = os.path.dirname(self.config_file_path)
        file_path = filedialog.askopenfilename(
            title="Select batch config JSON",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir or None,
        )
        if not file_path:
            return
        self.config_file_path = file_path
        self._require_frame().set_config_file_label(file_path)
        self._persist_config_path()

    def load_config_file(self):
        config_path = self._require_frame().get_config_path() or self.config_file_path
        if not config_path:
            self.dialogs.error(strings.ERROR_TITLE, "Please select a batch config JSON first.")
            return
        try:
            config = load_config(config_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Load config failed:\n{exc}")
            return

        self.config_file_path = config_path
        self.master_file_path = config.master_file
        self._require_frame().set_config_file_label(config_path)
        self._require_frame().load_config(config)
        self._maybe_migrate_legacy_auto_fill_rules(config)
        self._persist_config_path()

    def save_config_file(self):
        view_config = self._get_batch_view_or_notify()
        if view_config is None:
            return
        config_path = self._require_frame().get_config_path() or self.config_file_path
        if not config_path:
            config_path = filedialog.asksaveasfilename(
                title="Save batch config JSON",
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("All files", "*.*")],
            )
            if not config_path:
                return

        config = self._build_core_config(view_config)
        try:
            dump_config(config, config_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Save config failed:\n{exc}")
            return

        self.config_file_path = config_path
        self._require_frame().set_config_file_label(config_path)
        self._persist_config_path()
        self.dialogs.info(strings.SUCCESS_TITLE, f"Config saved:\n{config_path}")

    def export_template_file(self):
        mode = self._require_frame().get_mode()
        output_path = filedialog.asksaveasfilename(
            title="Export batch template JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not output_path:
            return
        try:
            config = template_config(mode)
            dump_config(config, output_path)
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Export template failed:\n{exc}")
            return
        self.dialogs.info(strings.SUCCESS_TITLE, f"Template exported:\n{output_path}")

    def _maybe_migrate_legacy_auto_fill_rules(self, config: BatchConfigV1):
        if not config.legacy_auto_fill_rules:
            return
        current = load_auto_fill_config(self.auto_fill_config_path)
        if current.rules:
            return
        migrated = AutoFillConfig(
            rules=tuple(
                AutoFillRule(
                    keyword=rule.keyword,
                    variable_column=rule.variable_column,
                )
                for rule in config.legacy_auto_fill_rules
            ),
            match_rule=AUTO_FILL_MATCH_RULE_PREFIX,
            scan_depth=AUTO_FILL_SCAN_DEPTH,
        )
        try:
            save_auto_fill_config(migrated, self.auto_fill_config_path)
        except Exception:
            return

    def select_job_folder(self, index: int):
        folder_path = self._ask_folder("Select target folder")
        if not folder_path:
            return
        mode = self._require_frame().get_mode()
        probe_result = self._confirm_excel_folder_selection(
            folder_path=folder_path,
            list_files=self._resolve_batch_list_files(mode),
            dialog_title="Confirm batch target files",
            require_writable_sample=self._batch_mode_requires_writable_sample(mode),
            sample_seed_key=self._build_batch_sample_seed(mode, index, folder_path),
        )
        if probe_result is None:
            return
        self._require_frame().set_job_target_folder(index, folder_path)

    @staticmethod
    def _batch_mode_requires_writable_sample(mode: str) -> bool:
        return mode == MODE_MASTER_TO_TARGET_SINGLE

    def _resolve_batch_list_files(self, mode: str):
        if self._batch_mode_requires_writable_sample(mode):
            return self.single_processor.list_target_files
        return self.reverse_processor.list_target_files

    @staticmethod
    def _build_batch_sample_seed(mode: str, index: int, folder_path: str) -> str:
        return f"batch|{mode}|{index}|{folder_path}"

    def _precheck_batch_target_folders(self, config: BatchConfigV1) -> list[str]:
        errors: list[str] = []
        list_files = self._resolve_batch_list_files(config.mode)
        require_writable_sample = self._batch_mode_requires_writable_sample(config.mode)
        for index, job in enumerate(config.jobs, start=1):
            probe_result = probe_excel_folder(
                list_files(job.target_folder),
                require_writable_sample=require_writable_sample,
                sample_seed_key=self._build_batch_sample_seed(
                    config.mode,
                    index - 1,
                    job.target_folder,
                ),
            )
            if not probe_result.file_paths:
                errors.append(
                    f"jobs[{index}] has no Excel files in target folder: {job.target_folder}"
                )
                continue
            if require_writable_sample and probe_result.sample_writable is False:
                errors.append(
                    probe_result.warning_message
                    or f"jobs[{index}] sampled file is not writable: {probe_result.sampled_file}"
                )
        return errors

    def auto_fill_jobs_by_keywords(self):
        # Backward compatibility wrapper for previously wired command hooks.
        self.auto_fill_jobs_from_mapping()

    def auto_fill_jobs_from_mapping(self):
        config = self._load_auto_fill_config_or_notify()
        if config is None:
            return
        rules = config.rules

        parent_folder = self._ask_folder("Select parent folder for auto extract")
        if not parent_folder:
            return

        if not os.path.isdir(parent_folder):
            self.dialogs.error(strings.ERROR_TITLE, f"Parent folder not found:\n{parent_folder}")
            return

        entries = self._discover_target_directories(parent_folder)
        matched_entries, missing_keywords = self._match_entries_by_rules(entries, rules)
        if not matched_entries:
            self.dialogs.warning(
                strings.WARNING_TITLE,
                (
                    "No target folders matched the keywords.\n"
                    f"Parent: {parent_folder}\n"
                    f"Keywords: {', '.join(rule.keyword for rule in rules)}"
                ),
            )
            return

        self._require_frame().replace_jobs_from_auto_fill(matched_entries)
        summary = [
            "Auto extract completed.",
            f"Matched folders: {len(matched_entries)}",
            f"Parent: {parent_folder}",
        ]
        if missing_keywords:
            summary.append(f"Missing keywords: {', '.join(missing_keywords)}")
            self.dialogs.warning(strings.WARNING_TITLE, "\n".join(summary))
            return
        self.dialogs.info(strings.SUCCESS_TITLE, "\n".join(summary))

    @staticmethod
    def _discover_target_directories(parent_folder: str) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = []
        try:
            for entry in os.scandir(parent_folder):
                if not entry.is_dir():
                    continue
                entries.append((entry.name, entry.path))
        except Exception:
            return []

        entries.sort(key=lambda item: item[0].lower())
        return entries

    @staticmethod
    def _match_entries_by_rules(
        entries: list[tuple[str, str]],
        rules: tuple[AutoFillRule, ...],
    ) -> tuple[list[dict[str, object]], list[str]]:
        matched: list[dict[str, object]] = []
        missing_keywords: list[str] = []
        seen: set[str] = set()

        for rule in rules:
            pattern = rule.keyword.strip().lower()
            found = False
            for name, path in entries:
                path_key = path.lower()
                if path_key in seen:
                    continue
                if not name.lower().startswith(pattern):
                    continue
                matched.append(
                    {
                        "target_folder": path,
                        "variable_column": int(rule.variable_column),
                    }
                )
                seen.add(path_key)
                found = True
                break
            if not found:
                missing_keywords.append(rule.keyword)

        return matched, missing_keywords

    def precheck_batch(self):
        view_config = self._get_batch_view_or_notify()
        if view_config is None:
            return
        config = self._build_core_config(view_config)
        if not self._ensure_master_file_ready(config.master_file):
            return
        errors = self._precheck_batch_target_folders(config)
        errors.extend(self.runner.precheck(config))
        if errors:
            self.dialogs.error(strings.ERROR_TITLE, "Batch precheck failed:\n" + "\n".join(errors))
            return
        self.dialogs.info(
            strings.SUCCESS_TITLE,
            f"Batch precheck passed.\nMode: {config.mode}\nJobs: {len(config.jobs)}",
        )

    def process_files(self):
        view_config = self._get_batch_view_or_notify()
        if view_config is None:
            return
        config = self._build_core_config(view_config)
        if not self._ensure_master_file_ready(config.master_file):
            return
        errors = self._precheck_batch_target_folders(config)
        errors.extend(self.runner.precheck(config))
        if errors:
            self.dialogs.error(strings.ERROR_TITLE, "Batch precheck failed:\n" + "\n".join(errors))
            return

        task_name = f"Batch:{config.mode}"

        def run():
            return self.runner.run(config)

        def on_success(summary: BatchRunSummary):
            self.dialogs.info(strings.SUCCESS_TITLE, self._summary_message(summary))

        self._run_action_or_notify(run, on_success=on_success, task_name=task_name)

    def _get_batch_view_or_notify(self):
        try:
            config = self._require_frame().get_config()
            self.master_file_path = config.master_file
            if config.config_path:
                self.config_file_path = config.config_path
                self._persist_config_path()
            return config
        except ValidationError as exc:
            self.dialogs.error(strings.ERROR_TITLE, f"Batch config error: {exc}")
        except Exception as exc:
            self.dialogs.error(strings.ERROR_TITLE, str(exc))
        return None

    @staticmethod
    def _build_core_config(view_config) -> BatchConfigV1:
        jobs: list[BatchJobConfig] = []
        for index, row in enumerate(view_config.jobs, start=1):
            jobs.append(
                BatchJobConfig(
                    name=str(row.name).strip() or f"job-{index}",
                    target_folder=str(row.target_folder).strip(),
                    variable_column=int(row.variable_column),
                )
            )

        if view_config.mode == "master_to_target_single":
            defaults = BatchDefaultsSingle(
                target_key_col=int(view_config.defaults_single.target_key_col),
                target_match_col=int(view_config.defaults_single.target_match_col),
                target_update_start_col=int(view_config.defaults_single.target_update_start_col),
                master_key_col=int(view_config.defaults_single.master_key_col),
                master_match_col=int(view_config.defaults_single.master_match_col),
                fill_blank_only=bool(view_config.defaults_single.fill_blank_only),
                post_process_enabled=bool(view_config.defaults_single.post_process_enabled),
                allow_blank_write=bool(view_config.defaults_single.allow_blank_write),
            )
        else:
            defaults = BatchDefaultsReverse(
                target_key_col=int(view_config.defaults_reverse.target_key_col),
                target_match_col=int(view_config.defaults_reverse.target_match_col),
                target_content_col=int(view_config.defaults_reverse.target_content_col),
                master_key_col=int(view_config.defaults_reverse.master_key_col),
                master_match_col=int(view_config.defaults_reverse.master_match_col),
                fill_blank_only=bool(view_config.defaults_reverse.fill_blank_only),
                allow_blank_write=bool(view_config.defaults_reverse.allow_blank_write),
            )

        return BatchConfigV1(
            schema_version=BATCH_SCHEMA_VERSION,
            mode=view_config.mode,
            master_file=str(view_config.master_file).strip(),
            defaults=defaults,
            jobs=tuple(jobs),
            runtime=BatchRuntimeOptions(
                continue_on_error=bool(view_config.runtime.continue_on_error),
            ),
        )

    @staticmethod
    def _summary_message(summary: BatchRunSummary) -> str:
        lines = [
            "Batch finished.",
            f"Mode: {summary.mode}",
            f"Jobs: {summary.jobs_succeeded}/{summary.jobs_total} succeeded, {summary.jobs_failed} failed",
            f"Updated total: {summary.updated_total}",
        ]
        if summary.backup_path:
            lines.append(f"Backup: {summary.backup_path}")
        if summary.stopped_early:
            lines.append("Stopped early due to continue_on_error = false.")
        if summary.jobs_failed:
            lines.append("")
            lines.append("Failed jobs:")
            for result in summary.results:
                if result.status != "failed":
                    continue
                lines.append(f"- #{result.job_index} {result.job_name}: {result.error}")
        return "\n".join(lines)

