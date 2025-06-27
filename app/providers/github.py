"""GitHub provider implementation."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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
        self.access_token = access_token or os.getenv("GITHUB_TOKEN")
        self.owner = owner or os.getenv("GITHUB_OWNER", "example-org")
        self.repo = repo or os.getenv("GITHUB_REPO", "example-repo")
        self.use_mock = use_mock or not self.access_token
        self.headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
        } if self.access_token else {}

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
        if self.use_mock:
            return self._get_mock_security_findings()
        
        findings = []
        
        # Try to get Dependabot alerts
        try:
            dependabot_alerts = self.collect_dependabot_alerts()
            findings.extend(dependabot_alerts)
        except Exception as e:
            logger.error(f"Failed to collect Dependabot alerts: {e}")
            logger.info("Falling back to mock Dependabot data")
            findings.extend(self._get_mock_dependabot_alerts())
        
        # Add other security checks
        findings.extend(self._check_security_settings())
        
        return findings

    def collect_dependabot_alerts(self) -> List[Dict[str, Any]]:
        """Collect Dependabot alerts from GitHub API."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/dependabot/alerts"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            # Handle authentication errors
            if response.status_code == 401:
                logger.error("GitHub API authentication failed. Check your GITHUB_TOKEN.")
                raise Exception("Authentication failed")
            
            # Handle rate limiting
            if response.status_code == 403:
                logger.error("GitHub API rate limit exceeded or insufficient permissions.")
                raise Exception("Rate limit exceeded or insufficient permissions")
            
            # Handle repository access errors
            if response.status_code == 404:
                logger.error(f"Repository {self.owner}/{self.repo} not found or access denied.")
                raise Exception("Repository not found or access denied")
            
            response.raise_for_status()
            
            alerts = response.json()
            
            # Convert alerts to internal format
            return [self._convert_alert(alert) for alert in alerts]
            
        except Exception as e:
            logger.error(f"GitHub API call failed: {e}")
            raise
    
    def _convert_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Dependabot alert to internal format."""
        vulnerability = alert.get("security_vulnerability", {})
        advisory = alert.get("security_advisory", {})
        
        # Map GitHub severity to our internal severity levels
        severity_mapping = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "moderate": "MEDIUM",
            "medium": "MEDIUM",
            "low": "LOW",
        }
        
        severity = severity_mapping.get(
            advisory.get("severity", "medium").lower(), "MEDIUM"
        )
        
        # Extract CVE and GHSA IDs
        identifiers = advisory.get("identifiers", [])
        cve_id = next(
            (id_obj["value"] for id_obj in identifiers if id_obj["type"] == "CVE"),
            None
        )
        ghsa_id = advisory.get("ghsa_id")
        
        # Get patch information
        first_patched_version = vulnerability.get("first_patched_version")
        fix_version = (
            first_patched_version.get("identifier")
            if first_patched_version
            else "No fix available"
        )
        
        return {
            "type": "dependabot_alert",
            "severity": severity,
            "package_name": vulnerability.get("package", {}).get("name", "Unknown"),
            "package_ecosystem": vulnerability.get("package", {}).get("ecosystem", "Unknown"),
            "vulnerable_version": vulnerability.get("vulnerable_version_range", "Unknown"),
            "fixed_version": fix_version,
            "cve_id": cve_id,
            "ghsa_id": ghsa_id,
            "title": advisory.get("summary", "Vulnerability detected"),
            "description": advisory.get("description", "No description available"),
            "recommendation": f"Update to version {fix_version}" if fix_version != "No fix available" else "Review and mitigate the vulnerability",
            "created_at": alert.get("created_at"),
            "state": alert.get("state", "open"),
            "dismissed": alert.get("dismissed_at") is not None,
            "dismissed_reason": alert.get("dismissed_reason"),
        }
    
    def _get_mock_dependabot_alerts(self) -> List[Dict[str, Any]]:
        """Get mock Dependabot alerts for fallback."""
        return [
            {
                "type": "dependabot_alert",
                "severity": "CRITICAL",
                "package_name": "requests",
                "package_ecosystem": "pip",
                "vulnerable_version": "< 2.32.0",
                "fixed_version": "2.32.0",
                "cve_id": "CVE-2023-32681",
                "ghsa_id": "GHSA-j8r2-6x86-q33q",
                "title": "Unintended leak of Proxy-Authorization header",
                "description": "Requests versions before 2.32.0 may leak Proxy-Authorization header",
                "recommendation": "Update to version 2.32.0",
                "created_at": "2024-05-20T00:00:00Z",
                "state": "open",
                "dismissed": False,
                "dismissed_reason": None,
            },
            {
                "type": "dependabot_alert",
                "severity": "HIGH",
                "package_name": "pyyaml",
                "package_ecosystem": "pip",
                "vulnerable_version": "< 5.4",
                "fixed_version": "5.4",
                "cve_id": "CVE-2020-14343",
                "ghsa_id": "GHSA-8q59-q68h-6hfq",
                "title": "Arbitrary code execution via python/object/new",
                "description": "A vulnerability was discovered in PyYAML allowing arbitrary code execution",
                "recommendation": "Update to version 5.4",
                "created_at": "2024-05-15T00:00:00Z",
                "state": "open",
                "dismissed": False,
                "dismissed_reason": None,
            },
        ]
    
    def _check_security_settings(self) -> List[Dict[str, Any]]:
        """Check repository security settings."""
        # This would check branch protection, 2FA, etc.
        # For now, return basic security checks
        return [
            {
                "type": "security_settings",
                "severity": "MEDIUM",
                "description": "Repository security settings should be reviewed",
                "recommendation": "Enable all recommended security features in repository settings",
            },
        ]
    
    def _get_mock_security_findings(self) -> List[Dict[str, Any]]:
        """Get mock security findings for fallback."""
        findings = []
        findings.extend(self._get_mock_dependabot_alerts())
        findings.extend([
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
        ])
        return findings

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
