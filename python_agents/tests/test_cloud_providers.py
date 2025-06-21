"""Tests for cloud provider implementations."""

import pytest
from unittest.mock import MagicMock, patch

from collector.cloud_provider import CloudConfig, CloudProvider, CloudCollectorFactory
from collector.gcp_provider import GCPProvider
from collector.aws_provider import AWSProvider  
from collector.azure_provider import AzureProvider


class TestCloudProviderFactory:
    """Test cloud provider factory."""
    
    def test_factory_registration(self):
        """Test that all providers are registered."""
        # Providers should be auto-registered on import
        gcp_config = CloudConfig(provider=CloudProvider.GCP, use_mock=True)
        gcp_provider = CloudCollectorFactory.create(gcp_config)
        assert isinstance(gcp_provider, GCPProvider)
        
        aws_config = CloudConfig(provider=CloudProvider.AWS, use_mock=True)
        aws_provider = CloudCollectorFactory.create(aws_config)
        assert isinstance(aws_provider, AWSProvider)
        
        azure_config = CloudConfig(provider=CloudProvider.AZURE, use_mock=True)
        azure_provider = CloudCollectorFactory.create(azure_config)
        assert isinstance(azure_provider, AzureProvider)
    
    def test_invalid_provider(self):
        """Test factory raises error for invalid provider."""
        with pytest.raises(ValueError):
            invalid_config = CloudConfig(provider="invalid", use_mock=True)


class TestGCPProvider:
    """Test GCP provider implementation."""
    
    @pytest.fixture
    def gcp_provider(self):
        """Create GCP provider instance."""
        config = CloudConfig(
            provider=CloudProvider.GCP,
            project_id="test-project",
            use_mock=True
        )
        return GCPProvider(config)
    
    def test_provider_name(self, gcp_provider):
        """Test provider name."""
        assert gcp_provider.provider_name == "Google Cloud Platform"
    
    def test_validate_credentials_mock(self, gcp_provider):
        """Test credential validation with mock."""
        assert gcp_provider.validate_credentials() is True
    
    def test_iam_collector(self, gcp_provider):
        """Test GCP IAM collector."""
        users = gcp_provider.iam_collector.collect_users()
        assert len(users) > 0
        assert all(u["provider"] == "gcp" for u in users)
        
        roles = gcp_provider.iam_collector.collect_roles()
        assert len(roles) > 0
        assert any(r["name"] == "roles/owner" for r in roles)
        
        policies = gcp_provider.iam_collector.collect_policies()
        assert len(policies) > 0
    
    def test_security_collector(self, gcp_provider):
        """Test GCP security collector."""
        findings = gcp_provider.security_collector.collect_findings()
        assert len(findings) > 0
        assert all(f["provider"] == "gcp" for f in findings)
        
        compliance = gcp_provider.security_collector.collect_compliance_status()
        assert "provider" in compliance
        assert compliance["provider"] == "gcp"
        assert "standards" in compliance
    
    def test_log_collector(self, gcp_provider):
        """Test GCP log collector."""
        logs = gcp_provider.log_collector.collect_recent_logs()
        assert len(logs) > 0
        
        suspicious = gcp_provider.log_collector.collect_suspicious_activities()
        assert len(suspicious) > 0


class TestAWSProvider:
    """Test AWS provider implementation."""
    
    @pytest.fixture
    def aws_provider(self):
        """Create AWS provider instance."""
        config = CloudConfig(
            provider=CloudProvider.AWS,
            account_id="123456789012",
            region="us-east-1",
            use_mock=True
        )
        return AWSProvider(config)
    
    def test_provider_name(self, aws_provider):
        """Test provider name."""
        assert aws_provider.provider_name == "Amazon Web Services"
    
    def test_validate_credentials_mock(self, aws_provider):
        """Test credential validation with mock."""
        assert aws_provider.validate_credentials() is True
    
    def test_iam_collector(self, aws_provider):
        """Test AWS IAM collector."""
        users = aws_provider.iam_collector.collect_users()
        assert len(users) > 0
        assert all("arn" in u for u in users)
        assert all(u["provider"] == "aws" for u in users)
        
        roles = aws_provider.iam_collector.collect_roles()
        assert len(roles) > 0
        assert all("arn" in r for r in roles)
        
        policies = aws_provider.iam_collector.collect_policies()
        assert len(policies) > 0
        assert all("document" in p for p in policies)
    
    def test_security_collector(self, aws_provider):
        """Test AWS security collector."""
        findings = aws_provider.security_collector.collect_findings()
        assert len(findings) > 0
        assert all(f["provider"] == "aws" for f in findings)
        
        # Test severity filter
        high_findings = aws_provider.security_collector.collect_findings(["HIGH"])
        assert all(f["severity"] == "HIGH" for f in high_findings)
        
        compliance = aws_provider.security_collector.collect_compliance_status()
        assert compliance["provider"] == "aws"
        assert "aws_foundational_security" in compliance["standards"]
    
    def test_log_collector(self, aws_provider):
        """Test AWS log collector."""
        logs = aws_provider.log_collector.collect_recent_logs(hours=24)
        assert len(logs) > 0
        assert all("event_name" in log for log in logs)
        
        suspicious = aws_provider.log_collector.collect_suspicious_activities()
        assert len(suspicious) > 0


class TestAzureProvider:
    """Test Azure provider implementation."""
    
    @pytest.fixture
    def azure_provider(self):
        """Create Azure provider instance."""
        config = CloudConfig(
            provider=CloudProvider.AZURE,
            subscription_id="00000000-0000-0000-0000-000000000000",
            use_mock=True
        )
        return AzureProvider(config)
    
    def test_provider_name(self, azure_provider):
        """Test provider name."""
        assert azure_provider.provider_name == "Microsoft Azure"
    
    def test_validate_credentials_mock(self, azure_provider):
        """Test credential validation with mock."""
        assert azure_provider.validate_credentials() is True
    
    def test_iam_collector(self, azure_provider):
        """Test Azure IAM collector."""
        users = azure_provider.iam_collector.collect_users()
        assert len(users) > 0
        assert any("object_id" in u for u in users)
        assert all(u["provider"] == "azure" for u in users)
        
        roles = azure_provider.iam_collector.collect_roles()
        assert len(roles) > 0
        assert any(r["name"] == "Owner" for r in roles)
        
        policies = azure_provider.iam_collector.collect_policies()
        assert len(policies) > 0
    
    def test_security_collector(self, azure_provider):
        """Test Azure security collector."""
        findings = azure_provider.security_collector.collect_findings()
        assert len(findings) > 0
        assert all(f["provider"] == "azure" for f in findings)
        
        compliance = azure_provider.security_collector.collect_compliance_status()
        assert compliance["provider"] == "azure"
        assert "azure_security_benchmark" in compliance["standards"]
    
    def test_log_collector(self, azure_provider):
        """Test Azure log collector."""
        logs = azure_provider.log_collector.collect_recent_logs()
        assert len(logs) > 0
        assert all("operation" in log for log in logs)
        
        suspicious = azure_provider.log_collector.collect_suspicious_activities()
        assert len(suspicious) > 0