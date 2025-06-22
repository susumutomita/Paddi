"""Tests for multi-cloud collector."""

import json
from pathlib import Path

import pytest

from app.collector.multi_cloud_collector import MultiCloudCollector


class TestMultiCloudCollector:
    """Test multi-cloud collector functionality."""

    @pytest.fixture
    def collector(self, tmp_path):
        """Create collector with temp directory."""
        return MultiCloudCollector(output_dir=str(tmp_path))

    def test_init(self, collector, tmp_path):
        """Test collector initialization."""
        assert collector.output_dir == tmp_path
        assert collector.output_dir.exists()

    def test_collect_from_single_provider_gcp(self, collector):
        """Test collecting from single GCP provider."""
        provider_config = {"provider": "gcp", "project_id": "test-project"}

        data = collector.collect_from_provider(provider_config)
        assert data["provider"] == "gcp"
        assert data["project_id"] == "test-project"
        assert "iam_policies" in data
        assert "security_findings" in data

    def test_collect_from_single_provider_aws(self, collector):
        """Test collecting from single AWS provider."""
        provider_config = {"provider": "aws", "account_id": "123456789012", "region": "us-west-2"}

        data = collector.collect_from_provider(provider_config)
        assert data["provider"] == "aws"
        assert data["account_id"] == "123456789012"
        assert data["region"] == "us-west-2"
        assert "iam_policies" in data

    def test_collect_from_single_provider_azure(self, collector):
        """Test collecting from single Azure provider."""
        provider_config = {"provider": "azure", "subscription_id": "test-sub-id"}

        data = collector.collect_from_provider(provider_config)
        assert data["provider"] == "azure"
        assert data["subscription_id"] == "test-sub-id"
        assert "iam_policies" in data

    def test_collect_from_provider_missing_provider_key(self, collector):
        """Test error when provider key is missing."""
        with pytest.raises(ValueError) as exc:
            collector.collect_from_provider({"project_id": "test"})
        assert "must include 'provider' key" in str(exc.value)

    def test_collect_from_multiple_providers(self, collector):
        """Test collecting from multiple providers."""
        providers = [
            {"provider": "gcp", "project_id": "gcp-project"},
            {"provider": "aws", "account_id": "123456789012"},
            {"provider": "azure", "subscription_id": "azure-sub"},
        ]

        data = collector.collect_from_multiple_providers(providers)

        assert "providers" in data
        assert "summary" in data
        assert len(data["providers"]) == 3
        assert data["summary"]["total_providers"] == 3
        assert data["summary"]["total_findings"] > 0
        assert "findings_by_severity" in data["summary"]
        assert "findings_by_provider" in data["summary"]

        # Check each provider data
        provider_names = [p["provider"] for p in data["providers"]]
        assert set(provider_names) == {"gcp", "aws", "azure"}

    def test_collect_from_multiple_providers_with_error(self, collector):
        """Test collecting with provider error."""
        providers = [
            {"provider": "gcp", "project_id": "gcp-project"},
            {"provider": "invalid"},  # This will cause an error
            {"provider": "aws", "account_id": "123456789012"},
        ]

        data = collector.collect_from_multiple_providers(providers)

        assert len(data["providers"]) == 3
        assert data["summary"]["total_providers"] == 3

        # Check that the invalid provider has error status
        invalid_provider = next(p for p in data["providers"] if p.get("provider") == "invalid")
        assert "error" in invalid_provider
        assert invalid_provider["status"] == "failed"

        # Other providers should still work
        valid_providers = [p for p in data["providers"] if "error" not in p]
        assert len(valid_providers) == 2

    def test_severity_counting(self, collector):
        """Test severity counting across providers."""
        providers = [
            {"provider": "gcp", "project_id": "test"},
            {"provider": "aws", "account_id": "123456789012"},
        ]

        data = collector.collect_from_multiple_providers(providers)
        severity_counts = data["summary"]["findings_by_severity"]

        assert all(sev in severity_counts for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        assert sum(severity_counts.values()) == data["summary"]["total_findings"]

    def test_save_data(self, collector, tmp_path):
        """Test saving collected data."""
        test_data = {
            "providers": [{"provider": "gcp", "data": "test"}],
            "summary": {"total_providers": 1},
        }

        output_path = collector.save_data(test_data)
        assert output_path == tmp_path / "collected.json"
        assert output_path.exists()

        # Verify saved data
        with open(output_path) as f:
            saved_data = json.load(f)
        assert saved_data == test_data

    def test_save_data_custom_filename(self, collector, tmp_path):
        """Test saving with custom filename."""
        test_data = {"test": "data"}
        output_path = collector.save_data(test_data, "custom.json")

        assert output_path == tmp_path / "custom.json"
        assert output_path.exists()
