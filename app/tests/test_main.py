"""Tests for the main CLI module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.main import PaddiCLI


class TestPaddiCLI:
    """Test cases for PaddiCLI class."""

    @pytest.fixture
    def cli(self):
        """Create PaddiCLI instance."""
        return PaddiCLI()

    @pytest.fixture
    def setup_test_dirs(self, tmp_path):
        """Setup temporary directories for testing."""
        data_dir = tmp_path / "data"
        output_dir = tmp_path / "output"
        data_dir.mkdir()
        output_dir.mkdir()
        return data_dir, output_dir

    def test_init_creates_directories(self, cli, tmp_path, monkeypatch):
        """Test that init creates necessary directories."""
        monkeypatch.chdir(tmp_path)

        cli.init(skip_run=True)

        assert Path("data").exists()
        assert Path("output").exists()

    def test_init_creates_sample_data(self, cli, tmp_path, monkeypatch):
        """Test that init creates sample data file."""
        monkeypatch.chdir(tmp_path)

        cli.init(skip_run=True)

        sample_data_path = Path("data/sample_collected.json")
        assert sample_data_path.exists()

        # Verify sample data content
        data = json.loads(sample_data_path.read_text(encoding="utf-8"))
        assert data["project_id"] == "example-project-123"
        assert len(data["iam_policies"]) > 0
        assert len(data["scc_findings"]) > 0

    @patch("app.main.collector_main")
    @patch("app.main.explainer_main")
    @patch("app.main.reporter_main")
    def test_init_with_run(
        self, mock_reporter, mock_explainer, mock_collector, cli, tmp_path, monkeypatch
    ):
        """Test that init runs the full pipeline when skip_run=False."""
        monkeypatch.chdir(tmp_path)

        # Create mock data files that would be created by the agents
        Path("data").mkdir()
        Path("data/collected.json").write_text(
            json.dumps({"iam_policies": [], "scc_findings": []}), encoding="utf-8"
        )
        Path("data/explained.json").write_text(json.dumps([]), encoding="utf-8")

        cli.init(skip_run=False)

        # Verify all agents were called
        mock_collector.assert_called_once()
        mock_explainer.assert_called_once()
        mock_reporter.assert_called_once()

    @patch("app.main.collector_main")
    def test_collect_command(self, mock_collector, cli, tmp_path, monkeypatch):
        """Test the collect command."""
        monkeypatch.chdir(tmp_path)
        Path("data").mkdir()

        # Create mock collected data
        Path("data/collected.json").write_text(
            json.dumps(
                {"iam_policies": [{"resource": "test"}], "scc_findings": [{"finding": "test"}]}
            ),
            encoding="utf-8",
        )

        cli.collect(project_id="test-project", use_mock=True)

        mock_collector.assert_called_once_with(
            project_id="test-project", organization_id=None, use_mock=True
        )

    @patch("app.main.explainer_main")
    def test_analyze_command(self, mock_explainer, cli, tmp_path, monkeypatch):
        """Test the analyze command."""
        monkeypatch.chdir(tmp_path)
        Path("data").mkdir()

        # Create mock explained data
        Path("data/explained.json").write_text(
            json.dumps([{"severity": "HIGH", "title": "Test finding"}]), encoding="utf-8"
        )

        cli.analyze(project_id="test-project", use_mock=True)

        mock_explainer.assert_called_once_with(
            project_id="test-project",
            location="us-central1",
            use_mock=True,
            ai_provider=None,
            ollama_model=None,
            ollama_endpoint=None,
        )

    @patch("app.main.reporter_main")
    def test_report_command(self, mock_reporter, cli):
        """Test the report command."""
        cli.report(formats=["markdown"], output_dir="test-output")

        mock_reporter.assert_called_once_with(
            template_dir="app/templates",
            formats=["markdown"],
            input_dir="data",
            output_dir="test-output",
        )

    @patch("app.main.collector_main")
    @patch("app.main.explainer_main")
    @patch("app.main.reporter_main")
    def test_audit_command_success(
        self, mock_reporter, mock_explainer, mock_collector, cli, tmp_path, monkeypatch
    ):
        """Test the audit command runs full pipeline."""
        monkeypatch.chdir(tmp_path)
        Path("data").mkdir()
        Path("output").mkdir()

        # Create mock data files
        Path("data/collected.json").write_text(
            json.dumps({"iam_policies": [], "scc_findings": []}), encoding="utf-8"
        )
        Path("data/explained.json").write_text(json.dumps([]), encoding="utf-8")

        cli.audit(project_id="test-project", use_mock=True)

        # Verify all agents were called
        mock_collector.assert_called_once()
        mock_explainer.assert_called_once()
        mock_reporter.assert_called_once()

    @patch("app.main.collector_main")
    def test_audit_command_failure(self, mock_collector, cli, tmp_path, monkeypatch):
        """Test the audit command handles failures."""
        monkeypatch.chdir(tmp_path)
        mock_collector.side_effect = Exception("Collection failed")

        with pytest.raises(SystemExit):
            cli.audit(project_id="test-project", use_mock=True)

    @patch("app.main.collector_main")
    @patch("app.main.explainer_main")
    @patch("app.main.reporter_main")
    def test_audit_verbose_mode(
        self, mock_reporter, mock_explainer, mock_collector, cli, tmp_path, monkeypatch
    ):  # pylint: disable=unused-argument
        """Test verbose mode sets debug logging."""
        monkeypatch.chdir(tmp_path)
        Path("data").mkdir()
        Path("output").mkdir()

        # Create mock data files
        Path("data/collected.json").write_text(
            json.dumps({"iam_policies": [], "scc_findings": []}), encoding="utf-8"
        )
        Path("data/explained.json").write_text(json.dumps([]), encoding="utf-8")

        with patch("logging.getLogger") as mock_logger:
            mock_root_logger = MagicMock()
            mock_logger.return_value = mock_root_logger

            cli.audit(verbose=True, use_mock=True)

            mock_root_logger.setLevel.assert_called_with(10)  # logging.DEBUG = 10
