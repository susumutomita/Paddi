"""Tests for multi-cloud explainer functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from explainer.multi_cloud_explainer import (
    SecurityFinding,
    MultiCloudGeminiAnalyzer,
    MultiCloudSecurityExplainer
)


class TestMultiCloudExplainer:
    """Test multi-cloud security explainer."""
    
    @pytest.fixture
    def multi_cloud_data(self):
        """Create mock multi-cloud collected data."""
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "providers": {
                "gcp": {
                    "iam": {
                        "users": [
                            {"email": "admin@example.com", "roles": ["roles/owner"]}
                        ],
                        "policies": [
                            {
                                "resource": "projects/test-project",
                                "bindings": [
                                    {"role": "roles/owner", "members": ["user:admin@example.com"]}
                                ]
                            }
                        ]
                    },
                    "security": {
                        "findings": [
                            {
                                "id": "finding-gcp-1",
                                "severity": "HIGH",
                                "category": "OVERPRIVILEGED_SERVICE_ACCOUNT"
                            }
                        ],
                        "compliance": {
                            "standards": {
                                "cis_gcp": {"score": 0.75}
                            }
                        }
                    }
                },
                "aws": {
                    "iam": {
                        "users": [
                            {"arn": "arn:aws:iam::123456789012:user/admin", "policies": ["AdministratorAccess"]}
                        ]
                    },
                    "security": {
                        "findings": [
                            {
                                "id": "finding-aws-1",
                                "severity": "HIGH",
                                "title": "Admin user with full access"
                            }
                        ]
                    }
                },
                "azure": {
                    "iam": {
                        "users": [
                            {"user_principal_name": "admin@contoso.com", "roles": ["Global Administrator"]}
                        ]
                    },
                    "security": {
                        "findings": [
                            {
                                "id": "finding-azure-1",
                                "severity": "MEDIUM",
                                "name": "Storage account public access"
                            }
                        ]
                    }
                }
            }
        }
    
    @pytest.fixture
    def legacy_gcp_data(self):
        """Create mock legacy GCP data."""
        return {
            "project_id": "test-project",
            "timestamp": "2024-01-01T00:00:00Z",
            "iam_policies": {
                "bindings": [
                    {"role": "roles/owner", "members": ["user:admin@example.com"]}
                ]
            },
            "scc_findings": [
                {
                    "category": "OVERPRIVILEGED_SERVICE_ACCOUNT",
                    "severity": "HIGH"
                }
            ]
        }
    
    @pytest.fixture
    def analyzer(self):
        """Create multi-cloud analyzer with mock mode."""
        return MultiCloudGeminiAnalyzer(
            project_id="test-project",
            use_mock=True
        )
    
    @pytest.fixture
    def explainer(self, tmp_path, multi_cloud_data):
        """Create explainer instance with test data."""
        # Save test data
        collected_file = tmp_path / "collected.json"
        with open(collected_file, "w") as f:
            json.dump(multi_cloud_data, f)
        
        return MultiCloudSecurityExplainer(
            project_id="test-project",
            use_mock=True,
            input_file=str(collected_file),
            output_dir=str(tmp_path)
        )
    
    def test_analyze_multi_cloud_risks(self, analyzer, multi_cloud_data):
        """Test analyzing risks across multiple clouds."""
        findings = analyzer.analyze_multi_cloud_risks(multi_cloud_data)
        
        assert len(findings) > 0
        
        # Check findings have required fields
        for finding in findings:
            assert finding.title
            assert finding.severity in ["HIGH", "MEDIUM", "LOW"]
            assert finding.explanation
            assert finding.recommendation
            assert finding.provider in ["gcp", "aws", "azure"]
        
        # Check we have findings from multiple providers
        providers = set(f.provider for f in findings)
        assert len(providers) > 1
    
    def test_analyze_legacy_format(self, analyzer, legacy_gcp_data):
        """Test backward compatibility with legacy GCP format."""
        findings = analyzer.analyze_multi_cloud_risks(legacy_gcp_data)
        
        assert len(findings) > 0
        # Legacy format should only produce GCP findings
        assert all(f.provider == "gcp" for f in findings)
    
    def test_mock_findings(self, analyzer):
        """Test mock findings generation."""
        # Mock IAM findings
        iam_findings = analyzer._get_mock_iam_findings()
        assert len(iam_findings) == 3  # One per cloud provider
        assert any("GCP" in f.title for f in iam_findings)
        assert any("AWS" in f.title for f in iam_findings)
        assert any("Azure" in f.title for f in iam_findings)
        
        # Mock security findings
        security_findings = analyzer._get_mock_security_findings()
        assert len(security_findings) > 0
        
        # Mock compliance findings
        compliance_findings = analyzer._get_mock_compliance_findings()
        assert len(compliance_findings) > 0
    
    def test_explainer_workflow(self, explainer):
        """Test complete explainer workflow."""
        # Analyze
        findings = explainer.analyze()
        assert len(findings) > 0
        
        # Save findings
        output_path = explainer.save_findings(findings)
        assert output_path.exists()
        
        # Verify saved format
        with open(output_path) as f:
            saved_findings = json.load(f)
        
        assert len(saved_findings) == len(findings)
        for saved, original in zip(saved_findings, findings):
            assert saved["title"] == original.title
            assert saved["severity"] == original.severity
            assert saved["provider"] == original.provider
    
    def test_severity_distribution(self, analyzer, multi_cloud_data):
        """Test that findings have appropriate severity distribution."""
        findings = analyzer.analyze_multi_cloud_risks(multi_cloud_data)
        
        severities = [f.severity for f in findings]
        # Should have at least some HIGH severity findings
        assert "HIGH" in severities
    
    def test_finding_to_dict(self):
        """Test SecurityFinding to_dict method."""
        finding = SecurityFinding(
            title="Test Finding",
            severity="HIGH",
            explanation="Test explanation",
            recommendation="Test recommendation",
            provider="gcp",
            resource="test-resource"
        )
        
        finding_dict = finding.to_dict()
        assert finding_dict["title"] == "Test Finding"
        assert finding_dict["severity"] == "HIGH"
        assert finding_dict["provider"] == "gcp"
        assert finding_dict["resource"] == "test-resource"