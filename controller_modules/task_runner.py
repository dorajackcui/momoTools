import queue
import threading
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol


class TaskRunner(Protocol):
    def run(
        self,
        task_name: str,
        action: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> bool:
        ...


class InlineTaskRunner:
    def run(
        self,
        task_name: str,
        action: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> bool:
        try:
            on_success(action())
            return True
        except Exception as exc:
            on_error(exc)
            return True


@dataclass(frozen=True)
class _TaskCompletion:
    task_name: str
    result: Any
    error: Optional[Exception]
    on_success: Callable[[Any], None]
    on_error: Callable[[Exception], None]


class TkSingleTaskRunner:
    def __init__(
        self,
        root,
        set_busy: Callable[[bool], None],
        set_status: Callable[[str], None],
        diagnostic_sink: Optional[Callable[[str], None]] = None,
    ):
        self._root = root
        self._set_busy = set_busy
        self._set_status = set_status
        self._diagnostic_sink = diagnostic_sink or (lambda _message: None)
        self._completion_queue: queue.Queue[_TaskCompletion] = queue.Queue()
        self._state_lock = threading.Lock()
        self._running = False
        self._shutdown = False

    def run(
        self,
        task_name: str,
        action: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> bool:
        with self._state_lock:
            if self._running or self._shutdown:
                return False
            self._running = True

        self._set_busy_safe(True)
        self._set_status_safe(self._status_text("Running", task_name))

        def worker():
            result = None
            error: Optional[Exception] = None
            com_module = self._co_initialize()
            try:
                result = action()
            except Exception as exc:
                error = exc
            finally:
                self._co_uninitialize(com_module)

            completion = _TaskCompletion(
                task_name=task_name,
                result=result,
                error=error,
                on_success=on_success,
                on_error=on_error,
            )
            if self._is_shutdown():
                self._skip_completion(completion)
                return
            self._completion_queue.put(completion)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return True

    def drain_pending_completions(self) -> None:
        while True:
            try:
                completion = self._completion_queue.get_nowait()
            except queue.Empty:
                return
            if self._is_shutdown():
                self._skip_completion(completion)
                continue
            self._finish_on_ui(completion)

    def shutdown(self) -> None:
        with self._state_lock:
            self._shutdown = True
        while True:
            try:
                completion = self._completion_queue.get_nowait()
            except queue.Empty:
                return
            self._skip_completion(completion)

    @staticmethod
    def _status_text(prefix: str, task_name: str) -> str:
        if task_name:
            return f"{prefix}: {task_name}"
        return prefix

    def _set_busy_safe(self, value: bool) -> None:
        try:
            self._set_busy(value)
        except Exception:
            pass

    def _set_status_safe(self, text: str) -> None:
        try:
            self._set_status(text)
        except Exception:
            pass

    def _finish_on_ui(self, completion: _TaskCompletion) -> None:
        try:
            if completion.error is None:
                self._set_status_safe(self._status_text("Done", completion.task_name))
                completion.on_success(completion.result)
            else:
                self._set_status_safe(self._status_text("Failed", completion.task_name))
                completion.on_error(completion.error)
        except Exception as exc:
            self._log_diagnostic(
                "TASKRUNNER_UI_CALLBACK_ERROR",
                completion.task_name,
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            self._set_busy_safe(False)
            self._mark_not_running()

    def _skip_completion(self, completion: _TaskCompletion) -> None:
        self._log_diagnostic(
            "TASKRUNNER_UI_COMPLETION_SKIPPED",
            completion.task_name,
            "UI shutdown before task completion could be delivered",
        )
        self._mark_not_running()

    def _mark_not_running(self) -> None:
        with self._state_lock:
            self._running = False

    def _is_shutdown(self) -> bool:
        with self._state_lock:
            return self._shutdown

    def _log_diagnostic(self, code: str, task_name: str, detail: str) -> None:
        try:
            message = f"{code}: {task_name} - {detail}" if task_name else f"{code}: {detail}"
            self._diagnostic_sink(message)
        except Exception:
            pass

    @staticmethod
    def _co_initialize():
        try:
            import pythoncom

            pythoncom.CoInitialize()
            return pythoncom
        except Exception:
            return None

    @staticmethod
    def _co_uninitialize(com_module) -> None:
        if com_module is None:
            return
        try:
            com_module.CoUninitialize()
        except Exception:
            pass
