"""Google Cloud Platform provider implementation."""

import logging
from typing import Any, Dict, List

from .base import CloudProvider

logger = logging.getLogger(__name__)


class GCPProvider(CloudProvider):
    """Google Cloud Platform provider implementation."""

    def __init__(self, project_id: str = None, use_mock: bool = False, **kwargs):
        """Initialize GCP provider.

        Args:
            project_id: GCP project ID to audit
            use_mock: Force use of mock data instead of real API calls
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        self.project_id = project_id or "sample-project"
        self.use_mock = use_mock

    def get_name(self) -> str:
        """Return the name of the cloud provider."""
        return "gcp"

    def get_iam_policies(self) -> Dict[str, Any]:
        """Retrieve IAM policies from GCP."""
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GCP setup
        return self._get_mock_iam_policies()

    def _get_mock_iam_policies(self) -> Dict[str, Any]:
        """Get mock IAM policies for fallback."""
        return {
            "project": self.project_id,
            "bindings": [
                {
                    "role": "roles/owner",
                    "members": [
                        "user:admin@example.com",
                        "serviceAccount:prod-sa@example.iam.gserviceaccount.com",
                    ],
                },
                {
                    "role": "roles/editor",
                    "members": ["user:developer@example.com"],
                },
                {
                    "role": "roles/viewer",
                    "members": ["user:readonly@example.com"],
                },
            ],
        }

    def get_security_findings(self) -> List[Dict[str, Any]]:
        """Retrieve Security Command Center findings."""
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GCP setup
        return self._get_mock_security_findings()

    def _get_mock_security_findings(self) -> List[Dict[str, Any]]:
        """Get mock security findings for fallback."""
        return [
            {
                "name": f"projects/{self.project_id}/findings/finding1",
                "category": "PUBLIC_BUCKET",
                "resourceName": f"//storage.googleapis.com/{self.project_id}-public",
                "severity": "HIGH",
                "finding": {
                    "description": "Storage bucket is publicly accessible",
                    "recommendation": "Remove public access from the bucket",
                },
            },
            {
                "name": f"projects/{self.project_id}/findings/finding2",
                "category": "OVER_PRIVILEGED_ACCOUNT",
                "resourceName": (
                    f"//iam.googleapis.com/projects/{self.project_id}/"
                    "serviceAccounts/prod-sa@example.iam.gserviceaccount.com"
                ),
                "severity": "MEDIUM",
                "finding": {
                    "description": "Service account has excessive permissions",
                    "recommendation": "Apply principle of least privilege",
                },
            },
        ]

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Retrieve Cloud Audit Logs."""
        # For hackathon demo, use mock data primarily
        # Real API implementation requires proper GCP setup
        return self._get_mock_audit_logs()

    def _get_mock_audit_logs(self) -> List[Dict[str, Any]]:
        """Get mock audit logs for fallback."""
        return [
            {
                "insertId": "log1",
                "resource": {"type": "project", "labels": {"project_id": self.project_id}},
                "protoPayload": {
                    "methodName": "SetIamPolicy",
                    "authenticationInfo": {"principalEmail": "admin@example.com"},
                    "requestMetadata": {"callerIp": "192.168.1.1"},
                },
                "severity": "INFO",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "insertId": "log2",
                "resource": {
                    "type": "gcs_bucket",
                    "labels": {"bucket_name": f"{self.project_id}-public"},
                },
                "protoPayload": {
                    "methodName": "storage.buckets.setIamPolicy",
                    "authenticationInfo": {"principalEmail": "developer@example.com"},
                },
                "severity": "WARNING",
                "timestamp": "2024-01-01T11:00:00Z",
            },
        ]
