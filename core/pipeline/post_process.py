import os
import time
from typing import Callable, Sequence


def run_excel_com_post_process(
    file_paths: Sequence[str],
    per_file_runner: Callable[[str, object], None],
    log_callback: Callable[[str], None],
    fail_callback: Callable[[Exception], None],
) -> None:
    if not file_paths:
        return

    excel_app = None
    total_files = len(file_paths)
    post_process_start_time = time.time()

    try:
        from win32com.client import Dispatch

        excel_app = Dispatch("Excel.Application")
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        for index, file_path in enumerate(file_paths, 1):
            log_callback(
                f"正在后处理文件 ({index}/{total_files}): {os.path.basename(file_path)}"
            )
            per_file_runner(file_path, excel_app)
    except Exception as exc:
        fail_callback(exc)
    finally:
        if excel_app is not None:
            try:
                excel_app.Quit()
            except Exception:
                pass

    elapsed = time.time() - post_process_start_time
    log_callback(f"后处理步骤耗时: {elapsed:.2f}秒")
