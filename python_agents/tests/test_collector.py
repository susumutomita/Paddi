"""Unit tests for the GCP Configuration Collector."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from python_agents.collector.agent_collector import (
    GCPConfigurationCollector,
    IAMCollector,
    JSONExporter,
    SCCFindingsCollector,
)


class TestIAMCollector:
    """Test cases for IAMCollector."""

    def test_collect_mock_data(self):
        """Test collecting mock IAM data."""
        collector = IAMCollector(use_mock=True)
        data = collector.collect()

        assert "policies" in data
        assert "custom_roles" in data
        assert len(data["policies"]) > 0
        assert len(data["custom_roles"]) > 0

    def test_collect_with_error_handling(self):
        """Test error handling in IAM collection."""
        collector = IAMCollector(use_mock=False)

        # Since we're not mocking the real GCP client, it should return mock data
        data = collector.collect()
        assert data is not None


class TestSCCFindingsCollector:
    """Test cases for SCCFindingsCollector."""

    def test_collect_mock_data(self):
        """Test collecting mock SCC findings."""
        collector = SCCFindingsCollector(use_mock=True)
        data = collector.collect()

        assert "findings" in data
        assert len(data["findings"]) > 0
        assert all("severity" in finding for finding in data["findings"])
        assert all("category" in finding for finding in data["findings"])

    def test_collect_with_error_handling(self):
        """Test error handling in SCC collection."""
        collector = SCCFindingsCollector(use_mock=False)

        # Since we're not mocking the real GCP client, it should return mock data
        data = collector.collect()
        assert data is not None


class TestJSONExporter:
    """Test cases for JSONExporter."""

    def test_export_data(self):
        """Test exporting data to JSON file."""
        exporter = JSONExporter()
        test_data = {"test": "data", "nested": {"key": "value"}}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"
            exporter.export(test_data, output_path)

            assert output_path.exists()

            with open(output_path, "r") as f:
                loaded_data = json.load(f)

            assert loaded_data == test_data

    def test_export_creates_directory(self):
        """Test that export creates parent directories if needed."""
        exporter = JSONExporter()
        test_data = {"test": "data"}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "dir" / "output.json"
            exporter.export(test_data, output_path)

            assert output_path.exists()

    def test_export_error_handling(self):
        """Test error handling during export."""
        exporter = JSONExporter()

        # Try to export to an invalid path
        with pytest.raises(Exception):
            exporter.export({"test": "data"}, Path("/invalid/path/output.json"))


class TestGCPConfigurationCollector:
    """Test cases for GCPConfigurationCollector."""

    def test_add_collector(self):
        """Test adding collectors."""
        collector = GCPConfigurationCollector()
        iam_collector = IAMCollector()

        collector.add_collector(iam_collector)
        assert len(collector.collectors) == 1
        assert collector.collectors[0] == iam_collector

    def test_collect_all(self):
        """Test collecting from all collectors."""
        collector = GCPConfigurationCollector()
        collector.add_collector(IAMCollector(use_mock=True))
        collector.add_collector(SCCFindingsCollector(use_mock=True))

        data = collector.collect_all()

        assert "IAMCollector" in data
        assert "SCCFindingsCollector" in data
        assert "policies" in data["IAMCollector"]
        assert "findings" in data["SCCFindingsCollector"]

    def test_collect_with_error(self):
        """Test that collection continues even if one collector fails."""
        collector = GCPConfigurationCollector()

        # Add a mock collector that raises an exception
        mock_collector = MagicMock()
        mock_collector.__class__.__name__ = "FailingCollector"
        mock_collector.collect.side_effect = Exception("Test error")

        collector.add_collector(mock_collector)
        collector.add_collector(IAMCollector(use_mock=True))

        data = collector.collect_all()

        assert "FailingCollector" in data
        assert "error" in data["FailingCollector"]
        assert "IAMCollector" in data
        assert "policies" in data["IAMCollector"]

    def test_run(self):
        """Test the full run process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"

            collector = GCPConfigurationCollector()
            collector.add_collector(IAMCollector(use_mock=True))
            collector.add_collector(SCCFindingsCollector(use_mock=True))

            collector.run(str(output_path))

            assert output_path.exists()

            with open(output_path, "r") as f:
                data = json.load(f)

            assert "IAMCollector" in data
            assert "SCCFindingsCollector" in data


class TestMainFunction:
    """Test cases for the main function."""

    @patch("python_agents.collector.agent_collector.GCPConfigurationCollector")
    def test_main_with_defaults(self, mock_collector_class):
        """Test main function with default arguments."""
        from python_agents.collector.agent_collector import main

        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance

        main()

        mock_collector_class.assert_called_once()
        assert mock_instance.add_collector.call_count == 2
        mock_instance.run.assert_called_once_with("data/collected.json")

    @patch("python_agents.collector.agent_collector.GCPConfigurationCollector")
    def test_main_with_custom_output(self, mock_collector_class):
        """Test main function with custom output path."""
        from python_agents.collector.agent_collector import main

        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance

        custom_path = "custom/output.json"
        main(output_path=custom_path)

        mock_instance.run.assert_called_once_with(custom_path)

    @patch("python_agents.collector.agent_collector.logging")
    def test_main_with_verbose(self, mock_logging):
        """Test main function with verbose logging."""
        from python_agents.collector.agent_collector import main

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            main(output_path=str(output_path), verbose=True)

        # Check that debug logging was enabled
        mock_logging.getLogger().setLevel.assert_called_with(mock_logging.DEBUG)