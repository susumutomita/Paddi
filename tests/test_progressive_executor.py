"""Tests for progressive executor module."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from app.execution.progressive_executor import (
    ExecutionControl,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    ProgressListener,
    ProgressiveExecutor,
    StepStatus,
    UserInputProvider,
)


class MockProgressListener(ProgressListener):
    """Mock implementation of ProgressListener."""

    def __init__(self):
        self.plan_start_called = False
        self.step_start_calls = []
        self.step_complete_calls = []
        self.plan_complete_called = False
        self.error_calls = []

    async def on_plan_start(self, plan: ExecutionPlan) -> None:
        self.plan_start_called = True

    async def on_step_start(self, step: ExecutionStep) -> None:
        self.step_start_calls.append(step.id)

    async def on_step_complete(
        self, step: ExecutionStep, result: ExecutionResult
    ) -> None:
        self.step_complete_calls.append((step.id, result.status))

    async def on_plan_complete(self, plan: ExecutionPlan) -> None:
        self.plan_complete_called = True

    async def on_error(self, step: ExecutionStep, error: Exception) -> None:
        self.error_calls.append((step.id, str(error)))


class MockUserInputProvider(UserInputProvider):
    """Mock implementation of UserInputProvider."""

    def __init__(self):
        self.confirmations = {}
        self.choices = {}
        self.control_inputs = [ExecutionControl.CONTINUE]

    async def get_confirmation(self, message: str) -> bool:
        return self.confirmations.get(message, True)

    async def get_choice(
        self, message: str, options: list[str]
    ) -> str:
        return self.choices.get(message, options[0] if options else None)

    async def get_control_input(self) -> ExecutionControl:
        if self.control_inputs:
            return self.control_inputs.pop(0)
        return ExecutionControl.CONTINUE


@pytest.fixture
def executor():
    """Create a ProgressiveExecutor instance."""
    return ProgressiveExecutor()


@pytest.fixture
def mock_listener():
    """Create a mock progress listener."""
    return MockProgressListener()


@pytest.fixture
def mock_input_provider():
    """Create a mock user input provider."""
    return MockUserInputProvider()


@pytest.fixture
def sample_plan():
    """Create a sample execution plan."""
    steps = [
        ExecutionStep(
            id="step1",
            description="First step",
            execute=lambda: "result1",
            can_skip=True,
            requires_confirmation=False,
        ),
        ExecutionStep(
            id="step2",
            description="Second step",
            execute=lambda: "result2",
            can_skip=True,
            requires_confirmation=False,
        ),
        ExecutionStep(
            id="step3",
            description="Third step",
            execute=lambda: "result3",
            can_skip=False,
            requires_confirmation=False,
        ),
    ]
    return ExecutionPlan(
        steps=steps,
        name="Test Plan",
        description="Test execution plan",
    )


@pytest.mark.asyncio
async def test_executor_initialization():
    """Test ProgressiveExecutor initialization."""
    executor = ProgressiveExecutor()
    assert executor.listeners == []
    assert executor.input_provider is None
    assert not executor._is_paused
    assert not executor._is_aborted


@pytest.mark.asyncio
async def test_add_remove_listener(executor, mock_listener):
    """Test adding and removing listeners."""
    executor.add_listener(mock_listener)
    assert mock_listener in executor.listeners

    executor.remove_listener(mock_listener)
    assert mock_listener not in executor.listeners


@pytest.mark.asyncio
async def test_execute_simple_plan(executor, sample_plan, mock_listener):
    """Test executing a simple plan without user interaction."""
    executor.add_listener(mock_listener)

    results = await executor.execute_with_feedback(sample_plan)

    # Verify all steps executed
    assert len(results) == 3
    assert all(r.status == StepStatus.COMPLETED for r in results.values())

    # Verify listener callbacks
    assert mock_listener.plan_start_called
    assert mock_listener.step_start_calls == ["step1", "step2", "step3"]
    assert len(mock_listener.step_complete_calls) == 3
    assert mock_listener.plan_complete_called


@pytest.mark.asyncio
async def test_execute_with_confirmation(
    executor, mock_listener, mock_input_provider
):
    """Test execution with confirmation required."""
    step = ExecutionStep(
        id="confirm_step",
        description="Confirmation required",
        execute=lambda: "confirmed",
        requires_confirmation=True,
    )
    plan = ExecutionPlan(
        steps=[step], name="Confirm Plan", description="Test confirmation"
    )

    executor.add_listener(mock_listener)
    executor.input_provider = mock_input_provider

    # Test confirmation accepted
    mock_input_provider.confirmations["Execute step: Confirmation required?"] = True
    results = await executor.execute_with_feedback(plan)
    assert results["confirm_step"].status == StepStatus.COMPLETED

    # Test confirmation rejected
    mock_input_provider.confirmations["Execute step: Confirmation required?"] = False
    results = await executor.execute_with_feedback(plan)
    assert results["confirm_step"].status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_execute_with_error(executor, mock_listener):
    """Test execution with step that raises an error."""

    def failing_step():
        raise ValueError("Test error")

    step = ExecutionStep(
        id="error_step",
        description="Failing step",
        execute=failing_step,
    )
    plan = ExecutionPlan(
        steps=[step], name="Error Plan", description="Test error handling"
    )

    executor.add_listener(mock_listener)

    results = await executor.execute_with_feedback(plan)

    assert results["error_step"].status == StepStatus.FAILED
    assert isinstance(results["error_step"].error, ValueError)
    assert len(mock_listener.error_calls) == 1
    assert mock_listener.error_calls[0][0] == "error_step"


@pytest.mark.asyncio
async def test_pause_resume_execution(executor, sample_plan, mock_listener):
    """Test pausing and resuming execution."""
    executor.add_listener(mock_listener)

    # Start execution in background
    task = asyncio.create_task(executor.execute_with_feedback(sample_plan))

    # Let first step complete
    await asyncio.sleep(0.1)

    # Pause execution
    await executor.pause()
    assert executor._is_paused

    # Resume execution
    await executor.resume()
    assert not executor._is_paused

    # Wait for completion
    results = await task
    assert len(results) == 3


@pytest.mark.asyncio
async def test_abort_execution(executor, sample_plan, mock_listener):
    """Test aborting execution."""
    executor.add_listener(mock_listener)

    # Start execution in background
    task = asyncio.create_task(executor.execute_with_feedback(sample_plan))

    # Let first step complete
    await asyncio.sleep(0.1)

    # Abort execution
    await executor.abort()
    assert executor._is_aborted

    # Wait for completion
    results = await task

    # Not all steps should have been executed
    assert len(results) < 3


@pytest.mark.asyncio
async def test_skip_control(executor, sample_plan, mock_input_provider):
    """Test skipping steps with user control."""
    executor.input_provider = mock_input_provider

    # Set control inputs to skip first two steps
    mock_input_provider.control_inputs = [
        ExecutionControl.SKIP,
        ExecutionControl.SKIP,
        ExecutionControl.CONTINUE,
    ]

    results = await executor.execute_with_feedback(sample_plan)

    # First two steps should be skipped (they have can_skip=True)
    assert results["step1"].status == StepStatus.SKIPPED
    assert results["step2"].status == StepStatus.SKIPPED
    # Third step cannot be skipped
    assert results["step3"].status == StepStatus.COMPLETED


@pytest.mark.asyncio
async def test_async_step_execution(executor):
    """Test execution of async steps."""

    async def async_step():
        await asyncio.sleep(0.1)
        return "async_result"

    step = ExecutionStep(
        id="async_step",
        description="Async step",
        execute=async_step,
    )
    plan = ExecutionPlan(
        steps=[step], name="Async Plan", description="Test async execution"
    )

    results = await executor.execute_with_feedback(plan)

    assert results["async_step"].status == StepStatus.COMPLETED
    assert results["async_step"].result == "async_result"


@pytest.mark.asyncio
async def test_get_progress(executor, sample_plan):
    """Test getting execution progress."""
    # Before execution
    progress = executor.get_progress()
    assert progress["status"] == "idle"

    # Start execution in background
    task = asyncio.create_task(executor.execute_with_feedback(sample_plan))

    # Check progress during execution
    await asyncio.sleep(0.1)
    progress = executor.get_progress()
    assert progress["status"] == "running"
    assert progress["total"] == 3
    assert 0 <= progress["percentage"] <= 100

    # Wait for completion
    await task

    # Check final progress
    progress = executor.get_progress()
    assert progress["completed"] == 3
    assert progress["percentage"] == 100


@pytest.mark.asyncio
async def test_error_retry(executor, mock_input_provider):
    """Test retrying failed steps."""
    attempt_count = 0

    def flaky_step():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise ValueError("First attempt fails")
        return "success"

    step = ExecutionStep(
        id="flaky_step",
        description="Flaky step",
        execute=flaky_step,
    )
    plan = ExecutionPlan(
        steps=[step], name="Retry Plan", description="Test retry"
    )

    executor.input_provider = mock_input_provider
    mock_input_provider.choices[
        "Step 'Flaky step' failed. What would you like to do?"
    ] = "retry"

    results = await executor.execute_with_feedback(plan)

    assert results["flaky_step"].status == StepStatus.COMPLETED
    assert results["flaky_step"].result == "success"
    assert attempt_count == 2