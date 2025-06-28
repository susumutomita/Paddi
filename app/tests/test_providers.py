"""Tests for cloud provider implementations."""

from unittest.mock import Mock, patch

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
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(use_mock=True)
        assert provider.get_name() == "github"
        assert provider.use_mock is True

    def test_init_without_token(self):
        """Test GitHub provider initialization without token."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(access_token=None)
        assert provider.use_mock is True

    def test_get_iam_policies(self):
        """Test getting repository access permissions."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(use_mock=True)
        policies = provider.get_iam_policies()
        assert "repository" in policies
        assert "visibility" in policies
        assert "collaborators" in policies
        assert "branch_protections" in policies
        assert len(policies["collaborators"]) > 0

    def test_get_security_findings(self):
        """Test getting security vulnerabilities."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(use_mock=True)
        findings = provider.get_security_findings()
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("type" in finding for finding in findings)
        assert all("severity" in finding for finding in findings)

    def test_get_audit_logs(self):
        """Test getting repository audit events."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(use_mock=True)
        logs = provider.get_audit_logs()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all("type" in log for log in logs)
        assert all("actor" in log for log in logs)
        assert all("timestamp" in log for log in logs)

    def test_collect_all(self):
        """Test collecting all GitHub data."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(owner="test-org", repo="test-repo", use_mock=True)
        data = provider.collect_all()
        assert data["provider"] == "github"
        assert data["repository"] == "test-org/test-repo"
        assert "iam_policies" in data
        assert "security_findings" in data
        assert "audit_logs" in data

    def test_environment_variables(self):
        """Test GitHub provider with environment variables."""
        from app.providers.github import GitHubProvider

        with patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "test-token", "GITHUB_OWNER": "env-owner", "GITHUB_REPO": "env-repo"},
        ):
            provider = GitHubProvider()
            assert provider.access_token == "test-token"
            assert provider.owner == "env-owner"
            assert provider.repo == "env-repo"
            assert provider.use_mock is False

    @patch("requests.get")
    def test_collect_dependabot_alerts_success(self, mock_get):
        """Test successful Dependabot alerts collection."""
        from app.providers.github import GitHubProvider

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "number": 1,
                "state": "open",
                "severity": "high",
                "security_vulnerability": {
                    "package": {"name": "requests", "ecosystem": "pip"},
                    "vulnerable_version_range": "<= 2.20.0",
                    "first_patched_version": {"identifier": "2.20.1"},
                },
                "security_advisory": {
                    "summary": "Security vulnerability in requests",
                    "cve_id": "CVE-2018-18074",
                    "ghsa_id": "GHSA-x84v-xcm2-53pg",
                    "references": [],
                },
                "created_at": "2023-01-01T00:00:00Z",
            }
        ]
        mock_get.return_value = mock_response

        provider = GitHubProvider(access_token="test-token", owner="test-org", repo="test-repo")
        alerts = provider.collect_dependabot_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "dependabot_alert"
        assert alerts[0]["severity"] == "HIGH"
        assert alerts[0]["package_name"] == "requests"
        assert alerts[0]["cve_id"] == "CVE-2018-18074"

    @patch("requests.get")
    def test_collect_dependabot_alerts_auth_error(self, mock_get):
        """Test Dependabot alerts collection with authentication error."""
        from app.providers.github import GitHubProvider

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response

        provider = GitHubProvider(access_token="invalid-token", owner="test-org", repo="test-repo")

        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "Authentication failed" in str(exc.value)

    @patch("requests.get")
    def test_collect_dependabot_alerts_rate_limit(self, mock_get):
        """Test Dependabot alerts collection with rate limit error."""
        from app.providers.github import GitHubProvider

        # Mock 403 rate limit response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "API rate limit exceeded"
        mock_response.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_get.return_value = mock_response

        provider = GitHubProvider(access_token="test-token", owner="test-org", repo="test-repo")

        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "rate limit exceeded" in str(exc.value)

    @patch("requests.get")
    def test_collect_dependabot_alerts_not_found(self, mock_get):
        """Test Dependabot alerts collection with repository not found."""
        from app.providers.github import GitHubProvider

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        provider = GitHubProvider(access_token="test-token", owner="test-org", repo="test-repo")

        with pytest.raises(Exception) as exc:
            provider.collect_dependabot_alerts()
        assert "not found" in str(exc.value)

    def test_convert_alert(self):
        """Test alert conversion to internal format."""
        from app.providers.github import GitHubProvider

        provider = GitHubProvider(use_mock=True)

        github_alert = {
            "number": 1,
            "state": "open",
            "severity": "critical",
            "security_vulnerability": {
                "package": {"name": "lodash", "ecosystem": "npm"},
                "vulnerable_version_range": "< 4.17.19",
                "first_patched_version": {"identifier": "4.17.19"},
            },
            "security_advisory": {
                "summary": "Prototype pollution in lodash",
                "cve_id": "CVE-2020-8203",
                "ghsa_id": "GHSA-jf85-cpcp-j695",
                "references": ["https://example.com/advisory"],
            },
            "created_at": "2023-01-01T00:00:00Z",
        }

        converted = provider._convert_alert(github_alert)

        assert converted["type"] == "dependabot_alert"
        assert converted["severity"] == "CRITICAL"
        assert converted["package_name"] == "lodash"
        assert converted["package_ecosystem"] == "npm"
        assert converted["vulnerable_version"] == "< 4.17.19"
        assert converted["patched_version"] == "4.17.19"
        assert converted["cve_id"] == "CVE-2020-8203"
        assert converted["ghsa_id"] == "GHSA-jf85-cpcp-j695"
        assert "Update lodash to version 4.17.19" in converted["recommendation"]

    @patch("requests.get")
    def test_get_security_findings_with_api(self, mock_get):
        """Test get_security_findings with real API."""
        from app.providers.github import GitHubProvider

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        provider = GitHubProvider(access_token="test-token", owner="test-org", repo="test-repo")
        findings = provider.get_security_findings()

        # Should include both Dependabot alerts and other security checks
        assert isinstance(findings, list)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_security_findings_fallback(self, mock_get):
        """Test get_security_findings fallback to mock on error."""
        from app.providers.github import GitHubProvider

        # Mock failed response
        mock_get.side_effect = Exception("API Error")

        provider = GitHubProvider(access_token="test-token", owner="test-org", repo="test-repo")
        findings = provider.get_security_findings()

        # Should fall back to mock data
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert all("type" in f for f in findings)
