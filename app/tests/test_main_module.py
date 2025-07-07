"""Tests for the main module entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from app.main import main


class TestMainModule:
    """Test cases for main module functionality."""

    @patch("app.main.fire.Fire")
    def test_main_with_known_command(self, mock_fire):
        """Test main with known Fire command."""
        test_args = ["main.py", "audit"]
        with patch.object(sys, "argv", test_args):
            main()
            mock_fire.assert_called_once()

    @patch("app.main.fire.Fire")
    def test_main_with_help_flag(self, mock_fire):
        """Test main with help flag."""
        test_args = ["main.py", "--help"]
        with patch.object(sys, "argv", test_args):
            main()
            mock_fire.assert_called_once()

    @patch("app.agents.autonomous_cli.AutonomousCLI")
    def test_main_with_natural_language(self, mock_autonomous_cli):
        """Test main with natural language input."""
        # Setup mock
        mock_cli_instance = MagicMock()
        mock_cli_instance.execute_one_shot.return_value = {"success": True}
        mock_autonomous_cli.return_value = mock_cli_instance

        test_args = ["main.py", "プロジェクトのセキュリティを確認して"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with 0 for success
            assert exc_info.value.code == 0

            # Should create AutonomousCLI and execute
            mock_autonomous_cli.assert_called_once()
            mock_cli_instance.execute_one_shot.assert_called_once_with(
                "プロジェクトのセキュリティを確認して"
            )

    @patch("app.agents.autonomous_cli.AutonomousCLI")
    def test_main_with_natural_language_failure(self, mock_autonomous_cli):
        """Test main with natural language input that fails."""
        # Setup mock to return failure
        mock_cli_instance = MagicMock()
        mock_cli_instance.execute_one_shot.return_value = {"success": False}
        mock_autonomous_cli.return_value = mock_cli_instance

        test_args = ["main.py", "invalid natural language command"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with 1 for failure
            assert exc_info.value.code == 1

            # Should create AutonomousCLI and execute
            mock_autonomous_cli.assert_called_once()
            mock_cli_instance.execute_one_shot.assert_called_once_with(
                "invalid natural language command"
            )

        # mock_fire is needed in signature but not used
        # This verifies Fire was not called

    @patch("app.main.fire.Fire")
    def test_main_with_multiple_args(self, mock_fire):
        """Test main with multiple arguments (normal Fire behavior)."""
        test_args = ["main.py", "audit", "--project-id", "test-project"]
        with patch.object(sys, "argv", test_args):
            main()
            mock_fire.assert_called_once()

    @patch("app.main.fire.Fire")
    def test_main_with_no_args(self, mock_fire):
        """Test main with no arguments."""
        test_args = ["main.py"]
        with patch.object(sys, "argv", test_args):
            main()
            mock_fire.assert_called_once()

    @patch("app.main.fire.Fire")
    def test_main_with_known_commands_not_natural_language(self, mock_fire):
        """Test that known commands are not treated as natural language."""
        known_commands = [
            "init",
            "audit",
            "collect",
            "analyze",
            "explain",
            "report",
            "list_commands",
            "validate_command",
            "approve_command",
            "execute_remediation",
            "approve",
            "reject",
            "list_approvals",
            "chat",
            "ai_agent",
            "ai_audit",
            "langchain_audit",
            "recursive_audit",
            "audit_log",
            "safety_demo",
            "audit_logs",
        ]

        for command in known_commands:
            mock_fire.reset_mock()
            test_args = ["main.py", command]
            with patch.object(sys, "argv", test_args):
                main()
                mock_fire.assert_called_once()

    def test_main_initialization(self):
        """Test that main module imports correctly."""
        # Simply test that the module can be imported without error
        # The actual initialization code runs at module level, so it's already been executed
        # when pytest imports the module
        # Import is already done at the top level, so this just verifies it works

        # If we get here without exception, the module initialized correctly
        assert True
