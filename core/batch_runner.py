import os
import shutil
import time
import gc
from dataclasses import dataclass
from datetime import datetime

from core.batch_config import (
    BatchConfigV1,
    BatchDefaultsReverse,
    BatchDefaultsSingle,
    MODE_MASTER_TO_TARGET_SINGLE,
    MODE_TARGET_TO_MASTER_REVERSE,
    validate_config_object,
)


@dataclass(frozen=True)
class BatchJobResult:
    job_index: int
    job_name: str
    status: str
    updated_count: int
    error: str
    elapsed_ms: int


@dataclass(frozen=True)
class BatchRunSummary:
    mode: str
    jobs_total: int
    jobs_succeeded: int
    jobs_failed: int
    updated_total: int
    results: tuple[BatchJobResult, ...]
    stopped_early: bool
    backup_path: str = ""


class BatchRunner:
    def __init__(self, single_processor, reverse_processor, log_callback=None):
        self.single_processor = single_processor
        self.reverse_processor = reverse_processor
        self.log = log_callback or (lambda _msg: None)

    def precheck(self, config: BatchConfigV1) -> list[str]:
        return validate_config_object(config, check_paths=True)

    def run(self, config: BatchConfigV1) -> BatchRunSummary:
        backup_path = ""
        errors = self.precheck(config)
        if errors:
            raise ValueError("\n".join(errors))

        if config.mode == MODE_TARGET_TO_MASTER_REVERSE:
            backup_path = self._backup_master_file(config.master_file)
            self.log(f"Batch backup created: {backup_path}")

        results: list[BatchJobResult] = []
        updated_total = 0
        stopped_early = False
        jobs_failed = 0

        for index, job in enumerate(config.jobs, start=1):
            display_name = job.name or f"job-{index}"
            start = time.time()
            self.log(
                f"Batch job start ({index}/{len(config.jobs)}): "
                f"{display_name} -> {job.target_folder}"
            )

            try:
                updated_count = self._run_single_job(config, index - 1)
                updated_total += updated_count
                result = BatchJobResult(
                    job_index=index,
                    job_name=display_name,
                    status="success",
                    updated_count=updated_count,
                    error="",
                    elapsed_ms=int((time.time() - start) * 1000),
                )
                self.log(
                    f"Batch job done ({index}/{len(config.jobs)}): "
                    f"{display_name}, updated={updated_count}"
                )
            except Exception as exc:
                jobs_failed += 1
                result = BatchJobResult(
                    job_index=index,
                    job_name=display_name,
                    status="failed",
                    updated_count=0,
                    error=str(exc),
                    elapsed_ms=int((time.time() - start) * 1000),
                )
                self.log(
                    f"Batch job failed ({index}/{len(config.jobs)}): "
                    f"{display_name}, error={exc}"
                )
                if not config.runtime.continue_on_error:
                    stopped_early = True
                    results.append(result)
                    break
            finally:
                self._cleanup_after_job(config.mode)

            results.append(result)

        self._collect_memory(force=True)
        return BatchRunSummary(
            mode=config.mode,
            jobs_total=len(config.jobs),
            jobs_succeeded=len(results) - jobs_failed,
            jobs_failed=jobs_failed,
            updated_total=updated_total,
            results=tuple(results),
            stopped_early=stopped_early,
            backup_path=backup_path,
        )

    def _run_single_job(self, config: BatchConfigV1, job_index: int) -> int:
        job = config.jobs[job_index]
        if config.mode == MODE_MASTER_TO_TARGET_SINGLE:
            defaults = config.defaults
            assert isinstance(defaults, BatchDefaultsSingle)
            processor = self.single_processor
            processor.set_master_file(config.master_file)
            processor.set_target_folder(job.target_folder)
            processor.set_target_column(
                defaults.target_key_col - 1,
                defaults.target_match_col - 1,
                defaults.target_update_start_col - 1,
            )
            processor.set_master_column(
                defaults.master_key_col - 1,
                defaults.master_match_col - 1,
                job.variable_column - 1,
            )
            processor.set_fill_blank_only(defaults.fill_blank_only)
            processor.set_allow_blank_write(defaults.allow_blank_write)
            processor.set_post_process_enabled(defaults.post_process_enabled)
            return int(processor.process_files() or 0)

        defaults = config.defaults
        assert isinstance(defaults, BatchDefaultsReverse)
        processor = self.reverse_processor
        processor.set_master_file(config.master_file)
        processor.set_target_folder(job.target_folder)
        processor.set_target_columns(
            defaults.target_key_col - 1,
            defaults.target_match_col - 1,
            defaults.target_content_col - 1,
        )
        processor.set_master_columns(
            defaults.master_key_col - 1,
            defaults.master_match_col - 1,
            job.variable_column - 1,
        )
        processor.set_fill_blank_only(defaults.fill_blank_only)
        processor.set_allow_blank_write(defaults.allow_blank_write)
        return int(processor.process_files() or 0)

    @staticmethod
    def _backup_master_file(master_file: str) -> str:
        folder = os.path.dirname(master_file)
        stem, ext = os.path.splitext(os.path.basename(master_file))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{stem}.batch_backup.{timestamp}{ext}"
        backup_path = os.path.join(folder, backup_name)
        shutil.copy2(master_file, backup_path)
        return backup_path

    def _cleanup_after_job(self, mode: str) -> None:
        if mode == MODE_MASTER_TO_TARGET_SINGLE:
            self._invoke_processor_cleanup(self.single_processor, "single")
        elif mode == MODE_TARGET_TO_MASTER_REVERSE:
            self._invoke_processor_cleanup(self.reverse_processor, "reverse")
        self._collect_memory(force=False)

    def _invoke_processor_cleanup(self, processor, processor_name: str) -> None:
        cleanup = getattr(processor, "cleanup_after_run", None)
        if not callable(cleanup):
            return
        try:
            cleanup()
        except Exception as exc:
            self.log(f"Batch cleanup warning ({processor_name}): {exc}")

    @staticmethod
    def _collect_memory(force: bool) -> None:
        generation = 2 if force else 1
        gc.collect(generation)
