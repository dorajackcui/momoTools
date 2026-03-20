from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ProcessorBundle:
    excel_processor: object
    clearer: object
    compatibility_processor: object
    multi_processor: object
    deep_replace_processor: object
    reverse_excel_processor: object
    master_merge_processor: object
    untranslated_stats_processor: object
    terminology_processor: object


def build_processors(log_sink: Callable[[str], None]) -> ProcessorBundle:
    from core.deep_replace_processor import DeepReplaceProcessor
    from core.excel_cleaner import ExcelColumnClearer
    from core.excel_compatibility_processor import ExcelCompatibilityProcessor
    from core.excel_processor import ExcelProcessor
    from core.master_merge_processor import MasterMergeProcessor
    from core.multi_column_processor import MultiColumnExcelProcessor
    from core.reverse_excel_processor import ReverseExcelProcessor
    from core.terminology import TerminologyProcessor
    from core.untranslated_stats_processor import UntranslatedStatsProcessor

    clearer = ExcelColumnClearer()
    clearer.set_log_callback(log_sink)

    compatibility_processor = ExcelCompatibilityProcessor()
    compatibility_processor.set_log_callback(log_sink)

    return ProcessorBundle(
        excel_processor=ExcelProcessor(log_sink),
        clearer=clearer,
        compatibility_processor=compatibility_processor,
        multi_processor=MultiColumnExcelProcessor(log_sink),
        deep_replace_processor=DeepReplaceProcessor(log_sink),
        reverse_excel_processor=ReverseExcelProcessor(log_sink),
        master_merge_processor=MasterMergeProcessor(log_sink),
        untranslated_stats_processor=UntranslatedStatsProcessor(log_sink),
        terminology_processor=TerminologyProcessor(log_sink),
    )
