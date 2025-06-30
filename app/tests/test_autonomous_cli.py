#!/usr/bin/env python3
"""
Tests for the Autonomous CLI module.
"""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.agents.autonomous_cli import (
    AutonomousCLI,
    ConversationContext,
    NaturalLanguageParser,
    SpecialCommand,
)


class TestNaturalLanguageParser:
    """Test the natural language parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = NaturalLanguageParser()

    def test_parse_audit_command_japanese(self):
        """Test parsing Japanese audit command."""
        command, params = self.parser.parse_command(
            "GCPプロジェクト example-123 のセキュリティを監査して"
        )
        assert command == "audit"
        assert params["project_id"] == "example-123"

    def test_parse_audit_command_english(self):
        """Test parsing English audit command."""
        command, params = self.parser.parse_command(
            "audit security for project test-project"
        )
        assert command == "audit"
        assert params["project_id"] == "test-project"

    def test_parse_collect_command(self):
        """Test parsing collect command."""
        command, params = self.parser.parse_command(
            "プロジェクトの構成情報を収集して"
        )
        assert command == "collect"

    def test_parse_analyze_command(self):
        """Test parsing analyze command."""
        command, params = self.parser.parse_command(
            "セキュリティリスクを分析して"
        )
        assert command == "analyze"

    def test_parse_report_command(self):
        """Test parsing report command."""
        command, params = self.parser.parse_command(
            "監査レポートを作成して"
        )
        assert command == "report"

    def test_parse_unknown_command(self):
        """Test parsing unknown command defaults to ai_agent."""
        command, params = self.parser.parse_command(
            "何か複雑なリクエスト"
        )
        assert command == "ai_agent"

    def test_extract_mock_flag(self):
        """Test extracting mock flag."""
        _, params = self.parser.parse_command(
            "テストデータで監査を実行"
        )
        assert params.get("use_mock") is True

    def test_extract_real_flag(self):
        """Test extracting real data flag."""
        _, params = self.parser.parse_command(
            "実際のデータで監査を実行"
        )
        assert params.get("use_mock") is False


class TestConversationContext:
    """Test the conversation context."""

    def test_initialization(self):
        """Test context initialization."""
        context = ConversationContext(history=[])
        assert context.history == []
        assert context.project_id is None
        assert context.model == "gemini-1.5-flash"
        assert isinstance(context.session_start, datetime)

    def test_with_project_id(self):
        """Test context with project ID."""
        context = ConversationContext(history=[], project_id="test-project")
        assert context.project_id == "test-project"


class TestAutonomousCLI:
    """Test the Autonomous CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = AutonomousCLI()

    def test_initialization(self):
        """Test CLI initialization."""
        assert self.cli.paddi_cli is not None
        assert self.cli.coordinator is not None
        assert self.cli.parser is not None
        assert isinstance(self.cli.context, ConversationContext)

    @patch("app.agents.autonomous_cli.console")
    def test_handle_exit_command(self, mock_console):
        """Test handling exit command."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli._handle_special_command("/exit")
        assert exc_info.value.code == 0

    @patch("app.agents.autonomous_cli.console")
    def test_handle_clear_command(self, mock_console):
        """Test handling clear command."""
        result = self.cli._handle_special_command("/clear")
        assert result is True
        mock_console.clear.assert_called_once()

    @patch("app.agents.autonomous_cli.console")
    def test_handle_help_command(self, mock_console):
        """Test handling help command."""
        result = self.cli._handle_special_command("/help")
        assert result is True
        mock_console.print.assert_called()

    @patch("app.agents.autonomous_cli.console")
    def test_handle_model_command(self, mock_console):
        """Test handling model command."""
        result = self.cli._handle_special_command("/model gemini-pro")
        assert result is True
        assert self.cli.context.model == "gemini-pro"

    @patch("app.agents.autonomous_cli.console")
    def test_handle_model_command_show_current(self, mock_console):
        """Test showing current model."""
        result = self.cli._handle_special_command("/model")
        assert result is True
        mock_console.print.assert_called()

    @patch("app.agents.autonomous_cli.console")
    def test_handle_history_command_empty(self, mock_console):
        """Test handling history command with empty history."""
        result = self.cli._handle_special_command("/history")
        assert result is True
        mock_console.print.assert_called_with("[yellow]会話履歴はありません。[/yellow]")

    @patch("app.agents.autonomous_cli.console")
    def test_handle_history_command_with_entries(self, mock_console):
        """Test handling history command with entries."""
        self.cli.context.history = [
            {"user": "test command", "response": "test response"}
        ]
        result = self.cli._handle_special_command("/history")
        assert result is True
        assert mock_console.print.call_count >= 2

    @patch("app.agents.autonomous_cli.console")
    def test_handle_reset_command(self, mock_console):
        """Test handling reset command."""
        self.cli.context.history = [{"user": "test", "response": "test"}]
        self.cli.context.project_id = "test-project"
        
        result = self.cli._handle_special_command("/reset")
        assert result is True
        assert self.cli.context.history == []
        assert self.cli.context.project_id is None

    def test_execute_paddi_command_audit(self):
        """Test executing audit command."""
        with patch.object(self.cli.paddi_cli, "audit") as mock_audit:
            result = self.cli._execute_paddi_command(
                "audit", {"project_id": "test-project"}
            )
            mock_audit.assert_called_once_with(project_id="test-project")
            assert result["success"] is True
            assert result["command"] == "audit"

    def test_execute_paddi_command_unknown(self):
        """Test executing unknown command."""
        with pytest.raises(ValueError, match="Unknown command"):
            self.cli._execute_paddi_command("unknown", {})

    @patch("app.agents.autonomous_cli.console")
    def test_process_command_success(self, mock_console):
        """Test processing command successfully."""
        with patch.object(self.cli.paddi_cli, "audit"):
            result = self.cli._process_command(
                "GCPプロジェクト test-123 を監査して"
            )
            assert result["success"] is True
            assert len(self.cli.context.history) == 1

    @patch("app.agents.autonomous_cli.console")
    def test_process_command_error(self, mock_console):
        """Test processing command with error."""
        with patch.object(self.cli.paddi_cli, "audit", side_effect=Exception("Test error")):
            result = self.cli._process_command(
                "監査を実行"
            )
            assert result["success"] is False
            assert "error" in result
            assert len(self.cli.context.history) == 1

    def test_format_response_success(self):
        """Test formatting successful response."""
        result = {
            "success": True,
            "message": "テスト成功",
            "summary": "サマリー",
            "report_path": "/path/to/report"
        }
        formatted = self.cli._format_response(result)
        assert "✅" in formatted
        assert "テスト成功" in formatted
        assert "サマリー" in formatted
        assert "/path/to/report" in formatted

    def test_format_response_failure(self):
        """Test formatting failed response."""
        result = {
            "success": False,
            "message": "テスト失敗"
        }
        formatted = self.cli._format_response(result)
        assert "❌" in formatted
        assert "テスト失敗" in formatted

    def test_execute_one_shot(self):
        """Test one-shot execution."""
        with patch.object(self.cli, "_process_command") as mock_process:
            mock_process.return_value = {"success": True}
            result = self.cli.execute_one_shot("test command")
            mock_process.assert_called_once_with("test command", one_shot=True)
            assert result["success"] is True


class TestSpecialCommand:
    """Test special command enum."""

    def test_special_commands(self):
        """Test special command values."""
        assert SpecialCommand.EXIT.value == "/exit"
        assert SpecialCommand.CLEAR.value == "/clear"
        assert SpecialCommand.HELP.value == "/help"
        assert SpecialCommand.MODEL.value == "/model"
        assert SpecialCommand.HISTORY.value == "/history"
        assert SpecialCommand.RESET.value == "/reset"


@patch("sys.argv", ["autonomous_cli.py"])
@patch("app.agents.autonomous_cli.AutonomousCLI")
def test_main_interactive(mock_cli_class):
    """Test main function in interactive mode."""
    from app.agents.autonomous_cli import main
    
    mock_cli = MagicMock()
    mock_cli_class.return_value = mock_cli
    
    main()
    
    mock_cli.start_interactive.assert_called_once()


@patch("sys.argv", ["autonomous_cli.py", "test command"])
@patch("app.agents.autonomous_cli.AutonomousCLI")
def test_main_one_shot_success(mock_cli_class):
    """Test main function in one-shot mode with success."""
    from app.agents.autonomous_cli import main
    
    mock_cli = MagicMock()
    mock_cli.execute_one_shot.return_value = {"success": True}
    mock_cli_class.return_value = mock_cli
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 0
    mock_cli.execute_one_shot.assert_called_once_with("test command")


@patch("sys.argv", ["autonomous_cli.py", "test command"])
@patch("app.agents.autonomous_cli.AutonomousCLI")
def test_main_one_shot_failure(mock_cli_class):
    """Test main function in one-shot mode with failure."""
    from app.agents.autonomous_cli import main
    
    mock_cli = MagicMock()
    mock_cli.execute_one_shot.return_value = {"success": False}
    mock_cli_class.return_value = mock_cli
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


@patch("sys.argv", ["autonomous_cli.py", "--interactive"])
@patch("app.agents.autonomous_cli.AutonomousCLI")
def test_main_interactive_flag(mock_cli_class):
    """Test main function with interactive flag."""
    from app.agents.autonomous_cli import main
    
    mock_cli = MagicMock()
    mock_cli_class.return_value = mock_cli
    
    main()
    
    mock_cli.start_interactive.assert_called_once()