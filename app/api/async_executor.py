"""Async executor for running Paddi agents in background."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Executes tasks asynchronously using ThreadPoolExecutor."""

    def __init__(self, max_workers: int = 3):
        """Initialize executor with thread pool."""
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks = {}  # audit_id -> future
        self._lock = threading.Lock()

    def submit_audit(self, audit_id: str, task: Callable, *args, **kwargs) -> None:
        """Submit an audit task for async execution."""
        with self._lock:
            if audit_id in self.running_tasks:
                raise ValueError(f"Audit {audit_id} is already running")

            future = self.executor.submit(task, *args, **kwargs)
            self.running_tasks[audit_id] = future

            # Clean up completed tasks
            self._cleanup_completed_tasks()

    def is_running(self, audit_id: str) -> bool:
        """Check if an audit is currently running."""
        with self._lock:
            if audit_id not in self.running_tasks:
                return False
            return not self.running_tasks[audit_id].done()

    def get_result(self, audit_id: str) -> Optional[Dict]:
        """Get result of a completed audit."""
        with self._lock:
            if audit_id not in self.running_tasks:
                return None

            future = self.running_tasks[audit_id]
            if not future.done():
                return None

            try:
                return future.result()
            except Exception as e:
                logger.error("Error getting result for %s: %s", audit_id, str(e))
                return {"error": str(e)}

    def cancel_audit(self, audit_id: str) -> bool:
        """Cancel a running audit."""
        with self._lock:
            if audit_id not in self.running_tasks:
                return False

            future = self.running_tasks[audit_id]
            return future.cancel()

    def _cleanup_completed_tasks(self) -> None:
        """Remove completed tasks from tracking."""
        completed = [audit_id for audit_id, future in self.running_tasks.items() if future.done()]
        for audit_id in completed:
            try:
                # Ensure any exceptions are logged
                self.running_tasks[audit_id].result()
            except Exception as e:
                logger.error("Task %s failed: %s", audit_id, str(e))
            # Don't delete the task immediately - get_result needs to access it
            # del self.running_tasks[audit_id]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor."""
        self.executor.shutdown(wait=wait)
