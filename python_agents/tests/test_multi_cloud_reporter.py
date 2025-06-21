"""Tests for multi-cloud reporter functionality."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from reporter.multi_cloud_reporter import (
    MultiCloudSecurityFinding,
    MultiCloudAuditReport,
    MultiCloudMarkdownGenerator,
    MultiCloudHTMLGenerator,
    MultiCloudReportService
)


class TestMultiCloudReporter:
    """Test multi-cloud report generation."""
    
    @pytest.fixture
    def multi_cloud_findings(self):
        """Create mock multi-cloud findings."""
        return [
            {
                "title": "GCP: Overly Permissive Owner Role",
                "severity": "HIGH",
                "explanation": "Multiple users have owner role",
                "recommendation": "Remove owner role from non-essential users",
                "provider": "gcp",
                "resource": "user:admin@example.com"
            },
            {
                "title": "AWS: Administrator Access Policy",
                "severity": "HIGH",
                "explanation": "User has AdministratorAccess policy",
                "recommendation": "Use least privilege principle",
                "provider": "aws",
                "resource": "arn:aws:iam::123456789012:user/admin"
            },
            {
                "title": "Azure: Global Administrator Assignment",
                "severity": "HIGH",
                "explanation": "User has Global Administrator role",
                "recommendation": "Limit administrative access",
                "provider": "azure",
                "resource": "admin@contoso.com"
            },
            {
                "title": "AWS: S3 Bucket Public Access",
                "severity": "MEDIUM",
                "explanation": "S3 bucket allows public read",
                "recommendation": "Restrict bucket access",
                "provider": "aws",
                "resource": "s3://public-bucket"
            }
        ]
    
    @pytest.fixture
    def legacy_findings(self):
        """Create mock legacy GCP findings."""
        return [
            {
                "title": "Overly Permissive Owner Role",
                "severity": "HIGH",
                "explanation": "Multiple users have owner role",
                "recommendation": "Remove owner role from non-essential users"
            },
            {
                "title": "Service Account with Editor Role",
                "severity": "MEDIUM",
                "explanation": "Service account has broad permissions",
                "recommendation": "Use more specific roles"
            }
        ]
    
    @pytest.fixture
    def multi_cloud_collected(self):
        """Create mock multi-cloud collected data."""
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "providers": {
                "gcp": {
                    "security": {
                        "compliance": {
                            "standards": {
                                "cis_gcp": {"score": 0.75}
                            }
                        }
                    }
                },
                "aws": {
                    "security": {
                        "compliance": {
                            "standards": {
                                "cis_aws": {"score": 0.82}
                            }
                        }
                    }
                },
                "azure": {
                    "security": {
                        "compliance": {
                            "standards": {
                                "cis_azure": {"score": 0.79}
                            }
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def report_service(self, tmp_path, multi_cloud_findings, multi_cloud_collected):
        """Create report service with test data."""
        # Save test data
        findings_file = tmp_path / "explained.json"
        with open(findings_file, "w") as f:
            json.dump(multi_cloud_findings, f)
        
        collected_file = tmp_path / "collected.json"
        with open(collected_file, "w") as f:
            json.dump(multi_cloud_collected, f)
        
        return MultiCloudReportService(
            findings_file=str(findings_file),
            collected_file=str(collected_file),
            output_dir=str(tmp_path / "output")
        )
    
    def test_create_multi_cloud_report(self, report_service, multi_cloud_findings, multi_cloud_collected):
        """Test creating multi-cloud audit report."""
        report = report_service.create_report(multi_cloud_findings, multi_cloud_collected)
        
        assert report.total_findings == 4
        assert len(report.providers) == 3
        assert set(report.providers) == {"aws", "azure", "gcp"}
        
        # Check severity counts
        assert report.severity_counts["HIGH"] == 3
        assert report.severity_counts["MEDIUM"] == 1
        
        # Check provider summary
        assert report.provider_summary["gcp"]["total"] == 1
        assert report.provider_summary["aws"]["total"] == 2
        assert report.provider_summary["azure"]["total"] == 1
        
        # Check compliance summary
        assert report.compliance_summary is not None
        assert "cis_gcp" in report.compliance_summary
    
    def test_create_legacy_report(self, report_service, legacy_findings):
        """Test backward compatibility with legacy findings."""
        # Override with legacy data
        with open(report_service.findings_file, "w") as f:
            json.dump(legacy_findings, f)
        
        # Clear collected data for legacy test
        with open(report_service.collected_file, "w") as f:
            json.dump({}, f)
        
        report = report_service.create_report(legacy_findings, {})
        
        assert report.total_findings == 2
        assert len(report.providers) == 1
        assert report.providers[0] == "gcp"  # Default to GCP for legacy
    
    def test_markdown_generation(self, report_service):
        """Test Markdown report generation."""
        markdown_path = report_service.generate_markdown(
            report_service.create_report(
                report_service.load_findings(),
                report_service.load_collected_data()
            )
        )
        
        assert markdown_path.exists()
        assert markdown_path.name == "audit.md"
        
        content = markdown_path.read_text()
        assert "Multi-Cloud Security Audit Report" in content
        assert "GCP Findings" in content
        assert "AWS Findings" in content
        assert "Azure Findings" in content
    
    def test_html_generation(self, report_service):
        """Test HTML report generation."""
        html_path = report_service.generate_html(
            report_service.create_report(
                report_service.load_findings(),
                report_service.load_collected_data()
            )
        )
        
        assert html_path.exists()
        assert html_path.name == "audit.html"
        
        content = html_path.read_text()
        assert "<title>Multi-Cloud Security Audit Report</title>" in content
        assert "GCP Findings" in content
        assert "AWS Findings" in content
        assert "Azure Findings" in content
    
    def test_generate_reports(self, report_service):
        """Test generating all report formats."""
        markdown_path, html_path = report_service.generate_reports()
        
        assert markdown_path.exists()
        assert html_path.exists()
    
    def test_markdown_generator_with_template(self, tmp_path):
        """Test Markdown generation with custom template."""
        # Create a simple template
        template_file = tmp_path / "test_template.md.j2"
        template_file.write_text("# Test Report\nTotal: {{ report.total_findings }}")
        
        generator = MultiCloudMarkdownGenerator()
        report = MultiCloudAuditReport(
            findings=[],
            audit_date=datetime.now().isoformat(),
            total_findings=5,
            severity_counts={},
            providers=["gcp"]
        )
        
        content = generator.generate(report, template_file)
        assert "Test Report" in content
        assert "Total: 5" in content
    
    def test_finding_dataclass(self):
        """Test MultiCloudSecurityFinding dataclass."""
        finding = MultiCloudSecurityFinding(
            title="Test Finding",
            severity="HIGH",
            explanation="Test explanation",
            recommendation="Test recommendation",
            provider="aws",
            resource="test-resource"
        )
        
        assert finding.title == "Test Finding"
        assert finding.provider == "aws"
        assert finding.resource == "test-resource"