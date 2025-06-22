"""Tests for cloud provider implementations."""

import pytest

from app.providers.aws import AWSProvider
from app.providers.azure import AzureProvider
from app.providers.factory import CloudProviderFactory
from app.providers.gcp import GCPProvider


class TestCloudProviderFactory:
    """Test cloud provider factory."""

    def test_create_gcp_provider(self):
        """Test creating GCP provider."""
        provider = CloudProviderFactory.create("gcp", project_id="test-project")
        assert isinstance(provider, GCPProvider)
        assert provider.get_name() == "gcp"

    def test_create_aws_provider(self):
        """Test creating AWS provider."""
        provider = CloudProviderFactory.create("aws", account_id="123456789012")
        assert isinstance(provider, AWSProvider)
        assert provider.get_name() == "aws"

    def test_create_azure_provider(self):
        """Test creating Azure provider."""
        provider = CloudProviderFactory.create("azure", subscription_id="test-sub")
        assert isinstance(provider, AzureProvider)
        assert provider.get_name() == "azure"

    def test_invalid_provider(self):
        """Test creating invalid provider."""
        with pytest.raises(ValueError) as exc:
            CloudProviderFactory.create("invalid")
        assert "Unsupported provider" in str(exc.value)

    def test_get_supported_providers(self):
        """Test getting list of supported providers."""
        providers = CloudProviderFactory.get_supported_providers()
        assert set(providers) == {"gcp", "aws", "azure"}


class TestGCPProvider:
    """Test GCP provider implementation."""

    def test_init(self):
        """Test GCP provider initialization."""
        provider = GCPProvider(project_id="test-project")
        assert provider.project_id == "test-project"
        assert provider.get_name() == "gcp"

    def test_get_iam_policies(self):
        """Test getting IAM policies."""
        provider = GCPProvider()
        policies = provider.get_iam_policies()
        assert "project" in policies
        assert "bindings" in policies
        assert len(policies["bindings"]) > 0

    def test_get_security_findings(self):
        """Test getting security findings."""
        provider = GCPProvider()
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("severity" in f for f in findings)

    def test_get_audit_logs(self):
        """Test getting audit logs."""
        provider = GCPProvider()
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("severity" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all data."""
        provider = GCPProvider(project_id="test-project")
        data = provider.collect_all()
        assert data["provider"] == "gcp"
        assert data["project_id"] == "test-project"
        assert "iam_policies" in data
        assert "security_findings" in data
        assert "audit_logs" in data


class TestAWSProvider:
    """Test AWS provider implementation."""

    def test_init(self):
        """Test AWS provider initialization."""
        provider = AWSProvider(account_id="123456789012", region="us-west-2")
        assert provider.account_id == "123456789012"
        assert provider.region == "us-west-2"
        assert provider.get_name() == "aws"

    def test_default_values(self):
        """Test AWS provider default values."""
        provider = AWSProvider()
        assert provider.account_id == "123456789012"
        assert provider.region == "us-east-1"

    def test_get_iam_policies(self):
        """Test getting IAM policies."""
        provider = AWSProvider()
        policies = provider.get_iam_policies()
        assert "account_id" in policies
        assert "users" in policies
        assert "roles" in policies
        assert "policies" in policies

    def test_get_security_findings(self):
        """Test getting Security Hub findings."""
        provider = AWSProvider()
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("Severity" in f for f in findings)
        assert all("Resources" in f for f in findings)

    def test_get_audit_logs(self):
        """Test getting CloudTrail logs."""
        provider = AWSProvider()
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("eventName" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all data."""
        provider = AWSProvider(account_id="test-account")
        data = provider.collect_all()
        assert data["provider"] == "aws"
        assert data["account_id"] == "test-account"
        assert "region" in data
        assert "iam_policies" in data
        assert "security_findings" in data
        assert "audit_logs" in data


class TestAzureProvider:
    """Test Azure provider implementation."""

    def test_init(self):
        """Test Azure provider initialization."""
        provider = AzureProvider(subscription_id="test-sub-id", tenant_id="test-tenant-id")
        assert provider.subscription_id == "test-sub-id"
        assert provider.tenant_id == "test-tenant-id"
        assert provider.get_name() == "azure"

    def test_default_values(self):
        """Test Azure provider default values."""
        provider = AzureProvider()
        assert provider.subscription_id == "00000000-0000-0000-0000-000000000000"
        assert provider.tenant_id == "11111111-1111-1111-1111-111111111111"

    def test_get_iam_policies(self):
        """Test getting Azure AD roles."""
        provider = AzureProvider()
        policies = provider.get_iam_policies()
        assert "subscription_id" in policies
        assert "tenant_id" in policies
        assert "users" in policies
        assert "service_principals" in policies
        assert "custom_roles" in policies

    def test_get_security_findings(self):
        """Test getting Security Center alerts."""
        provider = AzureProvider()
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("properties" in f for f in findings)
        assert all("severity" in f["properties"] for f in findings)

    def test_get_audit_logs(self):
        """Test getting Activity logs."""
        provider = AzureProvider()
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("operationName" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all data."""
        provider = AzureProvider(subscription_id="test-sub", tenant_id="test-tenant")
        data = provider.collect_all()
        assert data["provider"] == "azure"
        assert data["subscription_id"] == "test-sub"
        assert data["tenant_id"] == "test-tenant"
        assert "iam_policies" in data
        assert "security_findings" in data
        assert "audit_logs" in data
