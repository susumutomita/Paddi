"""Unit tests for the Security Audit Report Generator."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reporter.agent_reporter import (
    AuditReport,
    HTMLGenerator,
    MarkdownGenerator,
    ReportService,
    SecurityFinding,
)


@pytest.fixture
def sample_finding():
    """Create a sample security finding."""
    return SecurityFinding(
        title="Overly Permissive IAM Role",
        severity="HIGH",
        explanation="Service account has owner role which grants excessive permissions",
        recommendation="Apply principle of least privilege and use specific roles",
    )


@pytest.fixture
def sample_findings():
    """Create sample security findings list."""
    return [
        SecurityFinding(
            title="Overly Permissive IAM Role",
            severity="HIGH",
            explanation="Service account has owner role",
            recommendation="Use specific roles instead",
        ),
        SecurityFinding(
            title="Public Storage Bucket",
            severity="CRITICAL",
            explanation="Storage bucket is publicly accessible",
            recommendation="Restrict bucket access to authorized users only",
        ),
        SecurityFinding(
            title="Weak Password Policy",
            severity="MEDIUM",
            explanation="Password policy does not enforce complexity",
            recommendation="Enable password complexity requirements",
        ),
    ]


@pytest.fixture
def sample_report(sample_findings):
    """Create a sample audit report."""
    severity_counts = {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 1}
    return AuditReport(
        findings=sample_findings,
        project_name="test-project-123",
        audit_date="2024-01-01",
        total_findings=3,
        severity_counts=severity_counts,
    )


class TestSecurityFinding:
    """Test SecurityFinding dataclass."""

    def test_security_finding_creation(self, sample_finding):
        """Test creating a security finding."""
        assert sample_finding.title == "Overly Permissive IAM Role"
        assert sample_finding.severity == "HIGH"
        assert "owner role" in sample_finding.explanation
        assert "least privilege" in sample_finding.recommendation


class TestAuditReport:
    """Test AuditReport dataclass."""

    def test_audit_report_creation(self, sample_report):
        """Test creating an audit report."""
        assert sample_report.project_name == "test-project-123"
        assert sample_report.audit_date == "2024-01-01"
        assert sample_report.total_findings == 3
        assert sample_report.severity_counts["CRITICAL"] == 1
        assert len(sample_report.findings) == 3


class TestMarkdownGenerator:
    """Test Markdown report generation."""

    def test_generate_default_markdown(self, sample_report):
        """Test generating default Markdown report."""
        generator = MarkdownGenerator()
        content = generator.generate(sample_report)

        assert "# Security Audit Report - test-project-123" in content
        assert "**Audit Date:** 2024-01-01" in content
        assert "**Total Findings:** 3" in content
        assert "## Executive Summary" in content
        assert "### Severity Breakdown" in content
        assert "- **CRITICAL**: 1 findings" in content
        assert "## Detailed Findings" in content
        assert "### 1. Overly Permissive IAM Role" in content
        assert "**Severity:** HIGH" in content

    def test_generate_markdown_with_template(self, sample_report, tmp_path):
        """Test generating Markdown report with custom template."""
        template_content = """# {{ report.project_name }} Report
Total: {{ report.total_findings }}
{% for finding in report.findings %}
- {{ finding.title }} ({{ finding.severity }})
{% endfor %}"""

        template_file = tmp_path / "custom.md.j2"
        template_file.write_text(template_content)

        generator = MarkdownGenerator()
        content = generator.generate(sample_report, template_file)

        assert "# test-project-123 Report" in content
        assert "Total: 3" in content
        assert "- Overly Permissive IAM Role (HIGH)" in content
        assert "- Public Storage Bucket (CRITICAL)" in content


class TestHTMLGenerator:
    """Test HTML report generation."""

    def test_generate_default_html(self, sample_report):
        """Test generating default HTML report."""
        generator = HTMLGenerator()
        content = generator.generate(sample_report)

        assert "<!DOCTYPE html>" in content
        assert "<title>Security Audit Report - test-project-123</title>" in content
        assert "Audit Date:</strong> 2024-01-01" in content
        assert "Total Findings:</strong> 3" in content
        assert '<div class="summary-card">' in content
        assert 'class="finding finding-high"' in content
        assert "Overly Permissive IAM Role" in content

    def test_generate_html_with_template(self, sample_report, tmp_path):
        """Test generating HTML report with custom template."""
        template_content = """<html>
