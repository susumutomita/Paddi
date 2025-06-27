"""Tests for cloud provider implementations."""

import pytest
from unittest.mock import Mock, patch

from app.providers.aws import AWSProvider
from app.providers.azure import AzureProvider
from app.providers.factory import CloudProviderFactory
from app.providers.gcp import GCPProvider
from app.providers.github import GitHubProvider


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
        assert set(providers) == {"gcp", "aws", "azure", "github"}


class TestGCPProvider:
    """Test GCP provider implementation."""

    def test_init(self):
        """Test GCP provider initialization."""
        provider = GCPProvider(project_id="test-project", use_mock=True)
        assert provider.project_id == "test-project"
        assert provider.get_name() == "gcp"
        assert provider.use_mock is True

    def test_get_iam_policies(self):
        """Test getting IAM policies."""
        provider = GCPProvider(use_mock=True)
        policies = provider.get_iam_policies()
        assert "project" in policies
        assert "bindings" in policies
        assert len(policies["bindings"]) > 0

    def test_get_security_findings(self):
        """Test getting security findings."""
        provider = GCPProvider(use_mock=True)
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("severity" in f for f in findings)

    def test_get_audit_logs(self):
        """Test getting audit logs."""
        provider = GCPProvider(use_mock=True)
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("severity" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all data."""
        provider = GCPProvider(project_id="test-project", use_mock=True)
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


class TestGitHubProvider:
    """Test GitHub provider implementation."""

    def test_init_with_mock(self):
        """Test GitHub provider initialization with mock data."""
        provider = GitHubProvider(use_mock=True)
        assert provider.get_name() == "github"
        assert provider.use_mock is True

    def test_init_without_token(self):
        """Test GitHub provider initialization without token."""
        provider = GitHubProvider(access_token=None)
        assert provider.use_mock is True
    
    def test_init_with_env_vars(self):
        """Test GitHub provider initialization with environment variables."""
        with patch.dict('os.environ', {
            'GITHUB_TOKEN': 'test-token',
            'GITHUB_OWNER': 'test-owner',
            'GITHUB_REPO': 'test-repo'
        }):
            provider = GitHubProvider()
            assert provider.access_token == 'test-token'
            assert provider.owner == 'test-owner'
            assert provider.repo == 'test-repo'
            assert provider.use_mock is False
            assert provider.headers['Authorization'] == 'token test-token'

    def test_get_iam_policies(self):
        """Test getting repository access permissions."""
        provider = GitHubProvider(use_mock=True)
        policies = provider.get_iam_policies()
        assert "repository" in policies
        assert "visibility" in policies
        assert "collaborators" in policies
        assert "branch_protections" in policies
        assert len(policies["collaborators"]) > 0

    def test_get_security_findings(self):
        """Test getting security vulnerabilities."""
        provider = GitHubProvider(use_mock=True)
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("type" in finding for finding in findings)
        assert all("severity" in finding for finding in findings)
        
        # Check for Dependabot alerts in mock findings
        dependabot_alerts = [f for f in findings if f["type"] == "dependabot_alert"]
        assert len(dependabot_alerts) > 0
        for alert in dependabot_alerts:
            assert "package_name" in alert
            assert "severity" in alert
            assert "description" in alert
            assert "recommendation" in alert

    def test_get_audit_logs(self):
        """Test getting repository audit events."""
        provider = GitHubProvider(use_mock=True)
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("type" in log for log in logs)
        assert all("actor" in log for log in logs)
        assert all("timestamp" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all GitHub data."""
        provider = GitHubProvider(owner="test-org", repo="test-repo", use_mock=True)
        data = provider.collect_all()
        assert data["provider"] == "github"
        assert data["repository"] == "test-org/test-repo"
        assert "iam_policies" in data
        assert "security_findings" in data
        assert "audit_logs" in data
    
    @patch('requests.get')
    def test_collect_dependabot_alerts_success(self, mock_get):
        """Test successful Dependabot alerts collection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "security_vulnerability": {
                    "package": {"name": "requests", "ecosystem": "pip"},
                    "vulnerable_version_range": "< 2.32.0",
                    "first_patched_version": {"identifier": "2.32.0"}
                },
                "security_advisory": {
                    "severity": "critical",
                    "summary": "Critical vulnerability in requests",
                    "description": "Detailed description",
                    "ghsa_id": "GHSA-xxxx-xxxx-xxxx",
                    "identifiers": [{"type": "CVE", "value": "CVE-2023-12345"}]
                },
                "created_at": "2024-01-01T00:00:00Z",
                "state": "open",
                "dismissed_at": None,
                "dismissed_reason": None
            }
        ]
        mock_get.return_value = mock_response
        
        provider = GitHubProvider(access_token="test-token", use_mock=False)
        alerts = provider.collect_dependabot_alerts()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert["type"] == "dependabot_alert"
        assert alert["severity"] == "CRITICAL"
        assert alert["package_name"] == "requests"
        assert alert["cve_id"] == "CVE-2023-12345"
        assert alert["fixed_version"] == "2.32.0"
    
    @patch('requests.get')
    def test_collect_dependabot_alerts_auth_failure(self, mock_get):
        """Test Dependabot alerts collection with authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        provider = GitHubProvider(access_token="invalid-token", use_mock=False)
        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "Authentication failed" in str(exc.value)
    
    @patch('requests.get')
    def test_collect_dependabot_alerts_rate_limit(self, mock_get):
        """Test Dependabot alerts collection with rate limit."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        provider = GitHubProvider(access_token="test-token", use_mock=False)
        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "Rate limit exceeded" in str(exc.value)
    
    @patch('requests.get')
    def test_collect_dependabot_alerts_repo_not_found(self, mock_get):
        """Test Dependabot alerts collection with repository not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        provider = GitHubProvider(access_token="test-token", use_mock=False)
        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "Repository not found" in str(exc.value)
    
    def test_convert_alert(self):
        """Test alert conversion to internal format."""
        provider = GitHubProvider(use_mock=True)
        
        github_alert = {
            "security_vulnerability": {
                "package": {"name": "pyyaml", "ecosystem": "pip"},
                "vulnerable_version_range": "< 5.4",
                "first_patched_version": {"identifier": "5.4"}
            },
            "security_advisory": {
                "severity": "high",
                "summary": "YAML vulnerability",
                "description": "Arbitrary code execution",
                "ghsa_id": "GHSA-yyyy",
                "identifiers": [{"type": "CVE", "value": "CVE-2020-14343"}]
            },
            "created_at": "2024-01-01T00:00:00Z",
            "state": "open",
            "dismissed_at": None,
            "dismissed_reason": None
        }
        
        converted = provider._convert_alert(github_alert)
        
        assert converted["type"] == "dependabot_alert"
        assert converted["severity"] == "HIGH"
        assert converted["package_name"] == "pyyaml"
        assert converted["cve_id"] == "CVE-2020-14343"
        assert converted["fixed_version"] == "5.4"
        assert converted["recommendation"] == "Update to version 5.4"
    
    @patch('requests.get')
    def test_get_security_findings_with_api_failure(self, mock_get):
        """Test security findings fallback to mock on API failure."""
        mock_get.side_effect = Exception("API error")
        
        provider = GitHubProvider(access_token="test-token", use_mock=False)
        findings = provider.get_security_findings()
        
        # Should fallback to mock data
        assert isinstance(findings, list)
        assert len(findings) > 0
        
        # Check that mock Dependabot alerts are included
        dependabot_alerts = [f for f in findings if f["type"] == "dependabot_alert"]
        assert len(dependabot_alerts) > 0
