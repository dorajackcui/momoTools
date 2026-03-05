import pandas as pd

from .types import RelationSummaryRow, ReviewItem, TermOccurrence, TermSummaryRow


class TerminologyExcelExporter:
    def export(
        self,
        output_path: str,
        terms_summary_rows: list[TermSummaryRow],
        relations_summary_rows: list[RelationSummaryRow],
        review_items: list[ReviewItem],
        occurrences: list[TermOccurrence],
    ) -> None:
        terms_summary_columns = [
            "term_id",
            "term_type",
            "term_norm",
            "occurrences_count",
            "files_count",
            "files_list",
            "keys_count",
            "keys_list",
            "first_extractor",
            "is_low_confidence",
            "review_reasons",
        ]
        terms_summary_df = pd.DataFrame(
            [
                {
                    "term_id": row.term_id,
                    "term_type": row.term_type,
                    "term_norm": row.term_norm,
                    "occurrences_count": row.occurrences_count,
                    "files_count": row.files_count,
                    "files_list": row.files_list,
                    "keys_count": row.keys_count,
                    "keys_list": row.keys_list,
                    "first_extractor": row.first_extractor,
                    "is_low_confidence": row.is_low_confidence,
                    "review_reasons": row.review_reasons,
                }
                for row in terms_summary_rows
            ],
            columns=terms_summary_columns,
        )

        relations_summary_columns = [
            "relation_type",
            "evidence_count",
            "cross_term",
            "cross_files_count",
            "cross_files_list",
            "affix_role",
            "affix_anchor_term",
            "affix_related_count",
            "affix_related_list",
            "affix_delimiters",
            "notes",
        ]
        relations_summary_df = pd.DataFrame(
            [
                {
                    "relation_type": row.relation_type,
                    "evidence_count": row.evidence_count,
                    "cross_term": row.cross_term,
                    "cross_files_count": row.cross_files_count,
                    "cross_files_list": row.cross_files_list,
                    "affix_role": row.affix_role,
                    "affix_anchor_term": row.affix_anchor_term,
                    "affix_related_count": row.affix_related_count,
                    "affix_related_list": row.affix_related_list,
                    "affix_delimiters": row.affix_delimiters,
                    "notes": row.notes,
                }
                for row in relations_summary_rows
            ],
            columns=relations_summary_columns,
        )

        review_columns = [
            "term_id",
            "term_norm",
            "reason",
            "severity",
            "occurrences_count",
            "sample_file",
            "sample_row",
            "sample_col",
        ]
        review_df = pd.DataFrame(
            [
                {
                    "term_id": item.term_id,
                    "term_norm": item.term_norm,
                    "reason": item.reason,
                    "severity": item.severity,
                    "occurrences_count": item.occurrences_count,
                    "sample_file": item.sample_file,
                    "sample_row": item.sample_row,
                    "sample_col": item.sample_col,
                }
                for item in review_items
            ],
            columns=review_columns,
        )

        details_columns = [
            "term_id",
            "term_type",
            "term_norm",
            "candidate_id",
            "extractor_type",
            "rule_id",
            "file",
            "sheet",
            "row",
            "col",
            "key_value",
            "version_value",
            "term_raw",
            "cell_raw",
        ]
        details_df = pd.DataFrame(
            [
                {
                    "term_id": occ.term_id,
                    "term_type": occ.term_type,
                    "term_norm": occ.term_norm,
                    "candidate_id": occ.candidate.candidate_id,
                    "extractor_type": occ.candidate.extractor_type,
                    "rule_id": occ.candidate.rule_id,
                    "file": occ.candidate.file,
                    "sheet": occ.candidate.sheet,
                    "row": occ.candidate.row,
                    "col": occ.candidate.col,
                    "key_value": str(occ.candidate.meta.get("key", "")),
                    "version_value": str(occ.candidate.meta.get("version", "")),
                    "term_raw": occ.candidate.term_raw,
                    "cell_raw": occ.candidate.cell_raw,
                }
                for occ in occurrences
            ],
            columns=details_columns,
        )

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            terms_summary_df.to_excel(writer, sheet_name="terms_summary", index=False)
            relations_summary_df.to_excel(writer, sheet_name="relations_summary", index=False)
            review_df.to_excel(writer, sheet_name="review", index=False)
            details_df.to_excel(writer, sheet_name="details", index=False)
