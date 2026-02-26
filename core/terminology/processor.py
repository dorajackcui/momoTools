import os
from typing import Any

from core.kernel import ErrorEvent, EventLogger, ModeIOContract, ProcessingStats, iter_excel_files, open_workbook, safe_to_str

from .config import ExtractorConfigLoader
from .dedup import build_term_aggregates, build_terms_and_occurrences
from .exporter import TerminologyExcelExporter
from .extractors import BaseExtractor, ExtractContext, RecordRuleExtractor, TagSpanExtractor
from .normalize import normalize_candidates
from .relations import build_relation_summary, build_relations, build_review_items
from .types import Candidate, CompoundSplitRule, RecordRule, TagSpanRule, TermEntry, TermSummaryRow


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
        self._validate_required_paths()
        self.stats = ProcessingStats()

        config = self._config_loader.load(self.rule_config_path)
        extractors = self._build_extractors(config.extractors)

        discovered_paths = iter_excel_files(
            self.input_folder,
            extensions=self.io_contract.extensions,
            include_temp_files=False,
            case_sensitive=False,
        )
        file_paths = self._filter_file_paths(discovered_paths, config.files)
        self.stats.files_total = len(file_paths)
        self.log(f"Found {len(discovered_paths)} Excel files, selected {len(file_paths)} by config.files")

        all_candidates: list[Candidate] = []
        candidate_sequence = 0
        for file_path in file_paths:
            candidates = self._extract_file_candidates(file_path, extractors)
            if candidates is None:
                self.stats.files_failed += 1
                continue
            self.stats.files_succeeded += 1
            for candidate in candidates:
                candidate_sequence += 1
                candidate.candidate_id = f"C{candidate_sequence:08d}"
            all_candidates.extend(candidates)

        normalized = normalize_candidates(all_candidates, config.normalization)
        terms, occurrences, _candidate_to_term_id, dedup_to_term_id, _term_text_to_term_id = build_terms_and_occurrences(normalized)
        term_by_id = {term.term_id: term for term in terms}
        relations = build_relations(
            terms=terms,
            occurrences=occurrences,
            thresholds=config.thresholds,
            case_insensitive_dedup=config.normalization.case_insensitive_dedup,
            dedup_to_term_id=dedup_to_term_id,
            term_by_id=term_by_id,
            compound_delimiters=config.compound_delimiters,
        )
        review_items, reasons_by_term = build_review_items(
            terms=terms,
            occurrences=occurrences,
            thresholds=config.thresholds,
        )
        self._apply_review_reasons(terms, reasons_by_term)
        term_aggregates = build_term_aggregates(occurrences)
        terms_summary_rows = self._build_terms_summary_rows(terms, term_aggregates)
        relations_summary_rows = build_relation_summary(
            terms=terms,
            occurrences=occurrences,
            relations=relations,
        )

        self._exporter.export(
            output_path=self.output_file,
            terms_summary_rows=terms_summary_rows,
            relations_summary_rows=relations_summary_rows,
            review_items=review_items,
            occurrences=occurrences,
        )

        result = {
            "files_total": self.stats.files_total,
            "files_succeeded": self.stats.files_succeeded,
            "files_failed": self.stats.files_failed,
            "candidates_count": len(all_candidates),
            "terms_count": len(terms),
            "relations_count": len(relations_summary_rows),
            "review_count": len(review_items),
        }
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

    def _filter_file_paths(self, file_paths: list[str], configured_files: tuple[str, ...]) -> list[str]:
        if not configured_files:
            return file_paths
        return [path for path in file_paths if self._is_configured_file(path, configured_files)]

    @staticmethod
    def _is_configured_file(file_path: str, configured_files: tuple[str, ...]) -> bool:
        base_name = os.path.basename(file_path).lower()
        stem = os.path.splitext(base_name)[0]

        for raw_token in configured_files:
            token = raw_token.strip().lower()
            if not token:
                continue
            token_stem, token_ext = os.path.splitext(token)
            if token_ext:
                if base_name == token:
                    return True
            else:
                if stem == token or base_name == token:
                    return True
                if token_stem and stem == token_stem:
                    return True
        return False

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

    def _extract_file_candidates(self, file_path: str, extractors: list[BaseExtractor]) -> list[Candidate] | None:
        try:
            with open_workbook(file_path, read_only=True, data_only=True) as workbook:
                worksheet = workbook.active
                header_map = self._build_header_map(worksheet)
                self._ensure_required_columns(file_path, header_map, extractors)

                candidates: list[Candidate] = []
                for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
                    row_values: dict[str, Any] = {}
                    row_cells_text: dict[str, str] = {}
                    for header, col_index in header_map.items():
                        if col_index < len(row):
                            cell = row[col_index]
                            value = cell.value if cell else None
                        else:
                            value = None
                        row_values[header] = value
                        row_cells_text[header] = safe_to_str(value, strip=False)

                    context = ExtractContext(
                        file_path=file_path,
                        file_name=os.path.basename(file_path),
                        sheet_name=worksheet.title,
                        row_index=row_idx,
                        row_values=row_values,
                        row_cells_text=row_cells_text,
                        header_map=header_map,
                    )
                    for extractor in extractors:
                        candidates.extend(extractor.extract(context))
                    self.stats.rows_scanned += 1

                return candidates
        except Exception as exc:
            self._log_error(
                code="E_TERMINOLOGY_FILE",
                message="Failed to process file for terminology extraction",
                file_path=file_path,
                exc=exc,
            )
            return None

    def _build_header_map(self, worksheet) -> dict[str, int]:
        header_row = next(worksheet.iter_rows(min_row=1, max_row=1), [])
        header_map: dict[str, int] = {}
        fallback_count = 0
        for index, cell in enumerate(header_row):
            raw = safe_to_str(cell.value if cell else None, strip=True)
            header = raw if raw else f"col_{index + 1}"
            if header in header_map:
                fallback_count += 1
                header = f"{header}_{fallback_count}"
            header_map[header] = index

            # Add a lowercase alias so rule/header matching is case-insensitive
            # (e.g. "Version" can satisfy required "version").
            alias = header.lower()
            if alias not in header_map:
                header_map[alias] = index
        return header_map

    def _ensure_required_columns(
        self,
        file_path: str,
        header_map: dict[str, int],
        extractors: list[BaseExtractor],
    ) -> None:
        required: set[str] = set()
        for extractor in extractors:
            required.update(extractor.required_columns())
        missing = sorted(col for col in required if col not in header_map)
        if missing:
            raise ValueError(
                f"Missing required columns in file {file_path}: {', '.join(missing)}"
            )

    def _apply_review_reasons(self, terms: list[TermEntry], reasons_by_term: dict[str, list[str]]) -> None:
        for term in terms:
            reasons = reasons_by_term.get(term.term_id, [])
            term.is_low_confidence = bool(reasons)
            term.review_reasons = ";".join(reasons)

    @staticmethod
    def _build_terms_summary_rows(
        terms: list[TermEntry],
        term_aggregates: dict[str, dict[str, str | int | set[str]]],
    ) -> list[TermSummaryRow]:
        rows: list[TermSummaryRow] = []
        for term in sorted(terms, key=lambda item: item.term_norm):
            aggregate = term_aggregates.get(term.term_id, {})
            files_count = int(aggregate.get("files_count", term.files_count))
            files_list = str(aggregate.get("files_list", ""))
            keys_count = int(aggregate.get("keys_count", 0))
            keys_list = str(aggregate.get("keys_list", ""))
            rows.append(
                TermSummaryRow(
                    term_id=term.term_id,
                    term_norm=term.term_norm,
                    occurrences_count=term.occurrences_count,
                    files_count=files_count,
                    files_list=files_list,
                    keys_count=keys_count,
                    keys_list=keys_list,
                    first_extractor=term.first_extractor,
                    is_low_confidence=term.is_low_confidence,
                    review_reasons=term.review_reasons,
                )
            )
        return rows

    def _log_error(self, code: str, message: str, file_path: str = "", exc: Exception | None = None) -> None:
        event = ErrorEvent(
            code=code,
            message=message,
            file_path=file_path,
            exception=exc,
        )
        self.event_logger.error(self.stats, event)
