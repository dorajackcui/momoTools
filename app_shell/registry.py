from dataclasses import dataclass

from controllers import (
    BatchController,
    ClearerController,
    CompatibilityController,
    DeepReplaceController,
    MasterMergeController,
    ReverseUpdaterController,
    SourceTranslationPipelineController,
    TerminologyExtractorController,
    UpdateContentController,
    UpdateMasterController,
    UntranslatedStatsController,
    UpdaterController,
)
from ui.views import (
    BatchFrame,
    ClearerFrame,
    CompatibilityFrame,
    DeepReplaceFrame,
    MergeMastersFrame,
    ReverseUpdaterFrame,
    SourceTranslationPipelineFrame,
    TerminologyExtractorFrame,
    UntranslatedStatsFrame,
    UpdateContentFrame,
    UpdateMasterFrame,
    UpdaterFrame,
)


@dataclass(frozen=True)
class ToolGroupSpec:
    key: str
    title: str


@dataclass(frozen=True)
class ToolSpec:
    group: str
    tab_text: str
    controller_cls: type
    frame_cls: type
    processor_attrs: tuple[str, ...] = ()
    after_mount_hooks: tuple[str, ...] = ()


def build_tool_groups() -> tuple[ToolGroupSpec, ...]:
    return (
        ToolGroupSpec(key="main", title="Content Sync"),
        ToolGroupSpec(key="utilities", title="Utilities"),
        ToolGroupSpec(key="update_master", title="Master Update"),
    )


def build_tool_specs() -> tuple[ToolSpec, ...]:
    return (
        ToolSpec(
            group="main",
            tab_text="Master->Target",
            controller_cls=UpdaterController,
            frame_cls=UpdaterFrame,
            processor_attrs=("excel_processor", "multi_processor"),
        ),
        ToolSpec(
            group="main",
            tab_text="Target->Master",
            controller_cls=ReverseUpdaterController,
            frame_cls=ReverseUpdaterFrame,
            processor_attrs=("reverse_excel_processor",),
        ),
        ToolSpec(
            group="main",
            tab_text="Batch",
            controller_cls=BatchController,
            frame_cls=BatchFrame,
            processor_attrs=("excel_processor", "reverse_excel_processor"),
            after_mount_hooks=("restore_persisted_paths",),
        ),
        ToolSpec(
            group="utilities",
            tab_text="Column Clear",
            controller_cls=ClearerController,
            frame_cls=ClearerFrame,
            processor_attrs=("clearer",),
        ),
        ToolSpec(
            group="utilities",
            tab_text="Compatibility",
            controller_cls=CompatibilityController,
            frame_cls=CompatibilityFrame,
            processor_attrs=("compatibility_processor",),
        ),
        ToolSpec(
            group="utilities",
            tab_text="Deep Replace",
            controller_cls=DeepReplaceController,
            frame_cls=DeepReplaceFrame,
            processor_attrs=("deep_replace_processor",),
        ),
        ToolSpec(
            group="utilities",
            tab_text="Untranslated Stats",
            controller_cls=UntranslatedStatsController,
            frame_cls=UntranslatedStatsFrame,
            processor_attrs=("untranslated_stats_processor",),
        ),
        ToolSpec(
            group="utilities",
            tab_text="Term Extractor",
            controller_cls=TerminologyExtractorController,
            frame_cls=TerminologyExtractorFrame,
            processor_attrs=("terminology_processor",),
            after_mount_hooks=("restore_persisted_paths",),
        ),
        ToolSpec(
            group="update_master",
            tab_text="Merge Masters",
            controller_cls=MasterMergeController,
            frame_cls=MergeMastersFrame,
            processor_attrs=("master_merge_processor",),
        ),
        ToolSpec(
            group="update_master",
            tab_text="Source Text",
            controller_cls=UpdateMasterController,
            frame_cls=UpdateMasterFrame,
            processor_attrs=("master_merge_processor",),
        ),
        ToolSpec(
            group="update_master",
            tab_text="Translation",
            controller_cls=UpdateContentController,
            frame_cls=UpdateContentFrame,
            processor_attrs=("master_merge_processor",),
        ),
        ToolSpec(
            group="update_master",
            tab_text="Source+Translation",
            controller_cls=SourceTranslationPipelineController,
            frame_cls=SourceTranslationPipelineFrame,
            processor_attrs=("master_merge_processor",),
        ),
    )
