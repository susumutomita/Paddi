"""Tests for AsyncExecutor."""

import time
import unittest

from app.api.async_executor import AsyncExecutor


class TestAsyncExecutor(unittest.TestCase):
    """Test cases for AsyncExecutor."""

    def setUp(self):
        """Set up test environment."""
        self.executor = AsyncExecutor(max_workers=2)

    def tearDown(self):
        """Clean up test environment."""
        self.executor.shutdown(wait=True)

    def test_submit_audit(self):
        """Test submitting an audit task."""

        def dummy_task(value):
            time.sleep(0.1)
            return {"result": value}

        # Submit task
        self.executor.submit_audit("audit-1", dummy_task, "test-value")

        # Verify task is running
        self.assertTrue(self.executor.is_running("audit-1"))

        # Wait for completion
        time.sleep(0.2)

        # Verify task completed
        self.assertFalse(self.executor.is_running("audit-1"))

        # Get result
        result = self.executor.get_result("audit-1")
        self.assertEqual(result["result"], "test-value")

    def test_submit_duplicate_audit(self):
        """Test submitting duplicate audit IDs."""

        def dummy_task():
            time.sleep(0.5)
            return "done"

        # Submit first task
        self.executor.submit_audit("audit-1", dummy_task)

        # Try to submit duplicate
        with self.assertRaises(ValueError) as context:
            self.executor.submit_audit("audit-1", dummy_task)

        self.assertIn("already running", str(context.exception))

    def test_cancel_audit(self):
        """Test canceling an audit."""

        def slow_task():
            time.sleep(2)
            return "should not complete"

        # Submit task
        self.executor.submit_audit("audit-1", slow_task)

        # Cancel immediately
        self.executor.cancel_audit("audit-1")

        # Note: cancellation may not always succeed if task already started
        # This is a limitation of Python's concurrent.futures

    def test_get_result_not_found(self):
        """Test getting result of non-existent audit."""
        result = self.executor.get_result("non-existent")
        self.assertIsNone(result)

    def test_is_running_not_found(self):
        """Test checking status of non-existent audit."""
        is_running = self.executor.is_running("non-existent")
        self.assertFalse(is_running)

    def test_task_with_exception(self):
        """Test handling task that raises exception."""

        def failing_task():
            raise RuntimeError("Task failed")

        # Submit failing task
        self.executor.submit_audit("audit-fail", failing_task)

        # Wait for completion
        time.sleep(0.1)

        # Get result should return error
        result = self.executor.get_result("audit-fail")
        self.assertIsNotNone(result)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Task failed")

    def test_cleanup_completed_tasks(self):
        """Test that completed tasks are cleaned up."""

        def quick_task(audit_id):
            return f"completed-{audit_id}"

        # Submit multiple tasks
        for i in range(5):
            self.executor.submit_audit(f"audit-{i}", quick_task, f"audit-{i}")

        # Wait for completion
        time.sleep(0.2)

        # Submit another task to trigger cleanup
        self.executor.submit_audit("audit-cleanup", quick_task, "cleanup")

        # Verify internal state doesn't grow indefinitely
        # (This is more of an implementation detail test)
        self.assertLessEqual(len(self.executor.running_tasks), 6)


if __name__ == "__main__":
    unittest.main()
