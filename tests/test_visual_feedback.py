"""Tests for visual feedback module."""

import pytest
import sys
import time
from unittest.mock import MagicMock, patch

from app.execution.visual_feedback import (
    SpinnerFeedback,
    Theme,
    VisualFeedback,
)
from app.execution.progressive_executor import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    StepStatus,
)


@pytest.fixture
def theme():
    """Create a Theme instance."""
    return Theme()


@pytest.fixture
def visual_feedback():
    """Create a VisualFeedback instance."""
    return VisualFeedback(show_time=True, show_memory=False, compact_mode=False)


@pytest.fixture
def compact_feedback():
    """Create a compact VisualFeedback instance."""
    return VisualFeedback(show_time=False, show_memory=False, compact_mode=True)


@pytest.fixture
def sample_step():
    """Create a sample execution step."""
    return ExecutionStep(
        id="test_step",
        description="Test step description",
        execute=lambda: "result",
        estimated_duration=10.0,
    )


@pytest.fixture
def sample_plan():
    """Create a sample execution plan."""
    steps = [
        ExecutionStep(
            id=f"step{i}",
            description=f"Step {i} description",
            execute=lambda: f"result{i}",
        )
        for i in range(3)
    ]
    return ExecutionPlan(
        steps=steps,
        name="Test Plan",
        description="Test execution plan description",
    )


def test_theme_initialization(theme):
    """Test Theme initialization with default values."""
    assert theme.progress_fill == "━"
    assert theme.progress_empty == "━"
    assert theme.success == "✅"
    assert theme.error == "❌"
    assert theme.color_success == "\033[92m"


def test_visual_feedback_initialization(visual_feedback):
    """Test VisualFeedback initialization."""
    assert visual_feedback.show_time is True
    assert visual_feedback.show_memory is False
    assert visual_feedback.compact_mode is False
    assert visual_feedback._terminal_width > 0


@patch("os.get_terminal_size")
def test_get_terminal_width(mock_terminal_size):
    """Test getting terminal width."""
    mock_terminal_size.return_value.columns = 120
    vf = VisualFeedback()
    assert vf._terminal_width == 120

    # Test fallback when terminal size unavailable
    mock_terminal_size.side_effect = Exception()
    vf = VisualFeedback()
    assert vf._terminal_width == 80


@patch("sys.stdout.isatty")
def test_colorize(mock_isatty, visual_feedback):
    """Test text colorization."""
    # When terminal supports colors
    mock_isatty.return_value = True
    colored = visual_feedback._colorize("test", visual_feedback.theme.color_success)
    assert colored == f"{visual_feedback.theme.color_success}test{visual_feedback.theme.color_reset}"

    # When terminal doesn't support colors
    mock_isatty.return_value = False
    colored = visual_feedback._colorize("test", visual_feedback.theme.color_success)
    assert colored == "test"


def test_truncate_text(visual_feedback):
    """Test text truncation."""
    # Text shorter than max width
    text = "short text"
    result = visual_feedback._truncate_text(text, 20)
    assert result == text

    # Text longer than max width
    text = "This is a very long text that needs truncation"
    result = visual_feedback._truncate_text(text, 20)
    assert result == "This is a very lon..."
    assert len(result) == 20


def test_render_progress_bar(visual_feedback):
    """Test progress bar rendering."""
    # 0% progress
    bar = visual_feedback._render_progress_bar(0, 10, width=10)
    assert "0%" in bar

    # 50% progress
    bar = visual_feedback._render_progress_bar(5, 10, width=10)
    assert "50%" in bar

    # 100% progress
    bar = visual_feedback._render_progress_bar(10, 10, width=10)
    assert "100%" in bar

    # Empty total (avoid division by zero)
    bar = visual_feedback._render_progress_bar(0, 0, width=10)
    assert "0%" in bar


def test_render_step_status(visual_feedback, sample_step):
    """Test step status rendering."""
    # Test different statuses
    sample_step.status = StepStatus.PENDING
    status = visual_feedback._render_step_status(sample_step)
    assert visual_feedback.theme.pending in status

    sample_step.status = StepStatus.RUNNING
    status = visual_feedback._render_step_status(sample_step)
    assert visual_feedback.theme.running in status

    sample_step.status = StepStatus.COMPLETED
    status = visual_feedback._render_step_status(sample_step)
    assert visual_feedback.theme.success in status

    sample_step.status = StepStatus.FAILED
    status = visual_feedback._render_step_status(sample_step)
    assert visual_feedback.theme.error in status