<body>
<h1>{{ report.project_name }}</h1>
<ul>
{% for finding in report.findings %}
<li>{{ finding.title | e }}</li>
{% endfor %}
</ul>
</body>
</html>"""

        template_file = tmp_path / "custom.html.j2"
        template_file.write_text(template_content)

        generator = HTMLGenerator()
        content = generator.generate(sample_report, template_file)

        assert "<h1>test-project-123</h1>" in content
        assert "<li>Overly Permissive IAM Role</li>" in content
        assert "<li>Public Storage Bucket</li>" in content


class TestReportService:
    """Test ReportService functionality."""

    def test_init_creates_output_dir(self, tmp_path):
        """Test that init creates output directory."""
        output_dir = tmp_path / "output"
        service = ReportService(output_dir=output_dir)
        assert output_dir.exists()

    def test_load_findings_success(self, tmp_path):
        """Test loading findings from JSON file."""
        findings_data = [
            {
                "title": "Test Finding",
                "severity": "HIGH",
                "explanation": "Test explanation",
                "recommendation": "Test recommendation",
            }
        ]

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        explained_file = data_dir / "explained.json"
        explained_file.write_text(json.dumps(findings_data))

        service = ReportService(input_dir=data_dir)
        findings = service.load_findings()

        assert len(findings) == 1
        assert findings[0]["title"] == "Test Finding"

    def test_load_findings_file_not_found(self, tmp_path):
        """Test handling missing explained.json."""
        service = ReportService(input_dir=tmp_path)
        findings = service.load_findings()
        assert findings == []

    def test_load_metadata_success(self, tmp_path):
        """Test loading metadata from collected.json."""
        metadata = {"metadata": {"project_id": "test-project-456"}}

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        collected_file = data_dir / "collected.json"
        collected_file.write_text(json.dumps(metadata))

        service = ReportService(input_dir=data_dir)
        loaded_metadata = service.load_metadata()

        assert loaded_metadata["project_id"] == "test-project-456"

    def test_load_metadata_file_not_found(self, tmp_path):
        """Test handling missing collected.json."""
        service = ReportService(input_dir=tmp_path)
        metadata = service.load_metadata()
        assert metadata["project_id"] == "unknown-project"

    def test_create_report(self, tmp_path):
        """Test creating audit report from raw data."""
        findings_data = [
            {
                "title": "Finding 1",
                "severity": "HIGH",
                "explanation": "Explanation 1",
                "recommendation": "Recommendation 1",
            },
            {
                "title": "Finding 2",
                "severity": "HIGH",
                "explanation": "Explanation 2",
                "recommendation": "Recommendation 2",
            },
            {
                "title": "Finding 3",
                "severity": "LOW",
                "explanation": "Explanation 3",
                "recommendation": "Recommendation 3",
            },
        ]
        metadata = {"project_id": "test-project-789"}

        service = ReportService()
        report = service.create_report(findings_data, metadata)

        assert report.project_name == "test-project-789"
        assert report.total_findings == 3
        assert report.severity_counts["HIGH"] == 2
        assert report.severity_counts["LOW"] == 1
        assert len(report.findings) == 3

    def test_generate_reports_success(self, tmp_path):
        """Test generating both MD and HTML reports."""
        # Setup test data
        findings_data = [
            {
                "title": "Test Finding",
                "severity": "CRITICAL",
                "explanation": "Critical issue found",
                "recommendation": "Fix immediately",
            }
        ]
        metadata = {"metadata": {"project_id": "prod-project"}}

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        output_dir = tmp_path / "output"

        explained_file = data_dir / "explained.json"
        explained_file.write_text(json.dumps(findings_data))
        collected_file = data_dir / "collected.json"
        collected_file.write_text(json.dumps(metadata))

        # Generate reports
        service = ReportService(input_dir=data_dir, output_dir=output_dir)
        service.generate_reports()

        # Check outputs
        md_file = output_dir / "audit.md"
        html_file = output_dir / "audit.html"

        assert md_file.exists()
        assert html_file.exists()

        md_content = md_file.read_text()
        assert "Security Audit Report - prod-project" in md_content
        assert "Test Finding" in md_content
        assert "CRITICAL" in md_content

        html_content = html_file.read_text()
        assert "<title>Security Audit Report - prod-project</title>" in html_content
        assert "Test Finding" in html_content

    def test_generate_reports_no_findings(self, tmp_path):
        """Test handling case with no findings."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        output_dir = tmp_path / "output"

        service = ReportService(input_dir=data_dir, output_dir=output_dir)
        service.generate_reports()

        # Should not create any files
        assert not (output_dir / "audit.md").exists()
        assert not (output_dir / "audit.html").exists()

    def test_generate_reports_with_templates(self, tmp_path):
        """Test generating reports with custom templates."""
        # Setup test data
        findings_data = [{"title": "Test", "severity": "HIGH", "explanation": "Test", "recommendation": "Test"}]
        metadata = {"metadata": {"project_id": "test-proj"}}

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        output_dir = tmp_path / "output"
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create test data files
        (data_dir / "explained.json").write_text(json.dumps(findings_data))
        (data_dir / "collected.json").write_text(json.dumps(metadata))

        # Create custom templates
        md_template = template_dir / "report.md.j2"
        md_template.write_text("# Custom {{ report.project_name }}")

        # Generate reports
        service = ReportService(input_dir=data_dir, output_dir=output_dir, template_dir=template_dir)
        service.generate_reports()

        # Check custom template was used
        md_content = (output_dir / "audit.md").read_text()
        assert md_content == "# Custom test-proj"


class TestMainFunction:
    """Test the main entry point."""

    @patch("reporter.agent_reporter.ReportService")
    def test_main_with_defaults(self, mock_service_class):
        """Test main function with default arguments."""
        mock_instance = MagicMock()
        mock_service_class.return_value = mock_instance

        from reporter.agent_reporter import main

        main()

        mock_service_class.assert_called_once_with(
            input_dir=Path("data"),
            output_dir=Path("output"),
            template_dir=None,
        )
        mock_instance.generate_reports.assert_called_once()

    @patch("reporter.agent_reporter.ReportService")
    def test_main_with_custom_paths(self, mock_service_class):
        """Test main function with custom paths."""
        mock_instance = MagicMock()
        mock_service_class.return_value = mock_instance

        from reporter.agent_reporter import main

        main(input_dir="custom/input", output_dir="custom/output", template_dir="custom/templates")

        mock_service_class.assert_called_once_with(
            input_dir=Path("custom/input"),
            output_dir=Path("custom/output"),
            template_dir=Path("custom/templates"),
        )
        mock_instance.generate_reports.assert_called_once()