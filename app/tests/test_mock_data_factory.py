"""Tests for mock data factory."""

import pytest
from app.explainer.mock_data_factory import MockDataFactory
from app.common.models import SecurityFinding


class TestMockDataFactory:
    """Tests for MockDataFactory."""

    def test_create_finding(self):
        """Test creating a single finding."""
        factory = MockDataFactory()
        
        finding = factory.create_finding(
            title="Test Finding",
            severity="HIGH",
            explanation="Test explanation",
            recommendation="Test recommendation"
        )
        
        assert isinstance(finding, SecurityFinding)
        assert finding.title == "Test Finding"
        assert finding.severity == "HIGH"
        assert finding.explanation == "Test explanation"
        assert finding.recommendation == "Test recommendation"

    def test_create_iam_findings(self):
        """Test creating IAM-specific findings."""
        factory = MockDataFactory()
        
        findings = factory.create_iam_findings()
        
        assert len(findings) > 0
        assert all(isinstance(f, SecurityFinding) for f in findings)
        assert all(f.severity in ["HIGH", "MEDIUM", "LOW"] for f in findings)

    def test_create_provider_iam_findings(self):
        """Test creating provider-specific IAM findings."""
        factory = MockDataFactory()
        
        aws_findings = factory.create_provider_iam_findings("aws")
        azure_findings = factory.create_provider_iam_findings("azure")
        gcp_findings = factory.create_provider_iam_findings("gcp")
        
        # Check that each provider returns findings
        assert len(aws_findings) > 0
        assert len(azure_findings) > 0
        assert len(gcp_findings) > 0
        
        # Check that findings are provider-specific
        assert any("AWS" in f.title or "IAM" in f.title for f in aws_findings)
        assert any("Azure" in f.title or "Owner" in f.title for f in azure_findings)
        assert any("roles/owner" in f.explanation for f in gcp_findings)

    def test_create_provider_security_findings(self):
        """Test creating provider-specific security findings."""
        factory = MockDataFactory()
        
        aws_findings = factory.create_provider_security_findings("aws")
        azure_findings = factory.create_provider_security_findings("azure")
        
        # Check that each provider returns findings
        assert len(aws_findings) > 0
        assert len(azure_findings) > 0
        
        # Check that findings are provider-specific
        assert any("S3" in f.title or "RDS" in f.title for f in aws_findings)
        assert any("Storage" in f.title or "SQL" in f.title for f in azure_findings)

    def test_create_scc_findings(self):
        """Test creating Security Command Center findings."""
        factory = MockDataFactory()
        
        findings = factory.create_scc_findings()
        
        assert len(findings) > 0
        assert all(isinstance(f, SecurityFinding) for f in findings)
        assert any("Service Account" in f.title for f in findings)

    def test_create_enhanced_findings(self):
        """Test creating enhanced findings with Japanese content."""
        factory = MockDataFactory()
        
        findings = factory.create_enhanced_findings()
        
        assert len(findings) > 0
        assert all(isinstance(f, SecurityFinding) for f in findings)
        # Check for Japanese content
        assert any("権限" in f.title or "権限" in f.explanation for f in findings)

    def test_unknown_provider(self):
        """Test handling of unknown provider."""
        factory = MockDataFactory()
        
        findings = factory.create_provider_iam_findings("unknown")
        assert findings == []
        
        findings = factory.create_provider_security_findings("unknown")
        assert findings == []