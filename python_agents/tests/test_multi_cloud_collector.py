"""Tests for multi-cloud collector functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from collector.cloud_provider import CloudConfig, CloudProvider, CloudCollectorFactory
from collector.multi_cloud_collector import MultiCloudConfigurationCollector


class TestMultiCloudCollector:
    """Test multi-cloud configuration collector."""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock provider configurations."""
        return [
            {
                "provider": "gcp",
                "project_id": "test-gcp-project"
            },
            {
                "provider": "aws", 
                "account_id": "123456789012"
            },
            {
                "provider": "azure",
                "subscription_id": "00000000-0000-0000-0000-000000000000"
            }
        ]
    
    @pytest.fixture
    def collector(self, tmp_path, mock_providers):
        """Create a multi-cloud collector instance."""
        return MultiCloudConfigurationCollector(
            providers=mock_providers,
            use_mock=True,
            output_dir=str(tmp_path)
        )
    
    def test_collector_initialization(self, collector):
        """Test collector initializes with all providers."""
        assert len(collector.cloud_providers) == 3
        provider_names = [p.provider_name for p in collector.cloud_providers]
        assert "Google Cloud Platform" in provider_names
        assert "Amazon Web Services" in provider_names
        assert "Microsoft Azure" in provider_names
    
    def test_collect_all_providers(self, collector):
        """Test collecting data from all providers."""
        data = collector.collect_all()
        
        assert "timestamp" in data
        assert "providers" in data
        assert "summary" in data
        
        # Check all providers are present
        assert "gcp" in data["providers"]
        assert "aws" in data["providers"]
        assert "azure" in data["providers"]
        
        # Check each provider has expected structure
        for provider_name, provider_data in data["providers"].items():
            assert "iam" in provider_data
            assert "security" in provider_data
            assert "logs" in provider_data
            
            # Check IAM data
            assert "users" in provider_data["iam"]
            assert "roles" in provider_data["iam"]
            assert "policies" in provider_data["iam"]
            
            # Check security data
            assert "findings" in provider_data["security"]
            assert "compliance" in provider_data["security"]
    
    def test_summary_aggregation(self, collector):
        """Test that summary correctly aggregates data."""
        data = collector.collect_all()
        summary = data["summary"]
        
        assert summary["total_users"] > 0
        assert summary["total_roles"] > 0
        assert summary["total_findings"] > 0
        assert summary["high_severity_findings"] > 0
        assert len(summary["providers_analyzed"]) == 3
    
    def test_save_to_file(self, collector, tmp_path):
        """Test saving collected data to file."""
        data = collector.collect_all()
        output_path = collector.save_to_file(data)
        
        assert output_path.exists()
        assert output_path.name == "collected.json"
        
        # Load and verify saved data
        with open(output_path) as f:
            saved_data = json.load(f)
        
        assert saved_data == data
    
    def test_single_provider_mode(self, tmp_path):
        """Test collector with single provider."""
        collector = MultiCloudConfigurationCollector(
            providers=[{"provider": "gcp", "project_id": "test-project"}],
            use_mock=True,
            output_dir=str(tmp_path)
        )
        
        data = collector.collect_all()
        
        assert len(data["providers"]) == 1
        assert "gcp" in data["providers"]
        assert data["summary"]["providers_analyzed"] == ["gcp"]
    
    def test_invalid_provider(self, tmp_path):
        """Test collector handles invalid provider gracefully."""
        collector = MultiCloudConfigurationCollector(
            providers=[{"provider": "invalid-cloud"}],
            use_mock=True,
            output_dir=str(tmp_path)
        )
        
        # Should have no providers due to invalid configuration
        assert len(collector.cloud_providers) == 0
        
        data = collector.collect_all()
        assert len(data["providers"]) == 0
    
    def test_credential_validation(self, collector):
        """Test credential validation for each provider."""
        for provider in collector.cloud_providers:
            # Mock providers should always validate successfully
            assert provider.validate_credentials() is True
    
    def test_provider_specific_data_gcp(self, collector):
        """Test GCP-specific data collection."""
        data = collector.collect_all()
        gcp_data = data["providers"]["gcp"]
        
        # Check GCP-specific user format
        users = gcp_data["iam"]["users"]
        assert any(u["type"] == "serviceAccount" for u in users)
        
        # Check GCP-specific findings
        findings = gcp_data["security"]["findings"]
        assert any(f["category"] == "OVERPRIVILEGED_SERVICE_ACCOUNT" for f in findings)
    
    def test_provider_specific_data_aws(self, collector):
        """Test AWS-specific data collection."""
        data = collector.collect_all()
        aws_data = data["providers"]["aws"]
        
        # Check AWS-specific user format
        users = aws_data["iam"]["users"]
        assert all("arn" in u for u in users)
        
        # Check AWS-specific findings
        findings = aws_data["security"]["findings"]
        assert any("aws" in f["finding_type"] for f in findings)
    
    def test_provider_specific_data_azure(self, collector):
        """Test Azure-specific data collection."""
        data = collector.collect_all()
        azure_data = data["providers"]["azure"]
        
        # Check Azure-specific user format
        users = azure_data["iam"]["users"]
        assert any("object_id" in u for u in users)
        
        # Check Azure-specific findings  
        findings = azure_data["security"]["findings"]
        assert any("azure" in f["finding_type"] for f in findings)