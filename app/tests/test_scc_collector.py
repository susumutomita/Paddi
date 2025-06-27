#!/usr/bin/env python3
"""
Unit tests for Google Cloud Security Command Center collector.
"""

import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.api_core import exceptions as gcp_exceptions
from google.cloud import securitycenter_v1

from app.collector.scc_collector import SCCCollector


class TestSCCCollector:
    """Test cases for SCCCollector class."""

    def test_init_with_organization_id(self):
        """Test initialization with explicit organization ID."""
        collector = SCCCollector(organization_id="test-org-123")
        assert collector.organization_id == "test-org-123"
        assert collector._client is None

    def test_init_with_env_variable(self):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"GCP_ORGANIZATION_ID": "env-org-456"}):
            collector = SCCCollector()
            assert collector.organization_id == "env-org-456"

    def test_client_lazy_initialization(self):
        """Test that client is initialized only when accessed."""
        collector = SCCCollector(organization_id="test-org")
        assert collector._client is None

        with patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient") as mock_client:
            client = collector.client
            assert client is not None
            mock_client.assert_called_once()

    def test_collect_findings_with_mock(self):
        """Test collecting findings with mock data."""
        collector = SCCCollector(organization_id="test-org")
        findings = collector.collect_findings(use_mock=True)

        assert isinstance(findings, list)
        assert len(findings) == 4
        assert all("name" in f for f in findings)
        assert all("category" in f for f in findings)
        assert all("severity" in f for f in findings)

    def test_collect_findings_without_organization_id(self):
        """Test that collect_findings raises ValueError without organization ID."""
        collector = SCCCollector()
        with pytest.raises(ValueError, match="Organization ID is required"):
            collector.collect_findings(use_mock=False)

    @patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient")
    def test_collect_findings_success(self, mock_client_class):
        """Test successful collection of findings from all sources."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create mock findings
        mock_finding = Mock(spec=securitycenter_v1.Finding)
        mock_finding.name = "organizations/123/sources/456/findings/test-finding"
        mock_finding.category = "TEST_CATEGORY"
        mock_finding.resource_name = "//test.googleapis.com/test-resource"
        mock_finding.state = securitycenter_v1.Finding.State.ACTIVE
        mock_finding.severity = securitycenter_v1.Finding.Severity.HIGH
        mock_finding.finding_class = securitycenter_v1.Finding.FindingClass.VULNERABILITY
        mock_finding.create_time = Mock(isoformat=lambda: "2023-01-01T00:00:00Z")
        mock_finding.event_time = Mock(isoformat=lambda: "2023-01-01T00:00:00Z")
        mock_finding.description = "Test description"
        mock_finding.external_uri = "https://example.com"
        mock_finding.source_properties = {"recommendation": "Test recommendation"}
        mock_finding.resource_properties = {"resource_type": "test.Type"}
        mock_finding.indicator = Mock(domains=[], ip_addresses=[])

        # Create mock response
        mock_response = Mock()
        mock_response.finding = mock_finding

        # Setup list_findings to return mock findings
        mock_client.list_findings.return_value = [mock_response]

        collector = SCCCollector(organization_id="test-org-123")
        findings = collector.collect_findings(use_mock=False)

        assert isinstance(findings, list)
        assert len(findings) == 3  # SHA + WSS + Container findings
        assert mock_client.list_findings.call_count == 3

    @patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient")
    def test_collect_findings_permission_denied(self, mock_client_class):
        """Test handling of permission denied error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_findings.side_effect = gcp_exceptions.PermissionDenied("Access denied")

        collector = SCCCollector(organization_id="test-org-123")
        with pytest.raises(gcp_exceptions.PermissionDenied):
            collector.collect_findings(use_mock=False)

    @patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient")
    def test_collect_findings_not_found(self, mock_client_class):
        """Test handling of organization not found error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_findings.side_effect = gcp_exceptions.NotFound("Organization not found")

        collector = SCCCollector(organization_id="test-org-123")
        with pytest.raises(gcp_exceptions.NotFound):
            collector.collect_findings(use_mock=False)

    @patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient")
    def test_retry_on_service_unavailable(self, mock_client_class):
        """Test retry logic for service unavailable errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First two calls fail, third succeeds
        mock_client.list_findings.side_effect = [
            gcp_exceptions.ServiceUnavailable("Service unavailable"),
            gcp_exceptions.ServiceUnavailable("Service unavailable"),
            [],  # Success on third attempt
        ]

        collector = SCCCollector(organization_id="test-org-123")
        findings = collector.collect_findings(use_mock=False)

        assert isinstance(findings, list)
        assert mock_client.list_findings.call_count == 3

    def test_convert_finding_success(self):
        """Test successful conversion of finding to internal format."""
        collector = SCCCollector(organization_id="test-org")

        # Create mock finding
        mock_finding = Mock(spec=securitycenter_v1.Finding)
        mock_finding.name = "test-finding"
        mock_finding.category = "TEST_CATEGORY"
        mock_finding.resource_name = "//test.googleapis.com/test-resource"
        mock_finding.state = Mock(name="ACTIVE")
        mock_finding.severity = securitycenter_v1.Finding.Severity.HIGH
        mock_finding.finding_class = Mock(name="VULNERABILITY")
        mock_finding.create_time = Mock(isoformat=lambda: "2023-01-01T00:00:00Z")
        mock_finding.event_time = Mock(isoformat=lambda: "2023-01-01T00:00:00Z")
        mock_finding.description = "Test description"
        mock_finding.external_uri = "https://example.com"
        mock_finding.source_properties = {"recommendation": "Test recommendation"}
        mock_finding.resource_properties = {"resource_type": "test.Type"}
        mock_finding.indicator = Mock(domains=["example.com"], ip_addresses=["1.2.3.4"])

        result = collector._convert_finding(mock_finding, "SHA")

        assert result is not None
        assert result["name"] == "test-finding"
        assert result["category"] == "TEST_CATEGORY"
        assert result["severity"] == "HIGH"
        assert result["source_type"] == "SHA"
        assert result["indicator"]["domains"] == ["example.com"]
        assert result["indicator"]["ip_addresses"] == ["1.2.3.4"]

    def test_convert_finding_error_handling(self):
        """Test error handling in finding conversion."""
        collector = SCCCollector(organization_id="test-org")

        # Create finding with missing attributes
        mock_finding = Mock()
        mock_finding.name = "test-finding"
        # Missing other required attributes

        result = collector._convert_finding(mock_finding, "SHA")
        assert result is None  # Should return None on error

    def test_get_time_filter(self):
        """Test time filter generation."""
        collector = SCCCollector(organization_id="test-org")
        time_filter = collector._get_time_filter(days=7)

        assert isinstance(time_filter, str)
        assert "event_time >=" in time_filter
        assert "T" in time_filter  # ISO format contains T

    def test_is_sha_finding(self):
        """Test SHA finding identification."""
        collector = SCCCollector(organization_id="test-org")

        # Test with source_id
        mock_finding = Mock()
        mock_finding.source_properties = {"source_id": "SECURITY_HEALTH_ANALYTICS"}
        assert collector._is_sha_finding(mock_finding) is True

        # Test with known category
        mock_finding.source_properties = {}
        mock_finding.category = "PUBLIC_BUCKET"
        assert collector._is_sha_finding(mock_finding) is True

        # Test with unknown category
        mock_finding.category = "UNKNOWN_CATEGORY"
        assert collector._is_sha_finding(mock_finding) is False

        # Test without source_properties
        mock_finding.source_properties = None
        assert collector._is_sha_finding(mock_finding) is False

    @patch("app.collector.scc_collector.securitycenter_v1.SecurityCenterClient")
    def test_get_sha_findings_with_invalid_filter(self, mock_client_class):
        """Test SHA findings collection with invalid filter fallback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First call with complex filter fails, second with simple filter succeeds
        mock_finding = Mock(spec=securitycenter_v1.Finding)
        mock_finding.name = "test-sha-finding"
        mock_finding.category = "OVERPRIVILEGED_SERVICE_ACCOUNT"
        mock_finding.resource_name = "//iam.googleapis.com/test"
        mock_finding.state = securitycenter_v1.Finding.State.ACTIVE
        mock_finding.severity = securitycenter_v1.Finding.Severity.HIGH
        mock_finding.finding_class = securitycenter_v1.Finding.FindingClass.VULNERABILITY
        mock_finding.source_properties = {"source_id": "SECURITY_HEALTH_ANALYTICS"}
        mock_finding.resource_properties = {}
        mock_finding.create_time = None
        mock_finding.event_time = None
        mock_finding.description = ""
        mock_finding.external_uri = ""
        mock_finding.indicator = None

        mock_response = Mock()
        mock_response.finding = mock_finding

        mock_client.list_findings.side_effect = [
            gcp_exceptions.InvalidArgument("Invalid filter"),
            [mock_response],
        ]

        collector = SCCCollector(organization_id="test-org-123")
        findings = collector._get_sha_findings(mock_client, "organizations/test-org-123")

        assert len(findings) == 1
        assert mock_client.list_findings.call_count == 2

    def test_mock_data_structure(self):
        """Test that mock data has the expected structure."""
        collector = SCCCollector(organization_id="test-org")
        mock_data = collector._get_mock_scc_data()

        assert len(mock_data) == 4

        # Check SHA finding
        sha_finding = next(f for f in mock_data if f["source_type"] == "SHA")
        assert sha_finding["category"] in ["OVERPRIVILEGED_SERVICE_ACCOUNT", "PUBLIC_BUCKET"]
        assert sha_finding["severity"] in ["HIGH", "MEDIUM"]

        # Check WSS finding
        wss_finding = next(f for f in mock_data if f["source_type"] == "WSS")
        assert wss_finding["category"] == "XSS_SCRIPTING"
        assert "vulnerable_parameter" in wss_finding["source_properties"]

        # Check Container finding
        container_finding = next(f for f in mock_data if f["source_type"] == "CONTAINER")
        assert container_finding["category"] == "CONTAINER_VULNERABILITY"
        assert "cve_id" in container_finding["source_properties"]