"""Extended tests for CLI commands to improve coverage."""

from unittest.mock import MagicMock, patch

from app.cli.base import CommandContext
from app.cli.commands import (
    AuditCommand,
    CollectCommand,
    ExplainCommand,
    InitCommand,
    ReportCommand,
)


class TestInitCommandExtended:
    """Extended tests for InitCommand."""

    def test_name_property(self):
        """Test name property."""
        cmd = InitCommand()
        assert cmd.name == "init"

    def test_description_property(self):
        """Test description property."""
        cmd = InitCommand()
        assert "Initialize Paddi" in cmd.description

    @patch("app.cli.commands.Path")
    @patch("app.cli.commands.AuditCommand")
    def test_execute_skip_run(self, mock_audit_class, mock_path):  # pylint: disable=unused-argument
        """Test execute with skip_run=True."""
        # Setup
        cmd = InitCommand()
        context = CommandContext(skip_run=True)
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        # Execute
        cmd.execute(context)

        # Assert directories created
        assert mock_path.call_count >= 2  # data and output dirs

        # Assert audit command NOT called
        mock_audit_class.assert_not_called()

    @patch("app.cli.commands.Path")
    @patch("app.cli.commands.AuditCommand")
    @patch("app.cli.commands.json")
    def test_execute_creates_sample_data(
        self, mock_json, mock_audit_class, mock_path
    ):  # pylint: disable=unused-argument
        """Test execute creates sample data when not exists."""
        # Setup
        cmd = InitCommand()
        context = CommandContext(skip_run=True)

        # Mock path for directories
        mock_data_path = MagicMock()
        mock_output_path = MagicMock()
        mock_sample_path = MagicMock()
        mock_sample_path.exists.return_value = False  # Sample doesn't exist

        def path_side_effect(path_str):
            if path_str == "data":
                return mock_data_path
            if path_str == "output":
                return mock_output_path
            if path_str == "data/sample_collected.json":
                return mock_sample_path
            return MagicMock()

        mock_path.side_effect = path_side_effect

        # Execute
        cmd.execute(context)

        # Assert sample file was written
        mock_sample_path.write_text.assert_called_once()
        mock_json.dumps.assert_called_once()

        # Check sample data structure
        sample_data = mock_json.dumps.call_args[0][0]
        assert "project_id" in sample_data
        assert "iam_policies" in sample_data
        assert "scc_findings" in sample_data


class TestCollectCommandExtended:
    """Extended tests for CollectCommand."""

    def test_properties(self):
        """Test command properties."""
        cmd = CollectCommand()
        assert cmd.name == "collect"
        assert "Collect cloud configuration" in cmd.description

    @patch("app.cli.commands.collector_main")
    def test_execute_with_all_params(self, mock_collector_main):
        """Test execute with all parameters."""
        cmd = CollectCommand()
        context = CommandContext(
            project_id="test-project",
            organization_id="test-org",
            use_mock=False,
            collect_all=True,
            verbose=True,
        )

        cmd.execute(context)

        mock_collector_main.assert_called_once_with(
            project_id="test-project",
            organization_id="test-org",
            use_mock=False,
            collect_all=True,
            verbose=True,
        )


class TestExplainCommandExtended:
    """Extended tests for ExplainCommand."""

    def test_properties(self):
        """Test command properties."""
        cmd = ExplainCommand()
        assert cmd.name == "explain"
        assert "Analyze security risks" in cmd.description

    @patch("app.cli.commands.explainer_main")
    def test_execute_with_ai_params(self, mock_explainer_main):
        """Test execute with AI provider parameters."""
        cmd = ExplainCommand()
        context = CommandContext(
            project_id="test-project",
            location="us-west1",
            use_mock=False,
            ai_provider="ollama",
            ollama_model="llama3",
            ollama_endpoint="http://localhost:11434",
        )

        cmd.execute(context)

        mock_explainer_main.assert_called_once_with(
            project_id="test-project",
            location="us-west1",
            use_mock=False,
            ai_provider="ollama",
            ollama_model="llama3",
            ollama_endpoint="http://localhost:11434",
        )


class TestReportCommandExtended:
    """Extended tests for ReportCommand."""

    def test_properties(self):
        """Test command properties."""
        cmd = ReportCommand()
        assert cmd.name == "report"
        assert "Generate security audit report" in cmd.description

    @patch("app.cli.commands.reporter_main")
    def test_execute_custom_output_dir(self, mock_reporter_main):
        """Test execute with custom output directory."""
        cmd = ReportCommand()
        context = CommandContext(output_dir="custom_output")

        cmd.execute(context)

        mock_reporter_main.assert_called_once_with(output_dir="custom_output")


class TestAuditCommandExtended:
    """Extended tests for AuditCommand."""

    def test_properties(self):
        """Test command properties."""
        cmd = AuditCommand()
        assert cmd.name == "audit"
        assert "complete audit pipeline" in cmd.description

    @patch("app.cli.commands.CollectCommand")
    @patch("app.cli.commands.ExplainCommand")
    @patch("app.cli.commands.ReportCommand")
    @patch("app.cli.commands.logger")
    def test_execute_runs_all_steps(
        self, mock_logger, mock_report_class, mock_explain_class, mock_collect_class
    ):
        """Test execute runs all three steps."""
        # Setup mocks
        mock_collect = MagicMock()
        mock_explain = MagicMock()
        mock_report = MagicMock()

        mock_collect_class.return_value = mock_collect
        mock_explain_class.return_value = mock_explain
        mock_report_class.return_value = mock_report

        # Execute
        cmd = AuditCommand()
        context = CommandContext(project_id="test-project", output_dir="test_output")
        cmd.execute(context)

        # Verify all commands were instantiated
        mock_collect_class.assert_called_once()
        mock_explain_class.assert_called_once()
        mock_report_class.assert_called_once()

        # Verify all commands were executed with same context
        mock_collect.execute.assert_called_once_with(context)
        mock_explain.execute.assert_called_once_with(context)
        mock_report.execute.assert_called_once_with(context)

        # Verify completion message
        mock_logger.info.assert_called()
        final_log_call = mock_logger.info.call_args_list[-1]
        assert "Audit complete" in final_log_call[0][0]
        # Check if output_dir is passed as parameter
        assert final_log_call[0][1] == "test_output"
