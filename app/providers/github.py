"""GitHub provider implementation."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

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
        self.access_token = access_token
        self.owner = owner or "example-org"
        self.repo = repo or "example-repo"
        self.use_mock = use_mock or not access_token

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
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GitHub setup
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

    def collect_all(self) -> Dict[str, Any]:
        """Collect all GitHub repository data."""
        return {
            "provider": self.get_name(),
            "repository": f"{self.owner}/{self.repo}",
            "timestamp": self._get_timestamp(),
            "iam_policies": self.get_iam_policies(),
            "security_findings": self.get_security_findings(),
            "audit_logs": self.get_audit_logs(),
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import timezone

        return datetime.now(timezone.utc).isoformat()
