import threading
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


class TkSingleTaskRunner:
    def __init__(
        self,
        root,
        set_busy: Callable[[bool], None],
        set_status: Callable[[str], None],
    ):
        self._root = root
        self._set_busy = set_busy
        self._set_status = set_status
        self._state_lock = threading.Lock()
        self._running = False

    def run(
        self,
        task_name: str,
        action: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> bool:
        with self._state_lock:
            if self._running:
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

            def finish():
                try:
                    if error is None:
                        self._set_status_safe(self._status_text("Done", task_name))
                        on_success(result)
                    else:
                        self._set_status_safe(self._status_text("Failed", task_name))
                        on_error(error)
                finally:
                    self._set_busy_safe(False)
                    with self._state_lock:
                        self._running = False

            self._dispatch_to_ui(finish)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return True

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

    def _dispatch_to_ui(self, callback: Callable[[], None]) -> None:
        try:
            self._root.after(0, callback)
        except Exception:
            callback()

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
