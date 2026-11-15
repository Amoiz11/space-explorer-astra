"""
Thread-safe bootstrap status tracker for server startup.
"""

import threading
from typing import Optional

_lock = threading.Lock()
_status: str = "done"
_failure_reason: Optional[str] = None


def is_running() -> bool:
    """Return True if background bootstrap is currently executing."""
    with _lock:
        return _status == "running"


def get_status() -> str:
    """Return 'running', 'done', or 'failed: <reason>'."""
    with _lock:
        if _status == "failed" and _failure_reason:
            return f"failed: {_failure_reason}"
        return _status


def set_running() -> None:
    """Mark bootstrap as running."""
    global _status, _failure_reason
    with _lock:
        _status = "running"
        _failure_reason = None


def set_done() -> None:
    """Mark bootstrap as completed successfully."""
    global _status, _failure_reason
    with _lock:
        _status = "done"
        _failure_reason = None


def set_failed(reason: str) -> None:
    """Mark bootstrap as failed with reason."""
    global _status, _failure_reason
    with _lock:
        _status = "failed"
        _failure_reason = reason
