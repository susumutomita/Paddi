"""
Unit tests for the GCP Configuration Collector
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from collector.agent_collector import (
    GCPConfigurationCollector,
    IAMCollector,
    SCCCollector,
)


class TestIAMCollector:
    """Test cases for IAM Collector"""

    def test_collect_with_mock_data(self):
        """Test collecting IAM data with mock"""
        collector = IAMCollector(project_id="test-project", use_mock=True)
        data = collector.collect()

        assert "bindings" in data
        assert len(data["bindings"]) > 0
        assert data["bindings"][0]["role"] == "roles/owner"
        assert "etag" in data
        assert data["version"] == 1

    def test_collect_without_google_cloud_iam(self):
        """Test behavior when google-cloud-iam is not installed"""
        collector = IAMCollector(project_id="test-project", use_mock=False)

        # Since google-cloud-iam is not actually installed,
        # the collect method should return mock data
        data = collector.collect()

        # Should return mock data
        assert "bindings" in data
        assert data["bindings"][0]["role"] == "roles/owner"

    def test_collect_handles_exceptions(self):
        """Test that collector handles exceptions gracefully"""
        collector = IAMCollector(project_id="test-project", use_mock=False)

        # Since google-cloud-iam is not installed, it should return mock data
        data = collector.collect()
        # Should return mock data
        assert "bindings" in data


class TestSCCCollector:
    """Test cases for Security Command Center Collector"""

    def test_collect_with_mock_data(self):
        """Test collecting SCC findings with mock"""
        collector = SCCCollector(organization_id="123456", use_mock=True)
        findings = collector.collect()

        assert isinstance(findings, list)
        assert len(findings) > 0
        assert findings[0]["category"] == "OVERPRIVILEGED_SERVICE_ACCOUNT"
        assert findings[0]["severity"] == "HIGH"
        assert findings[1]["category"] == "PUBLIC_BUCKET"

    def test_collect_without_google_cloud_securitycenter(self):
        """Test behavior when google-cloud-securitycenter is not installed"""
        collector = SCCCollector(organization_id="123456", use_mock=False)

        # Should fall back to mock data when import fails
        data = collector.collect()
        assert isinstance(data, list)
        assert len(data) > 0


class TestGCPConfigurationCollector:
    """Test cases for the main GCP Configuration Collector"""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary output directory"""
        return tmp_path / "test_output"

    def test_initialization(self, temp_output_dir):
        """Test collector initialization"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        assert collector.project_id == "test-project"
        assert collector.organization_id == "test-org"
        assert collector.use_mock is True
        assert collector.output_dir.exists()

    def test_collect_all(self, temp_output_dir):
        """Test collecting all configurations"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        data = collector.collect_all()

        assert "metadata" in data
        assert data["metadata"]["project_id"] == "test-project"
        assert data["metadata"]["organization_id"] == "test-org"
        assert "timestamp" in data["metadata"]
        assert "iam_policies" in data
        assert "scc_findings" in data
        assert isinstance(data["iam_policies"], dict)
        assert isinstance(data["scc_findings"], list)

    def test_save_to_file(self, temp_output_dir):
        """Test saving collected data to file"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        data = collector.collect_all()
        output_path = collector.save_to_file(data)

        assert output_path.exists()
        assert output_path.name == "collected.json"

        # Verify saved data
        with open(output_path, "r") as f:
            saved_data = json.load(f)

        assert "metadata" in saved_data
        assert saved_data["metadata"]["project_id"] == "test-project"
        assert saved_data["metadata"]["organization_id"] == "test-org"

    def test_save_to_file_custom_filename(self, temp_output_dir):
        """Test saving with custom filename"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        data = collector.collect_all()
        output_path = collector.save_to_file(data, filename="custom.json")

        assert output_path.exists()
        assert output_path.name == "custom.json"

    def test_timestamp_format(self, temp_output_dir):
        """Test that timestamp is in correct ISO format"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        timestamp = collector._get_timestamp()

        # Should be able to parse as ISO format
        from datetime import datetime

        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None

    def test_default_organization_id(self, temp_output_dir):
        """Test default organization ID when not provided"""
        collector = GCPConfigurationCollector(
            project_id="test-project",
            use_mock=True,
            output_dir=str(temp_output_dir),
        )

        assert collector.organization_id == "123456"  # Default value


class TestMainFunction:
    """Test cases for the main CLI function"""

    @patch("collector.agent_collector.GCPConfigurationCollector")
    def test_main_with_defaults(self, mock_collector_class):
        """Test main function with default arguments"""
        from collector.agent_collector import main

        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance
        mock_instance.collect_all.return_value = {"test": "data"}

        main()

        mock_collector_class.assert_called_with(
            project_id="example-project",
            organization_id=None,
            use_mock=True,
            output_dir="data",
        )
        mock_instance.collect_all.assert_called_once()
        mock_instance.save_to_file.assert_called_once()

    @patch("collector.agent_collector.GCPConfigurationCollector")
    def test_main_with_custom_args(self, mock_collector_class):
        """Test main function with custom arguments"""
        from collector.agent_collector import main

        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance
        mock_instance.collect_all.return_value = {"test": "data"}

        main(
            project_id="custom-project",
            organization_id="custom-org",
            use_mock=False,
            output_dir="custom-dir",
        )

        mock_collector_class.assert_called_with(
            project_id="custom-project",
            organization_id="custom-org",
            use_mock=False,
            output_dir="custom-dir",
        )

    @patch("collector.agent_collector.GCPConfigurationCollector")
    @patch("collector.agent_collector.logger")
    def test_main_handles_exceptions(self, mock_logger, mock_collector_class):
        """Test that main function handles exceptions properly"""
        from collector.agent_collector import main

        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance
        mock_instance.collect_all.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            main()

        mock_logger.error.assert_called_with(
            "Collection failed: %s", mock_instance.collect_all.side_effect
        )