def test_render_time_elapsed(visual_feedback):
    """Test elapsed time rendering."""
    # Seconds
    assert visual_feedback._render_time_elapsed(5.5) == "5.5秒"
    assert visual_feedback._render_time_elapsed(59.9) == "59.9秒"

    # Minutes
    assert visual_feedback._render_time_elapsed(60) == "1分0秒"
    assert visual_feedback._render_time_elapsed(125) == "2分5秒"

    # Hours
    assert visual_feedback._render_time_elapsed(3600) == "1時間0分"
    assert visual_feedback._render_time_elapsed(3665) == "1時間1分"


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_plan_start(mock_print, visual_feedback, sample_plan):
    """Test handling plan start event."""
    await visual_feedback.on_plan_start(sample_plan)

    assert visual_feedback._current_plan == sample_plan
    assert visual_feedback._start_time is not None

    # Verify output
    assert mock_print.called
    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "Test Plan" in printed_text
    assert "Test execution plan description" in printed_text


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_plan_start_compact(mock_print, compact_feedback, sample_plan):
    """Test plan start in compact mode."""
    await compact_feedback.on_plan_start(sample_plan)

    # In compact mode, less output
    assert mock_print.call_count == 0 or mock_print.call_count < 3


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_step_start(mock_print, visual_feedback, sample_step):
    """Test handling step start event."""
    await visual_feedback.on_step_start(sample_step)

    # Verify output
    assert mock_print.called
    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "Test step description" in printed_text


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_step_complete_success(mock_print, visual_feedback, sample_step):
    """Test handling successful step completion."""
    sample_step.status = StepStatus.COMPLETED
    result = ExecutionResult(
        step_id="test_step",
        status=StepStatus.COMPLETED,
        result="success",
    )

    await visual_feedback.on_step_complete(sample_step, result)

    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "完了" in printed_text


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_step_complete_failure(mock_print, visual_feedback, sample_step):
    """Test handling failed step completion."""
    sample_step.status = StepStatus.FAILED
    result = ExecutionResult(
        step_id="test_step",
        status=StepStatus.FAILED,
        error=ValueError("Test error"),
    )

    await visual_feedback.on_step_complete(sample_step, result)

    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "失敗" in printed_text
    assert "Test error" in printed_text


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_plan_complete(mock_print, visual_feedback, sample_plan):
    """Test handling plan completion."""
    # Set up plan state
    visual_feedback._current_plan = sample_plan
    visual_feedback._start_time = time.time() - 10  # 10 seconds ago

    # Mark steps as completed/failed
    sample_plan.steps[0].status = StepStatus.COMPLETED
    sample_plan.steps[1].status = StepStatus.COMPLETED
    sample_plan.steps[2].status = StepStatus.FAILED

    await visual_feedback.on_plan_complete(sample_plan)

    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "実行完了" in printed_text
    assert "エラーあり" in printed_text
    assert "2/3" in printed_text  # 2 out of 3 completed


@pytest.mark.asyncio
@patch("builtins.print")
async def test_on_error(mock_print, visual_feedback, sample_step):
    """Test handling error event."""
    error = ValueError("Test error message")

    await visual_feedback.on_error(sample_step, error)

    printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "エラー" in printed_text
    assert "ValueError" in printed_text
    assert "Test error message" in printed_text


def test_render_progress_summary(visual_feedback):
    """Test rendering progress summary."""
    progress = {
        "plan_name": "Test Plan",
        "completed_steps": 5,
        "total_steps": 10,
        "elapsed_time": 120.5,
        "estimated_remaining": 120.5,
        "current_step": "Processing data",
    }

    summary = visual_feedback.render_progress_summary(progress)

    assert "Test Plan" in summary
    assert "5/10" in summary
    assert "経過: 2分0秒" in summary
    assert "残り: 2分0秒" in summary
    assert "Processing data" in summary


def test_spinner_feedback_initialization():
    """Test SpinnerFeedback initialization."""
    spinner = SpinnerFeedback("処理中")
    assert spinner.message == "処理中"
    assert len(spinner.chars) == 10
    assert spinner.current == 0
    assert not spinner._running


@patch("sys.stdout.isatty")
@patch("builtins.print")
def test_spinner_feedback_animation(mock_print, mock_isatty):
    """Test spinner animation."""
    mock_isatty.return_value = True
    spinner = SpinnerFeedback("Loading")

    # Start spinner
    spinner.start()
    assert spinner._running

    # Give it a moment to animate
    time.sleep(0.2)

    # Stop spinner
    spinner.stop()
    assert not spinner._running

    # Verify animation occurred
    assert mock_print.called