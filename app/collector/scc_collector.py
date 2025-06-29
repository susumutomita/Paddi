#!/usr/bin/env python3
"""
Google Cloud Security Command Center (SCC) Collector

This module provides integration with Google Cloud Security Command Center API
to collect vulnerability findings from various security scanners.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from google.api_core import exceptions as gcp_exceptions
from google.cloud import securitycenter_v1
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class SCCCollector:
    """Collector for Security Command Center findings."""

    def __init__(self, organization_id: Optional[str] = None):
        """
        Initialize SCCCollector with organization configuration.

        Args:
            organization_id: GCP organization ID. If not provided, attempts to
                           read from environment variable GCP_ORGANIZATION_ID.
        """
        self.organization_id = organization_id or os.getenv("GCP_ORGANIZATION_ID")
        self._client: Optional[securitycenter_v1.SecurityCenterClient] = None

    @property
    def client(self) -> securitycenter_v1.SecurityCenterClient:
        """Lazy initialization of Security Center client."""
        if self._client is None:
            self._client = securitycenter_v1.SecurityCenterClient()
        return self._client

    def collect_findings(self, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Collect Security Command Center findings.

        Args:
            use_mock: If True, returns mock data instead of making API calls.

        Returns:
            List of findings in internal format.

        Raises:
            ValueError: If organization_id is not set.
            Exception: If API calls fail after retries.
        """
        # Ensure use_mock is properly converted to boolean
        if isinstance(use_mock, str):
            use_mock = use_mock.lower() in ("true", "1", "yes", "on")
        else:
            use_mock = bool(use_mock)

        logger.info("Collecting SCC findings for organization: %s", self.organization_id)
        logger.info("use_mock: %s (type: %s)", use_mock, type(use_mock))
        if use_mock:
            logger.info("Using mock SCC data")
            return self._get_mock_scc_data()

        if not self.organization_id:
            raise ValueError(
                "Organization ID is required. Set GCP_ORGANIZATION_ID "
                "environment variable or pass organization_id to constructor."
            )

        try:
            logger.info("Collecting SCC findings for organization: %s", self.organization_id)
            parent = f"organizations/{self.organization_id}"

            findings = []

            # Collect findings from different sources
            logger.info("Collecting Security Health Analytics findings...")
            findings.extend(self._get_sha_findings(self.client, parent))

            logger.info("Collecting Web Security Scanner findings...")
            findings.extend(self._get_wss_findings(self.client, parent))

            logger.info("Collecting Container Analysis findings...")
            findings.extend(self._get_container_findings(self.client, parent))

            logger.info("Total findings collected: %d", len(findings))
            return findings

        except gcp_exceptions.PermissionDenied as e:
            logger.error("Permission denied accessing SCC API: %s", e)
            logger.error(
                "Ensure the service account has 'roles/securitycenter.adminViewer' permission"
            )
            raise
        except gcp_exceptions.NotFound as e:
            logger.error("Organization not found: %s", e)
            raise
        except Exception as e:
            logger.error("SCC API call failed: %s", e)
            raise

    @retry(
        retry=retry_if_exception_type(
            (gcp_exceptions.ServiceUnavailable, gcp_exceptions.DeadlineExceeded)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_sha_findings(
        self, client: securitycenter_v1.SecurityCenterClient, parent: str
    ) -> List[Dict[str, Any]]:
        """
        Get Security Health Analytics findings.

        Args:
            client: SCC client instance.
            parent: Parent resource (organization).

        Returns:
            List of converted findings.
        """
        findings = []

        # Set filter for active SHA findings from the last 7 days
        time_filter = self._get_time_filter(days=7)
        filter_str = (
            f'state="ACTIVE" AND '
            f'finding_class="VULNERABILITY" AND '
            f'source_properties.source_id="SECURITY_HEALTH_ANALYTICS" AND '
            f"{time_filter}"
        )

        request = securitycenter_v1.ListFindingsRequest(
            parent=f"{parent}/sources/-",
            filter=filter_str,
            page_size=100,
        )

        try:
            page_result = client.list_findings(request=request)
            for response in page_result:
                finding = response.finding
                converted = self._convert_finding(finding, "SHA")
                if converted:
                    findings.append(converted)
        except gcp_exceptions.InvalidArgument as e:
            logger.warning("Invalid filter for SHA findings: %s", e)
            # Fallback to simpler filter
            request.filter = 'state="ACTIVE" AND finding_class="VULNERABILITY"'
            page_result = client.list_findings(request=request)
            for response in page_result:
                finding = response.finding
                if self._is_sha_finding(finding):
                    converted = self._convert_finding(finding, "SHA")
                    if converted:
                        findings.append(converted)

        logger.info("Found %d SHA findings", len(findings))
        return findings

    @retry(
        retry=retry_if_exception_type(
            (gcp_exceptions.ServiceUnavailable, gcp_exceptions.DeadlineExceeded)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_wss_findings(
        self, client: securitycenter_v1.SecurityCenterClient, parent: str
    ) -> List[Dict[str, Any]]:
        """
        Get Web Security Scanner findings.

        Args:
            client: SCC client instance.
            parent: Parent resource (organization).

        Returns:
            List of converted findings.
        """
        findings = []

        # Set filter for WSS findings
        time_filter = self._get_time_filter(days=7)
        filter_str = (
            f'state="ACTIVE" AND '
            f'finding_class="VULNERABILITY" AND '
            f'source_properties.source_id="WEB_SECURITY_SCANNER" AND '
            f"{time_filter}"
        )

        request = securitycenter_v1.ListFindingsRequest(
            parent=f"{parent}/sources/-",
            filter=filter_str,
            page_size=100,
        )

        try:
            page_result = client.list_findings(request=request)
            for response in page_result:
                finding = response.finding
                converted = self._convert_finding(finding, "WSS")
                if converted:
                    findings.append(converted)
        except gcp_exceptions.InvalidArgument:
            logger.info("Web Security Scanner might not be enabled")

        logger.info("Found %d WSS findings", len(findings))
        return findings

    @retry(
        retry=retry_if_exception_type(
            (gcp_exceptions.ServiceUnavailable, gcp_exceptions.DeadlineExceeded)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_container_findings(
        self, client: securitycenter_v1.SecurityCenterClient, parent: str
    ) -> List[Dict[str, Any]]:
        """
        Get Container Analysis findings.

        Args:
            client: SCC client instance.
            parent: Parent resource (organization).

        Returns:
            List of converted findings.
        """
        findings = []

        # Set filter for Container Analysis findings
        time_filter = self._get_time_filter(days=7)
        filter_str = (
            f'state="ACTIVE" AND '
            f'finding_class="VULNERABILITY" AND '
            f'source_properties.source_id="CONTAINER_SCANNER" AND '
            f"{time_filter}"
        )

        request = securitycenter_v1.ListFindingsRequest(
            parent=f"{parent}/sources/-",
            filter=filter_str,
            page_size=100,
        )

        try:
            page_result = client.list_findings(request=request)
            for response in page_result:
                finding = response.finding
                converted = self._convert_finding(finding, "CONTAINER")
                if converted:
                    findings.append(converted)
        except gcp_exceptions.InvalidArgument:
            logger.info("Container Analysis might not be enabled")

        logger.info("Found %d Container Analysis findings", len(findings))
        return findings

    def _convert_finding(
        self, finding: securitycenter_v1.Finding, source_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert SCC API finding to internal format.

        Args:
            finding: SCC Finding object.
            source_type: Type of scanner (SHA, WSS, CONTAINER).

        Returns:
            Converted finding dict or None if conversion fails.
        """
        try:
            # Map SCC severity to internal format
            severity_map = {
                securitycenter_v1.Finding.Severity.CRITICAL: "CRITICAL",
                securitycenter_v1.Finding.Severity.HIGH: "HIGH",
                securitycenter_v1.Finding.Severity.MEDIUM: "MEDIUM",
                securitycenter_v1.Finding.Severity.LOW: "LOW",
            }

            # Extract resource information
            resource_name = finding.resource_name
            resource_type = ""
            if finding.resource_properties:
                resource_type = finding.resource_properties.get("resource_type", "")

            # Build internal format
            converted = {
                "name": finding.name,
                "category": finding.category,
                "resource_name": resource_name,
                "resource_type": resource_type,
                "state": finding.state.name if finding.state else "ACTIVE",
                "severity": severity_map.get(finding.severity, "MEDIUM"),
                "finding_class": (
                    finding.finding_class.name if finding.finding_class else "VULNERABILITY"
                ),
                "source_type": source_type,
                "create_time": finding.create_time.isoformat() if finding.create_time else None,
                "event_time": finding.event_time.isoformat() if finding.event_time else None,
                "description": finding.description,
                "recommendation": (
                    finding.source_properties.get("recommendation", "")
                    if finding.source_properties
                    else ""
                ),
                "external_uri": finding.external_uri,
                "indicator": {
                    "domains": list(finding.indicator.domains) if finding.indicator else [],
                    "ip_addresses": (
                        list(finding.indicator.ip_addresses) if finding.indicator else []
                    ),
                },
            }

            # Add source-specific properties
            if finding.source_properties:
                converted["source_properties"] = dict(finding.source_properties)

            return converted

        except Exception as e:
            logger.error("Error converting finding: %s", e)
            return None

    def _get_time_filter(self, days: int = 7) -> str:
        """
        Generate time filter for findings query.

        Args:
            days: Number of days to look back.

        Returns:
            Time filter string for SCC API.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        return f'event_time >= "{start_time.isoformat()}"'

    def _is_sha_finding(self, finding: securitycenter_v1.Finding) -> bool:
        """
        Check if a finding is from Security Health Analytics.

        Args:
            finding: SCC Finding object.

        Returns:
            True if SHA finding, False otherwise.
        """
        # Check source_properties if available
        if finding.source_properties:
            source_id = finding.source_properties.get("source_id", "")
            if source_id == "SECURITY_HEALTH_ANALYTICS":
                return True

        # Check if category matches known SHA categories
        return finding.category in [
            "OVERPRIVILEGED_SERVICE_ACCOUNT",
            "PUBLIC_BUCKET",
            "FIREWALL_RULE_OPEN",
            "CRYPTO_KEY_PUBLIC_ACCESS",
            "LOG_NOT_ENCRYPTED",
            "DATASET_PUBLIC_ACCESS",
            "BUCKET_LOGGING_DISABLED",
        ]

    def _get_mock_scc_data(self) -> List[Dict[str, Any]]:
        """Return mock SCC findings for testing."""
        return [
            {
                "name": "organizations/123456/sources/789/findings/finding-1",
                "category": "OVERPRIVILEGED_SERVICE_ACCOUNT",
                "resource_name": (
                    "//iam.googleapis.com/projects/example-project/serviceAccounts/"
                    "over-privileged-sa@example-project.iam.gserviceaccount.com"
                ),
                "resource_type": "serviceAccount",
                "state": "ACTIVE",
                "severity": "HIGH",
                "finding_class": "VULNERABILITY",
                "source_type": "SHA",
                "create_time": datetime.now(timezone.utc).isoformat(),
                "event_time": datetime.now(timezone.utc).isoformat(),
                "description": (
                    "Service account has overly permissive permissions. "
                    "It has been granted roles/owner which provides full access to all resources."
                ),
                "recommendation": (
                    "Review the permissions granted to this service account and apply "
                    "the principle of least privilege. Consider using predefined roles "
                    "or creating custom roles with only necessary permissions."
                ),
                "external_uri": "https://cloud.google.com/iam/docs/understanding-roles",
                "indicator": {
                    "domains": [],
                    "ip_addresses": [],
                },
                "source_properties": {
                    "source_id": "SECURITY_HEALTH_ANALYTICS",
                    "iam_bindings": ["roles/owner", "roles/editor"],
                },
            },
            {
                "name": "organizations/123456/sources/789/findings/finding-2",
                "category": "PUBLIC_BUCKET",
                "resource_name": "//storage.googleapis.com/example-public-bucket",
                "resource_type": "storage.bucket",
                "state": "ACTIVE",
                "severity": "MEDIUM",
                "finding_class": "MISCONFIGURATION",
                "source_type": "SHA",
                "create_time": datetime.now(timezone.utc).isoformat(),
                "event_time": datetime.now(timezone.utc).isoformat(),
                "description": (
                    "Cloud Storage bucket is publicly accessible. "
                    "Any user on the internet can list and download objects."
                ),
                "recommendation": (
                    "Remove public access from the bucket unless explicitly required. "
                    "Use IAM conditions and uniform bucket-level access for better control."
                ),
                "external_uri": "https://cloud.google.com/storage/docs/access-control",
                "indicator": {
                    "domains": [],
                    "ip_addresses": [],
                },
                "source_properties": {
                    "source_id": "SECURITY_HEALTH_ANALYTICS",
                    "public_access": "allUsers",
                },
            },
            {
                "name": "organizations/123456/sources/789/findings/finding-3",
                "category": "XSS_SCRIPTING",
                "resource_name": "//appengine.googleapis.com/apps/example-project/services/default",
                "resource_type": "appengine.Service",
                "state": "ACTIVE",
                "severity": "HIGH",
                "finding_class": "VULNERABILITY",
                "source_type": "WSS",
                "create_time": datetime.now(timezone.utc).isoformat(),
                "event_time": datetime.now(timezone.utc).isoformat(),
                "description": (
                    "Cross-site scripting vulnerability detected in web application. "
                    "User input is not properly sanitized before being rendered."
                ),
                "recommendation": (
                    "Implement proper input validation and output encoding. "
                    "Use Content Security Policy (CSP) headers to mitigate XSS attacks."
                ),
                "external_uri": "https://owasp.org/www-community/attacks/xss/",
                "indicator": {
                    "domains": ["example-app.appspot.com"],
                    "ip_addresses": [],
                },
                "source_properties": {
                    "source_id": "WEB_SECURITY_SCANNER",
                    "vulnerable_parameter": "search",
                    "attack_vector": "<script>alert('XSS')</script>",
                },
            },
            {
                "name": "organizations/123456/sources/789/findings/finding-4",
                "category": "CONTAINER_VULNERABILITY",
                "resource_name": (
                    "//container.googleapis.com/projects/example-project/"
                    "zones/us-central1-a/clusters/prod-cluster"
                ),
                "resource_type": "container.Cluster",
                "state": "ACTIVE",
                "severity": "CRITICAL",
                "finding_class": "VULNERABILITY",
                "source_type": "CONTAINER",
                "create_time": datetime.now(timezone.utc).isoformat(),
                "event_time": datetime.now(timezone.utc).isoformat(),
                "description": (
                    "Critical vulnerability CVE-2023-12345 found in container image. "
                    "This vulnerability allows remote code execution."
                ),
                "recommendation": (
                    "Update the base image to the latest patched version. "
                    "Implement vulnerability scanning in your CI/CD pipeline."
                ),
                "external_uri": "https://nvd.nist.gov/vuln/detail/CVE-2023-12345",
                "indicator": {
                    "domains": [],
                    "ip_addresses": [],
                },
                "source_properties": {
                    "source_id": "CONTAINER_SCANNER",
                    "image_uri": "gcr.io/example-project/app:v1.2.3",
                    "cve_id": "CVE-2023-12345",
                    "package_name": "openssl",
                    "package_version": "1.1.1",
                },
            },
        ]
