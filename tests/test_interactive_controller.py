"""Tests for interactive controller module."""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

from app.execution.interactive_controller import (
    DialogController,
    InteractiveController,
)
from app.execution.progressive_executor import ExecutionControl


@pytest.fixture
def controller():
    """Create an InteractiveController instance."""
    return InteractiveController(auto_mode=False)


@pytest.fixture
def auto_controller():
    """Create an InteractiveController in auto mode."""
    return InteractiveController(auto_mode=True)


@pytest.fixture
def dialog_controller():
    """Create a DialogController instance."""
    return DialogController(auto_mode=False)


def test_controller_initialization(controller):
    """Test InteractiveController initialization."""
    assert not controller.auto_mode
    assert controller._is_interactive


def test_auto_mode_initialization(auto_controller):
    """Test auto mode initialization."""
    assert auto_controller.auto_mode


@pytest.mark.asyncio
async def test_get_confirmation_auto_mode(auto_controller):
    """Test confirmation in auto mode always returns True."""
    result = await auto_controller.get_confirmation("Proceed?")
    assert result is True


@pytest.mark.asyncio
async def test_get_confirmation_non_interactive():
    """Test confirmation in non-interactive mode."""
    with patch("sys.stdin.isatty", return_value=False):
        controller = InteractiveController(auto_mode=False)
        result = await controller.get_confirmation("Proceed?")
        assert result is True


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_get_confirmation_interactive(mock_loop, controller):
    """Test interactive confirmation."""
    # Mock user input
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "y"
    )

    result = await controller.get_confirmation("Proceed?")
    assert result is True

    # Test "no" response
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "n"
    )
    result = await controller.get_confirmation("Proceed?")
    assert result is False


@pytest.mark.asyncio
async def test_get_choice_auto_mode(auto_controller):
    """Test choice in auto mode returns first option."""
    options = ["option1", "option2", "option3"]
    result = await auto_controller.get_choice("Choose:", options)
    assert result == "option1"


@pytest.mark.asyncio
async def test_get_choice_empty_options(auto_controller):
    """Test choice with empty options."""
    result = await auto_controller.get_choice("Choose:", [])
    assert result is None


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_get_choice_by_number(mock_loop, controller):
    """Test choosing by number."""
    options = ["first", "second", "third"]
    
    # Mock user selecting option 2
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "2"
    )

    with patch("builtins.print"):  # Suppress print output
        result = await controller.get_choice("Choose:", options)
    
    assert result == "second"


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_get_choice_by_text(mock_loop, controller):
    """Test choosing by text."""
    options = ["start", "stop", "restart"]
    
    # Mock user typing "stop"
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "stop"
    )

    with patch("builtins.print"):  # Suppress print output
        result = await controller.get_choice("Choose:", options)
    
    assert result == "stop"


@pytest.mark.asyncio
async def test_get_control_input_auto_mode(auto_controller):
    """Test control input in auto mode always returns CONTINUE."""
    result = await auto_controller.get_control_input()
    assert result == ExecutionControl.CONTINUE


@pytest.mark.asyncio
async def test_get_control_input_non_interactive():
    """Test control input in non-interactive mode."""
    with patch("sys.stdin.isatty", return_value=False):
        controller = InteractiveController(auto_mode=False)
        result = await controller.get_control_input()
        assert result == ExecutionControl.CONTINUE


def test_parse_control_input(controller):
    """Test parsing control input strings."""
    # Test single letter shortcuts
    assert controller._parse_control_input("p") == ExecutionControl.PAUSE
    assert controller._parse_control_input("s") == ExecutionControl.SKIP
    assert controller._parse_control_input("a") == ExecutionControl.ABORT
    assert controller._parse_control_input("d") == ExecutionControl.DETAILS
    assert controller._parse_control_input("r") == ExecutionControl.RETRY

    # Test full words
    assert controller._parse_control_input("pause") == ExecutionControl.PAUSE
    assert controller._parse_control_input("skip") == ExecutionControl.SKIP
    assert controller._parse_control_input("abort") == ExecutionControl.ABORT

    # Test case insensitive
    assert controller._parse_control_input("PAUSE") == ExecutionControl.PAUSE
    assert controller._parse_control_input("Skip") == ExecutionControl.SKIP

    # Test invalid input
    assert controller._parse_control_input("invalid") == ExecutionControl.CONTINUE
    assert controller._parse_control_input("") == ExecutionControl.CONTINUE


def test_show_controls(controller):
    """Test showing controls."""
    with patch("builtins.print") as mock_print:
        controller.show_controls()
        
        # Verify controls were printed
        assert mock_print.call_count > 0
        printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        assert "一時停止" in printed_text
        assert "スキップ" in printed_text
        assert "中止" in printed_text


def test_show_controls_auto_mode(auto_controller):
    """Test controls not shown in auto mode."""
    with patch("builtins.print") as mock_print:
        auto_controller.show_controls()
        mock_print.assert_not_called()


# DialogController tests

def test_dialog_controller_initialization(dialog_controller):
    """Test DialogController initialization."""
    assert not dialog_controller.auto_mode
    assert dialog_controller.context == {}


@pytest.mark.asyncio
async def test_show_step_details_auto_mode():
    """Test step details in auto mode returns None."""
    dialog = DialogController(auto_mode=True)
    result = await dialog.show_step_details({"description": "Test"})
    assert result is None


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_show_step_details(mock_loop, dialog_controller):
    """Test showing step details."""
    step_info = {
        "description": "Test step",
        "duration": "5 seconds",
        "status": "pending",
    }

    # Mock user selecting "続行"
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "1"
    )

    with patch("builtins.print"):  # Suppress print output
        result = await dialog_controller.show_step_details(step_info)
    
    assert result == "続行"


@pytest.mark.asyncio
async def test_get_settings_update_auto_mode():
    """Test settings update in auto mode returns unchanged."""
    dialog = DialogController(auto_mode=True)
    current = {"key1": "value1", "key2": "value2"}
    result = await dialog.get_settings_update(current)
    assert result == current


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_get_settings_update(mock_loop, dialog_controller):
    """Test updating settings."""
    current_settings = {"timeout": "30", "retries": "3"}

    # Mock user input sequence: change timeout, then exit
    inputs = iter(["timeout", "60", ""])
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: next(inputs)
    )

    with patch("builtins.print"):  # Suppress print output
        result = await dialog_controller.get_settings_update(current_settings)
    
    assert result["timeout"] == "60"
    assert result["retries"] == "3"  # Unchanged


@pytest.mark.asyncio
async def test_show_error_dialog_auto_mode():
    """Test error dialog in auto mode returns retry."""
    dialog = DialogController(auto_mode=True)
    error = ValueError("Test error")
    result = await dialog.show_error_dialog(error, {})
    assert result == "retry"


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
async def test_show_error_dialog(mock_loop, dialog_controller):
    """Test showing error dialog."""
    error = ValueError("Test error")
    context = {"step": "test_step", "attempt": 1}

    # Mock user selecting "スキップ" (option 2)
    mock_loop.return_value.run_in_executor = asyncio.coroutine(
        lambda *args: "2"
    )

    with patch("builtins.print"):  # Suppress print output
        result = await dialog_controller.show_error_dialog(error, context)
    
    assert result == "スキップ"