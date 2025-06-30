"""Tests for feedback manager module."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.execution.feedback_manager import (
    FeedbackLevel,
    FeedbackManager,
    FeedbackMessage,
    StepMetrics,
)
from app.execution.progressive_executor import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    StepStatus,
)


@pytest.fixture
def feedback_manager():
    """Create a FeedbackManager instance."""
    return FeedbackManager(max_history=10)


@pytest.fixture
def sample_step():
    """Create a sample execution step."""
    return ExecutionStep(
        id="test_step",
        description="Test step",
        execute=lambda: "result",
        estimated_duration=5.0,
    )


@pytest.fixture
def sample_plan():
    """Create a sample execution plan."""
    steps = [
        ExecutionStep(id=f"step{i}", description=f"Step {i}", execute=lambda: f"result{i}")
        for i in range(3)
    ]
    return ExecutionPlan(
        steps=steps,
        name="Test Plan",
        description="Test execution plan",
    )


def test_feedback_manager_initialization(feedback_manager):
    """Test FeedbackManager initialization."""
    assert feedback_manager.messages.maxlen == 10
    assert feedback_manager.metrics == {}
    assert feedback_manager.callback is None
    assert feedback_manager._completed_steps == 0


def test_add_message(feedback_manager):
    """Test adding feedback messages."""
    # Add a message
    feedback_manager.add_message(
        FeedbackLevel.INFO,
        "Test message",
        step_id="step1",
        details={"key": "value"},
    )

    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.INFO
    assert message.message == "Test message"
    assert message.step_id == "step1"
    assert message.details == {"key": "value"}
    assert isinstance(message.timestamp, datetime)


def test_add_message_with_callback(feedback_manager):
    """Test adding message with callback."""
    callback = MagicMock()
    feedback_manager.callback = callback

    feedback_manager.add_message(FeedbackLevel.INFO, "Test message")

    callback.assert_called_once()
    assert isinstance(callback.call_args[0][0], FeedbackMessage)


def test_message_history_limit(feedback_manager):
    """Test message history limit."""
    # Add more messages than max_history
    for i in range(15):
        feedback_manager.add_message(FeedbackLevel.INFO, f"Message {i}")

    # Should only keep last 10 messages
    assert len(feedback_manager.messages) == 10
    assert feedback_manager.messages[0].message == "Message 5"
    assert feedback_manager.messages[-1].message == "Message 14"


@pytest.mark.asyncio
async def test_on_plan_start(feedback_manager, sample_plan):
    """Test handling plan start event."""
    await feedback_manager.on_plan_start(sample_plan)

    assert feedback_manager._current_plan == sample_plan
    assert feedback_manager._completed_steps == 0
    assert feedback_manager._total_steps == 3
    assert feedback_manager._start_time is not None

    # Check message was added
    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.INFO
    assert "開始します" in message.message


@pytest.mark.asyncio
async def test_on_step_start(feedback_manager, sample_step):
    """Test handling step start event."""
    await feedback_manager.on_step_start(sample_step)

    # Check metrics were created
    assert "test_step" in feedback_manager.metrics
    metrics = feedback_manager.metrics["test_step"]
    assert metrics.step_id == "test_step"
    assert metrics.start_time is not None

    # Check message was added
    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.INFO
    assert "実行中" in message.message


@pytest.mark.asyncio
async def test_on_step_complete_success(feedback_manager, sample_step):
    """Test handling successful step completion."""
    # Start the step first
    await feedback_manager.on_step_start(sample_step)

    result = ExecutionResult(
        step_id="test_step",
        status=StepStatus.COMPLETED,
        result="success",
    )

    await feedback_manager.on_step_complete(sample_step, result)

    # Check metrics were updated
    metrics = feedback_manager.metrics["test_step"]
    assert metrics.end_time is not None
    assert metrics.duration is not None
    assert metrics.duration > 0

    # Check message was added
    messages = list(feedback_manager.messages)
    assert len(messages) == 2  # start + complete
    complete_message = messages[-1]
    assert complete_message.level == FeedbackLevel.SUCCESS
    assert "完了しました" in complete_message.message


@pytest.mark.asyncio
async def test_on_step_complete_failure(feedback_manager, sample_step):
    """Test handling failed step completion."""
    result = ExecutionResult(
        step_id="test_step",
        status=StepStatus.FAILED,
        error=ValueError("Test error"),
    )

    await feedback_manager.on_step_complete(sample_step, result)

    # Check error count
    metrics = feedback_manager.metrics.get("test_step")
    if metrics:
        assert metrics.error_count == 1

    # Check message was added
    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.ERROR
    assert "失敗しました" in message.message


@pytest.mark.asyncio
async def test_on_step_complete_skipped(feedback_manager, sample_step):
    """Test handling skipped step completion."""
    result = ExecutionResult(
        step_id="test_step",
        status=StepStatus.SKIPPED,
    )

    await feedback_manager.on_step_complete(sample_step, result)

    # Check message was added
    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.WARNING
    assert "スキップしました" in message.message


@pytest.mark.asyncio
async def test_on_plan_complete(feedback_manager, sample_plan):
    """Test handling plan completion."""
    # Simulate plan execution
    await feedback_manager.on_plan_start(sample_plan)

    # Mark some steps as completed/failed
    sample_plan.steps[0].status = StepStatus.COMPLETED
    sample_plan.steps[1].status = StepStatus.COMPLETED
    sample_plan.steps[2].status = StepStatus.FAILED

    await feedback_manager.on_plan_complete(sample_plan)

    # Check final message
    messages = list(feedback_manager.messages)
    complete_message = messages[-1]
    assert complete_message.level == FeedbackLevel.INFO
    assert "完了しました" in complete_message.message

    # Check details
    details = complete_message.details
    assert details["successful_steps"] == 2
    assert details["failed_steps"] == 1
    assert details["total_steps"] == 3
    assert details["total_duration"] > 0


@pytest.mark.asyncio
async def test_on_error(feedback_manager, sample_step):
    """Test handling error event."""
    error = ValueError("Test error")

    await feedback_manager.on_error(sample_step, error)

    # Check message was added
    assert len(feedback_manager.messages) == 1
    message = feedback_manager.messages[0]
    assert message.level == FeedbackLevel.ERROR
    assert "エラーが発生しました" in message.message
    assert message.details["error_type"] == "ValueError"


def test_get_progress_summary_idle(feedback_manager):
    """Test getting progress summary when idle."""
    summary = feedback_manager.get_progress_summary()
    assert summary["status"] == "idle"


@pytest.mark.asyncio
async def test_get_progress_summary_active(feedback_manager, sample_plan):
    """Test getting progress summary during execution."""
    await feedback_manager.on_plan_start(sample_plan)
    feedback_manager._completed_steps = 1

    summary = feedback_manager.get_progress_summary()

    assert summary["plan_name"] == "Test Plan"
    assert summary["completed_steps"] == 1
    assert summary["total_steps"] == 3
    assert summary["percentage"] == pytest.approx(33.33, rel=0.1)
    assert summary["elapsed_time"] > 0
    assert "recent_messages" in summary


def test_get_recent_messages(feedback_manager):
    """Test getting recent messages."""
    # Add various messages
    feedback_manager.add_message(FeedbackLevel.INFO, "Info 1")
    feedback_manager.add_message(FeedbackLevel.ERROR, "Error 1")
    feedback_manager.add_message(FeedbackLevel.INFO, "Info 2")
    feedback_manager.add_message(FeedbackLevel.WARNING, "Warning 1")

    # Get all recent messages
    recent = feedback_manager.get_recent_messages(count=3)
    assert len(recent) == 3
    assert recent[-1].message == "Warning 1"

    # Get filtered messages
    errors = feedback_manager.get_recent_messages(count=10, level=FeedbackLevel.ERROR)
    assert len(errors) == 1
    assert errors[0].message == "Error 1"


def test_clear_history(feedback_manager):
    """Test clearing history."""
    # Add some data
    feedback_manager.add_message(FeedbackLevel.INFO, "Test")
    feedback_manager.metrics["step1"] = StepMetrics(step_id="step1")

    # Clear history
    feedback_manager.clear_history()

    assert len(feedback_manager.messages) == 0
    assert len(feedback_manager.metrics) == 0


def test_calculate_avg_step_duration(feedback_manager):
    """Test calculating average step duration."""
    # Add metrics with durations
    feedback_manager.metrics["step1"] = StepMetrics(
        step_id="step1", duration=5.0
    )
    feedback_manager.metrics["step2"] = StepMetrics(
        step_id="step2", duration=10.0
    )
    feedback_manager.metrics["step3"] = StepMetrics(
        step_id="step3", duration=None  # No duration
    )

    avg_duration = feedback_manager._calculate_avg_step_duration()
    assert avg_duration == 7.5  # (5.0 + 10.0) / 2


def test_estimate_remaining_time(feedback_manager):
    """Test estimating remaining time."""
    feedback_manager._total_steps = 5
    feedback_manager._completed_steps = 2

    # With average duration
    remaining = feedback_manager._estimate_remaining_time(3.0)
    assert remaining == 9.0  # 3 remaining steps * 3.0 avg duration

    # With zero average duration
    remaining = feedback_manager._estimate_remaining_time(0.0)
    assert remaining == 0.0