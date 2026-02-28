from typing import Callable, Sequence

from core.kernel import run_parallel_sum


def process_files_in_parallel(
    file_paths: Sequence[str],
    worker: Callable[[str], int],
    max_workers_cap: int = 32,
) -> int:
    return run_parallel_sum(
        file_paths,
        worker,
        max_workers_cap=max_workers_cap,
    )
