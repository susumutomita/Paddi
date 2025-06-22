"""Google Cloud Platform provider implementation."""

import logging
from typing import Any, Dict, List, Optional

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
        self.project_id = project_id or "sample-project"
        self.use_mock = use_mock
        self._iam_service = None
        self._scc_service = None
        self._logging_service = None
        
        # Try to initialize real services if not using mock
        if not self.use_mock:
            try:
                from google.cloud import iam_admin_v1
                from google.cloud import securitycenter_v1
                from google.cloud import logging_v2
                from google.auth import default
                from google.auth.exceptions import DefaultCredentialsError
                
                # Get default credentials
                try:
                    credentials, project = default()
                    if not self.project_id or self.project_id == "sample-project":
                        self.project_id = project or self.project_id
                    
                    # Initialize services
                    self._iam_service = iam_admin_v1.IAMClient(credentials=credentials)
                    self._scc_service = securitycenter_v1.SecurityCenterClient(credentials=credentials)
                    self._logging_service = logging_v2.Client(project=self.project_id, credentials=credentials)
                    
                    logger.info(f"Successfully initialized GCP services for project: {self.project_id}")
                except DefaultCredentialsError:
                    logger.warning("No GCP credentials found. Falling back to mock data.")
                    self.use_mock = True
            except ImportError:
                logger.warning("GCP libraries not properly installed. Falling back to mock data.")
                self.use_mock = True
            except Exception as e:
                logger.warning(f"Failed to initialize GCP services: {e}. Falling back to mock data.")
                self.use_mock = True

    def get_name(self) -> str:
        """Return the name of the cloud provider."""
        return "gcp"

    def get_iam_policies(self) -> Dict[str, Any]:
        """Retrieve IAM policies from GCP."""
        if self.use_mock or not self._iam_service:
            return self._get_mock_iam_policies()
        
        try:
            from google.api_core.exceptions import GoogleAPIError
            from google.iam.v1 import policy_pb2
            
            # Get project IAM policy using the resource manager API
            resource = f"projects/{self.project_id}"
            
            # Use resource manager v3 API to get IAM policy
            from google.cloud import resourcemanager_v3
            
            rm_client = resourcemanager_v3.ProjectsClient()
            policy = rm_client.get_iam_policy(request={"resource": resource})
            
            # Convert policy to dict format
            bindings = []
            for binding in policy.bindings:
                bindings.append({
                    "role": binding.role,
                    "members": list(binding.members),
                })
            
            return {
                "project": self.project_id,
                "bindings": bindings,
                "etag": policy.etag.decode() if policy.etag else None,
                "version": policy.version,
            }
            
        except GoogleAPIError as e:
            logger.error(f"Failed to retrieve IAM policies: {e}")
            return self._get_mock_iam_policies()
        except Exception as e:
            logger.error(f"Unexpected error retrieving IAM policies: {e}")
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
        if self.use_mock or not self._scc_service:
            return self._get_mock_security_findings()
        
        try:
            from google.api_core.exceptions import GoogleAPIError
            from google.cloud import securitycenter_v1
            
            # Get organization ID (you might need to configure this)
            # For now, we'll use a pattern to search within the project
            parent = f"organizations/-/sources/-/findings"
            
            # Create filter for active findings in this project
            filter_str = f'resource_name : "projects/{self.project_id}" AND state="ACTIVE"'
            
            # List findings
            findings = []
            request = securitycenter_v1.ListFindingsRequest(
                parent=parent,
                filter=filter_str,
                page_size=100,
            )
            
            page_result = self._scc_service.list_findings(request=request)
            for response in page_result:
                finding = response.finding
                findings.append({
                    "name": finding.name,
                    "category": finding.category,
                    "resourceName": finding.resource_name,
                    "severity": finding.severity.name if finding.severity else "UNSPECIFIED",
                    "state": finding.state.name if finding.state else "UNSPECIFIED",
                    "finding": {
                        "description": finding.description or finding.category,
                        "recommendation": finding.next_steps or "Review and remediate the finding",
                        "source": finding.source_properties,
                    },
                    "create_time": finding.create_time.isoformat() if finding.create_time else None,
                })
            
            return findings if findings else self._get_mock_security_findings()
            
        except GoogleAPIError as e:
            logger.error(f"Failed to retrieve Security Command Center findings: {e}")
            return self._get_mock_security_findings()
        except Exception as e:
            logger.error(f"Unexpected error retrieving security findings: {e}")
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
        if self.use_mock or not self._logging_service:
            return self._get_mock_audit_logs()
        
        try:
            from google.api_core.exceptions import GoogleAPIError
            from datetime import datetime, timedelta
            
            # Create filter for audit logs
            # Look for IAM and security-related activities in the last 7 days
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)
            
            filter_str = (
                f'timestamp >= "{seven_days_ago.isoformat()}Z" '
                f'AND (protoPayload.methodName:"SetIamPolicy" '
                f'OR protoPayload.methodName:"storage.buckets.setIamPolicy" '
                f'OR protoPayload.methodName:"compute.instances.setIamPolicy" '
                f'OR protoPayload.methodName:"iam.serviceAccounts.create" '
                f'OR protoPayload.methodName:"iam.serviceAccounts.setIamPolicy") '
                f'AND severity >= "WARNING"'
            )
            
            # List entries
            logs = []
            entries = self._logging_service.list_entries(
                filter_=filter_str,
                page_size=100,
                order_by="timestamp desc",
            )
            
            for entry in entries:
                log_entry = {
                    "insertId": entry.insert_id,
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels),
                    },
                    "severity": entry.severity.name if entry.severity else "DEFAULT",
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                }
                
                # Extract proto payload details if available
                if hasattr(entry, 'proto_payload') and entry.proto_payload:
                    payload = entry.proto_payload
                    log_entry["protoPayload"] = {
                        "methodName": getattr(payload, 'method_name', None),
                        "authenticationInfo": {
                            "principalEmail": getattr(payload.authentication_info, 'principal_email', None)
                        } if hasattr(payload, 'authentication_info') else {},
                        "requestMetadata": {
                            "callerIp": getattr(payload.request_metadata, 'caller_ip', None)
                        } if hasattr(payload, 'request_metadata') else {},
                    }
                
                logs.append(log_entry)
            
            return logs[:50] if logs else self._get_mock_audit_logs()  # Limit to 50 most recent
            
        except GoogleAPIError as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return self._get_mock_audit_logs()
        except Exception as e:
            logger.error(f"Unexpected error retrieving audit logs: {e}")
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

    def collect_all(self) -> Dict[str, Any]:
        """Collect all GCP security data."""
        return {
            "provider": self.get_name(),
            "project_id": self.project_id,
            "iam_policies": self.get_iam_policies(),
            "security_findings": self.get_security_findings(),
            "audit_logs": self.get_audit_logs(),
        }
