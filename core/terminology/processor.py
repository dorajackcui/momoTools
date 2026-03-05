import os
import time

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats

from .config import ExtractorConfigLoader
from .exporter import TerminologyExcelExporter
from .extractors import BaseExtractor, RecordRuleExtractor, TagSpanExtractor
from .pipeline_aggregate import aggregate_terminology
from .pipeline_discovery import discover_and_filter_excel_files
from .pipeline_extract import extract_file_candidates
from .types import Candidate, CompoundSplitRule, RecordRule, TagSpanRule


class TerminologyProcessor:
    def __init__(self, log_callback=None):
        self.input_folder = ""
        self.rule_config_path = ""
        self.output_file = ""
        self.log_callback = log_callback or (lambda msg: None)
        self.io_contract = ModeIOContract(mode_name="terminology_extractor", skip_header=True)
        self.stats = ProcessingStats()
        self.event_logger = EventLogger(self.log_callback, self.io_contract.mode_name)
        self._config_loader = ExtractorConfigLoader()
        self._exporter = TerminologyExcelExporter()

    def set_input_folder(self, folder_path: str) -> None:
        self.input_folder = folder_path

    def set_rule_config(self, config_path: str) -> None:
        self.rule_config_path = config_path

    def set_output_file(self, output_file: str) -> None:
        self.output_file = output_file

    def process_files(self) -> dict[str, int]:
        total_started = time.perf_counter()
        self._validate_required_paths()
        self.stats = ProcessingStats()

        config_started = time.perf_counter()
        config = self._config_loader.load(self.rule_config_path)
        config_ms = _elapsed_ms(config_started)

        versions_scope = ",".join(config.versions) if config.versions else "ALL"
        files_scope = ",".join(config.files) if config.files else "ALL"
        self.log(
            "Loaded terminology config: "
            f"path={self.rule_config_path}, "
            f"versions={versions_scope}, "
            f"files={files_scope}"
        )

        extractors = self._build_extractors(config.extractors)

        discovery_started = time.perf_counter()
        discovered_paths, file_paths = discover_and_filter_excel_files(
            input_folder=self.input_folder,
            extensions=self.io_contract.extensions,
            configured_files=config.files,
        )
        discovery_ms = _elapsed_ms(discovery_started)

        self.stats.files_total = len(file_paths)
        self.log(f"Found {len(discovered_paths)} Excel files, selected {len(file_paths)} by config.files")

        extract_started = time.perf_counter()
        all_candidates: list[Candidate] = []
        candidate_sequence = 0
        rows_scanned = 0
        rows_skipped_by_version = 0

        for file_path in file_paths:
            try:
                extract_result = extract_file_candidates(file_path, extractors, config.versions)
            except Exception as exc:
                self._log_error(
                    code="E_TERMINOLOGY_FILE",
                    message="Failed to process file for terminology extraction",
                    file_path=file_path,
                    exc=exc,
                )
                self.stats.files_failed += 1
                continue

            self.stats.files_succeeded += 1
            rows_scanned += extract_result.rows_scanned
            rows_skipped_by_version += extract_result.rows_skipped_by_version

            for candidate in extract_result.candidates:
                candidate_sequence += 1
                candidate.candidate_id = f"C{candidate_sequence:08d}"
            all_candidates.extend(extract_result.candidates)

        self.stats.rows_scanned = rows_scanned
        extract_ms = _elapsed_ms(extract_started)

        aggregate_started = time.perf_counter()
        aggregate_result = aggregate_terminology(candidates=all_candidates, config=config)
        aggregate_ms = _elapsed_ms(aggregate_started)

        export_started = time.perf_counter()
        self._exporter.export(
            output_path=self.output_file,
            terms_summary_rows=aggregate_result.terms_summary_rows,
            relations_summary_rows=aggregate_result.relations_summary_rows,
            review_items=aggregate_result.review_items,
            occurrences=aggregate_result.occurrences,
        )
        export_ms = _elapsed_ms(export_started)

        result = {
            "files_total": self.stats.files_total,
            "files_succeeded": self.stats.files_succeeded,
            "files_failed": self.stats.files_failed,
            "candidates_count": len(all_candidates),
            "terms_count": len(aggregate_result.terms),
            "relations_count": len(aggregate_result.relations_summary_rows),
            "review_count": len(aggregate_result.review_items),
        }

        total_ms = _elapsed_ms(total_started)
        self.log(
            "Terminology stage stats: "
            f"files_discovered={len(discovered_paths)}, "
            f"files_selected={len(file_paths)}, "
            f"rows_scanned={rows_scanned}, "
            f"rows_skipped_by_version={rows_skipped_by_version}, "
            f"candidates={len(all_candidates)}, "
            f"normalized={aggregate_result.normalized_count}, "
            f"body_terms={aggregate_result.body_terms_count}, "
            f"suffix_terms={aggregate_result.suffix_terms_count}, "
            f"relations={result['relations_count']}, "
            f"review={result['review_count']}, "
            "timings_ms="
            f"config:{config_ms},"
            f"discovery:{discovery_ms},"
            f"extract:{extract_ms},"
            f"aggregate:{aggregate_ms},"
            f"export:{export_ms},"
            f"total:{total_ms}"
        )
        self.log(
            "Terminology extraction complete: "
            f"files={result['files_succeeded']}/{result['files_total']}, "
            f"candidates={result['candidates_count']}, "
            f"terms={result['terms_count']}, "
            f"relations={result['relations_count']}, "
            f"review={result['review_count']}"
        )
        return result

    def log(self, message: str) -> None:
        self.log_callback(message)

    def _validate_required_paths(self) -> None:
        if not self.input_folder:
            raise ValueError("Input folder is required")
        if not self.rule_config_path:
            raise ValueError("Rule config file is required")
        if not self.output_file:
            raise ValueError("Output file is required")
        if not os.path.isdir(self.input_folder):
            raise ValueError(f"Input folder not found: {self.input_folder}")
        if not os.path.isfile(self.rule_config_path):
            raise ValueError(f"Rule config not found: {self.rule_config_path}")

    def _build_extractors(self, rules: tuple[RecordRule | TagSpanRule | CompoundSplitRule, ...]) -> list[BaseExtractor]:
        extractors: list[BaseExtractor] = []
        for rule in rules:
            if isinstance(rule, RecordRule):
                extractors.append(RecordRuleExtractor(rule))
            elif isinstance(rule, TagSpanRule):
                extractors.append(TagSpanExtractor(rule))
            elif isinstance(rule, CompoundSplitRule):
                # Compound split is now handled in post-cleaning relation stage.
                continue
            else:
                raise ValueError(f"Unsupported rule type: {type(rule)}")
        return extractors

    def _log_error(self, code: str, message: str, file_path: str = "", exc: Exception | None = None) -> None:
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            exception=exc,
        )
        self.event_logger.error(self.stats, event)


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
