"""Tests for CLI command pattern implementation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.cli.base import Command, CommandContext
from app.cli.commands import (
    AuditCommand,
    CollectCommand,
    ExplainCommand,
    ReportCommand,
    InitCommand
)


class TestCommandContext:
    """Tests for CommandContext."""

    def test_context_creation(self):
        """Test creating command context."""
        context = CommandContext(
            project_id="test-project",
            use_mock=True,
            output_dir="output"
        )
        
        assert context.project_id == "test-project"
        assert context.use_mock is True
        assert context.output_dir == "output"

    def test_context_defaults(self):
        """Test context with default values."""
        context = CommandContext()
        
        assert context.project_id == "example-project-123"
        assert context.use_mock is True
        assert context.output_dir == "output"


class TestCommand:
    """Tests for base Command class."""

    def test_command_abstract_methods(self):
        """Test that Command is abstract."""
        with pytest.raises(TypeError):
            Command()  # Can't instantiate abstract class

    def test_command_implementation(self):
        """Test concrete command implementation."""
        class TestCommand(Command):
            def execute(self, context: CommandContext) -> None:
                pass
            
            @property
            def name(self) -> str:
                return "test"
            
            @property
            def description(self) -> str:
                return "Test command"
        
        cmd = TestCommand()
        assert cmd.name == "test"
        assert cmd.description == "Test command"


class TestAuditCommand:
    """Tests for AuditCommand."""

    @patch('app.cli.commands.CollectCommand')
    @patch('app.cli.commands.ExplainCommand')
    @patch('app.cli.commands.ReportCommand')
    def test_audit_executes_all_steps(self, mock_report, mock_explain, mock_collect):
        """Test that audit command executes all steps."""
        context = CommandContext(use_mock=True)
        cmd = AuditCommand()
        
        # Configure mocks
        mock_collect_instance = Mock()
        mock_explain_instance = Mock()
        mock_report_instance = Mock()
        
        mock_collect.return_value = mock_collect_instance
        mock_explain.return_value = mock_explain_instance
        mock_report.return_value = mock_report_instance
        
        # Execute
        cmd.execute(context)
        
        # Verify all commands were created and executed
        mock_collect_instance.execute.assert_called_once_with(context)
        mock_explain_instance.execute.assert_called_once_with(context)
        mock_report_instance.execute.assert_called_once_with(context)


class TestCollectCommand:
    """Tests for CollectCommand."""

    @patch('app.cli.commands.collector_main')
    def test_collect_calls_collector(self, mock_collector):
        """Test that collect command calls collector."""
        context = CommandContext(
            project_id="test-project",
            use_mock=True
        )
        cmd = CollectCommand()
        
        cmd.execute(context)
        
        mock_collector.assert_called_once_with(
            project_id="test-project",
            organization_id=None,
            use_mock=True,
            collect_all=True,
            verbose=False
        )


class TestExplainCommand:
    """Tests for ExplainCommand."""

    @patch('app.cli.commands.explainer_main')
    def test_explain_calls_explainer(self, mock_explainer):
        """Test that explain command calls explainer."""
        context = CommandContext(
            project_id="test-project",
            use_mock=True,
            ai_provider="gemini"
        )
        cmd = ExplainCommand()
        
        cmd.execute(context)
        
        mock_explainer.assert_called_once_with(
            project_id="test-project",
            location="us-central1",
            use_mock=True,
            verbose=False,
            ai_provider="gemini",
            ollama_model=None,
            ollama_endpoint=None
        )


class TestReportCommand:
    """Tests for ReportCommand."""

    @patch('app.cli.commands.reporter_main')
    def test_report_calls_reporter(self, mock_reporter):
        """Test that report command calls reporter."""
        context = CommandContext(
            output_dir="test-output",
            verbose=True
        )
        cmd = ReportCommand()
        
        cmd.execute(context)
        
        mock_reporter.assert_called_once_with(
            output_dir="test-output",
            verbose=True
        )


class TestInitCommand:
    """Tests for InitCommand."""

    @patch('app.cli.commands.Path.mkdir')
    @patch('app.cli.commands.Path.exists')
    @patch('app.cli.commands.Path.write_text')
    @patch('app.cli.commands.AuditCommand')
    def test_init_creates_sample_data(self, mock_audit, mock_write, mock_exists, mock_mkdir):
        """Test that init command creates sample data."""
        mock_exists.return_value = False
        context = CommandContext(skip_run=True)
        cmd = InitCommand()
        
        cmd.execute(context)
        
        # Verify directories were created
        assert mock_mkdir.call_count >= 2  # data and output dirs
        
        # Verify sample data was written
        mock_write.assert_called_once()
        
        # Verify audit was not run (skip_run=True)
        mock_audit.assert_not_called()

    @patch('app.cli.commands.Path.mkdir')
    @patch('app.cli.commands.Path.exists')
    @patch('app.cli.commands.Path.write_text')
    @patch('app.cli.commands.AuditCommand')
    def test_init_runs_audit_by_default(self, mock_audit, mock_write, mock_exists, mock_mkdir):
        """Test that init command runs audit by default."""
        mock_exists.return_value = True  # Sample data already exists
        mock_audit_instance = Mock()
        mock_audit.return_value = mock_audit_instance
        
        context = CommandContext(skip_run=False)
        cmd = InitCommand()
        
        cmd.execute(context)
        
        # Verify audit was executed
        mock_audit_instance.execute.assert_called_once()