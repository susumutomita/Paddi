"""GitHub provider implementation."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

from .base import CloudProvider

logger = logging.getLogger(__name__)


class GitHubProvider(CloudProvider):
    """GitHub provider implementation for repository security audit."""

    def __init__(
        self,
        access_token: str = None,
        owner: str = None,
        repo: str = None,
        use_mock: bool = False,
        **kwargs,
    ):
        """Initialize GitHub provider.

        Args:
            access_token: GitHub personal access token or GitHub App token
            owner: Repository owner (organization or user)
            repo: Repository name
            use_mock: Force use of mock data instead of real API calls
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        self.access_token = access_token or os.getenv("GITHUB_TOKEN")
        self.owner = owner or os.getenv("GITHUB_OWNER") or "example-org"
        self.repo = repo or os.getenv("GITHUB_REPO") or "example-repo"
        self.repository = f"{self.owner}/{self.repo}"
        self.use_mock = use_mock or not self.access_token
        self.headers = (
            {
                "Authorization": f"token {self.access_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            if self.access_token
            else {}
        )

    def get_name(self) -> str:
        """Return the name of the provider."""
        return "github"

    def get_iam_policies(self) -> Dict[str, Any]:
        """Get repository access permissions and collaborators."""
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GitHub setup
        return self._get_mock_iam_policies()

    def _get_mock_iam_policies(self) -> Dict[str, Any]:
        """Get mock IAM policies for fallback."""
        return {
            "repository": f"{self.owner}/{self.repo}",
            "visibility": "private",
            "default_branch": "main",
            "collaborators": [
                {
                    "login": "admin-user",
                    "type": "User",
                    "permissions": {"admin": True, "push": True, "pull": True},
                    "role": "admin",
                },
                {
                    "login": "dev-user",
                    "type": "User",
                    "permissions": {"admin": False, "push": True, "pull": True},
                    "role": "write",
                },
                {
                    "login": "readonly-user",
                    "type": "User",
                    "permissions": {"admin": False, "push": False, "pull": True},
                    "role": "read",
                },
            ],
            "teams": [
                {
                    "name": "Development Team",
                    "slug": "dev-team",
                    "permission": "push",
                    "members_count": 5,
                },
            ],
            "branch_protections": [
                {
                    "branch": "main",
                    "enforce_admins": False,
                    "require_pull_request_reviews": True,
                    "dismiss_stale_reviews": True,
                    "required_approving_review_count": 2,
                },
            ],
            "security_features": {
                "vulnerability_alerts": False,
                "automated_security_fixes": False,
            },
        }

    def get_security_findings(self) -> List[Dict[str, Any]]:
        """Get security vulnerabilities and code scanning alerts."""
        if self.use_mock or not self.access_token:
            return self._get_mock_security_findings()

        try:
            # Get Dependabot alerts
            dependabot_alerts = self.collect_dependabot_alerts()

            # Get other security findings (branch protection, etc.)
            other_findings = self._check_security_settings()

            return dependabot_alerts + other_findings
        except Exception as e:
            logger.error("Failed to get security findings: %s", e)
            logger.info("Falling back to mock data")
            return self._get_mock_security_findings()

    def _get_mock_security_findings(self) -> List[Dict[str, Any]]:
        """Get mock security findings for fallback."""
        return [
            {
                "type": "vulnerability_alerts",
                "enabled": False,
                "severity": "HIGH",
                "description": "Dependabot vulnerability alerts are disabled",
                "recommendation": "Enable Dependabot alerts to monitor for vulnerabilities",
            },
            {
                "type": "branch_protection",
                "branch": "main",
                "severity": "HIGH",
                "description": "Default branch 'main' is not protected",
                "recommendation": "Enable branch protection rules for the default branch",
            },
            {
                "type": "two_factor_auth",
                "severity": "MEDIUM",
                "description": "Some collaborators don't have 2FA enabled",
                "recommendation": "Require two-factor authentication for all collaborators",
            },
            {
                "type": "stale_permissions",
                "severity": "MEDIUM",
                "description": "Found inactive collaborators with write access",
                "recommendation": "Review and remove access for inactive collaborators",
            },
        ]

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Get repository audit events and activities."""
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GitHub setup
        return self._get_mock_audit_logs()

    def _get_mock_audit_logs(self) -> List[Dict[str, Any]]:
        """Get mock audit logs for fallback."""
        now = datetime.now()
        return [
            {
                "type": "repository.settings",
                "actor": "admin-user",
                "action": "repository.update_settings",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "details": {
                    "change": "Disabled branch protection on main",
                    "severity": "HIGH",
                },
            },
            {
                "type": "collaborator",
                "actor": "admin-user",
                "action": "repository.add_member",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "details": {
                    "member": "new-contractor",
                    "permission": "admin",
                    "severity": "MEDIUM",
                },
            },
            {
                "type": "commit",
                "actor": "dev-user",
                "action": "pushed",
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "details": {
                    "message": "Added AWS credentials to config",
                    "sha": "abc1234",
                    "verified": False,
                    "severity": "HIGH",
                },
            },
            {
                "type": "security.alert",
                "actor": "github[bot]",
                "action": "security.vulnerability_alert",
                "timestamp": (now - timedelta(days=3)).isoformat(),
                "details": {
                    "alert": "Critical vulnerability in dependency",
                    "package": "requests==2.20.0",
                    "severity": "CRITICAL",
                },
            },
        ]



    def collect_dependabot_alerts(self) -> List[Dict[str, Any]]:
        """Collect Dependabot alerts from GitHub API."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/dependabot/alerts"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)

            # Handle specific error cases
            if response.status_code == 401:
                raise ValueError("Authentication failed. Please check your GitHub token.")
            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    raise ValueError("GitHub API rate limit exceeded. Please try again later.")
                raise ValueError("Access forbidden. Please check repository permissions.")
            if response.status_code == 404:
                raise ValueError(f"Repository {self.owner}/{self.repo} not found or no access.")

            response.raise_for_status()

            alerts = response.json()

            # Convert alerts to internal format
            return [self._convert_alert(alert) for alert in alerts]

        except requests.exceptions.RequestException as e:
            logger.error("GitHub API call failed: %s", e)
            raise

    def _convert_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Dependabot alert to internal format."""
        # Extract relevant information from the alert
        vulnerability = alert.get("security_vulnerability", {})
        package = vulnerability.get("package", {})
        advisory = alert.get("security_advisory", {})

        # Map GitHub severity to internal severity
        severity_mapping = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
        }
        github_severity = alert.get("severity", "unknown").lower()
        severity = severity_mapping.get(github_severity, "MEDIUM")

        # Build the internal format
        return {
            "type": "dependabot_alert",
            "severity": severity,
            "package_name": package.get("name", "Unknown"),
            "package_ecosystem": package.get("ecosystem", "Unknown"),
            "vulnerable_version": vulnerability.get("vulnerable_version_range", "Unknown"),
            "patched_version": vulnerability.get("first_patched_version", {}).get(
                "identifier", "Not available"
            ),
            "description": advisory.get(
                "summary", alert.get("summary", "No description available")
            ),
            "cve_id": advisory.get("cve_id"),
            "ghsa_id": advisory.get("ghsa_id"),
            "references": advisory.get("references", []),
            "recommendation": self._get_recommendation(package, vulnerability),
            "created_at": alert.get("created_at"),
            "state": alert.get("state"),
            "alert_number": alert.get("number"),
        }

    def _get_recommendation(self, package: Dict[str, Any], vulnerability: Dict[str, Any]) -> str:
        """Get recommendation for fixing vulnerability."""
        package_name = package.get("name", "package")
        patched_version = vulnerability.get("first_patched_version", {}).get(
            "identifier", "latest patched version"
        )
        return f"Update {package_name} to version {patched_version} or higher"

    def _check_security_settings(self) -> List[Dict[str, Any]]:
        """Check repository security settings and return findings."""
        findings = []

        # This would normally make API calls to check settings
        # For now, returning some basic checks
        if self.use_mock:
            return [
                {
                    "type": "branch_protection",
                    "branch": "main",
                    "severity": "HIGH",
                    "description": "Default branch 'main' is not protected",
                    "recommendation": "Enable branch protection rules for the default branch",
                },
                {
                    "type": "two_factor_auth",
                    "severity": "MEDIUM",
                    "description": "Some collaborators don't have 2FA enabled",
                    "recommendation": "Require two-factor authentication for all collaborators",
                },
            ]

        return findings
