"""Agent C: Security Audit Report Generator.

This agent reads the explained security findings from Agent B and generates
human-readable audit reports in Markdown and HTML formats.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire
from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Data class representing a security finding."""

    title: str
    severity: str
    explanation: str
    recommendation: str


@dataclass
class AuditReport:
    """Data class representing the complete audit report."""

    findings: List[SecurityFinding]
    project_name: str
    audit_date: str
    total_findings: int
    severity_counts: Dict[str, int]


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate report content."""
        pass


class MarkdownGenerator(ReportGenerator):
    """Generates Markdown reports."""

    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate Markdown report content."""
        if template_path:
            return self._generate_from_template(report, template_path)
        return self._generate_default(report)

    def _generate_default(self, report: AuditReport) -> str:
        """Generate default Markdown report."""
        lines = [
            f"# Security Audit Report - {report.project_name}",
            "",
            f"**Audit Date:** {report.audit_date}",
            f"**Total Findings:** {report.total_findings}",
            "",
            "## Executive Summary",
            "",
            f"This security audit identified {report.total_findings} findings across your GCP infrastructure.",
            "",
            "### Severity Breakdown",
            "",
        ]

        for severity, count in sorted(report.severity_counts.items()):
            lines.append(f"- **{severity}**: {count} findings")

        lines.extend(["", "## Detailed Findings", ""])

        for i, finding in enumerate(report.findings, 1):
            lines.extend(
                [
                    f"### {i}. {finding.title}",
                    "",
                    f"**Severity:** {finding.severity}",
                    "",
                    f"**Explanation:** {finding.explanation}",
                    "",
                    f"**Recommendation:** {finding.recommendation}",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_from_template(self, report: AuditReport, template_path: Path) -> str:
        """Generate Markdown report from template."""
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(),
        )
        template = env.get_template(template_path.name)
        return template.render(report=report)


class HTMLGenerator(ReportGenerator):
    """Generates HTML reports."""

    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate HTML report content."""
        if template_path:
            return self._generate_from_template(report, template_path)
        return self._generate_default(report)

    def _generate_default(self, report: AuditReport) -> str:
        """Generate default HTML report with styling."""
        severity_colors = {
            "CRITICAL": "#D32F2F",
            "HIGH": "#F44336",
            "MEDIUM": "#FF9800",
            "LOW": "#FFC107",
            "INFO": "#2196F3",
        }

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Audit Report - {report.project_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #202124;
            margin-top: 30px;
        }}
        h3 {{
            color: #5f6368;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }}
        .finding {{
            background-color: #f8f9fa;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #e0e0e0;
        }}
        .finding-critical {{ border-left-color: #D32F2F; }}
        .finding-high {{ border-left-color: #F44336; }}
        .finding-medium {{ border-left-color: #FF9800; }}
        .finding-low {{ border-left-color: #FFC107; }}
        .finding-info {{ border-left-color: #2196F3; }}
        .recommendation {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .summary-card h4 {{
            margin: 0;
            color: #5f6368;
        }}
        .summary-card .count {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Security Audit Report - {report.project_name}</h1>
        
        <div class="metadata">
            <strong>Audit Date:</strong> {report.audit_date}<br>
            <strong>Total Findings:</strong> {report.total_findings}
        </div>
        
        <h2>Executive Summary</h2>
        <p>This security audit identified {report.total_findings} findings across your GCP infrastructure.</p>
        
        <h3>Severity Breakdown</h3>
        <div class="summary-grid">
"""

        for severity, count in sorted(report.severity_counts.items()):
            color = severity_colors.get(severity, "#9E9E9E")
            html += f"""
            <div class="summary-card">
                <h4>{severity}</h4>
                <div class="count" style="color: {color};">{count}</div>
            </div>
"""

        html += """
        </div>
        
        <h2>Detailed Findings</h2>
"""

        for i, finding in enumerate(report.findings, 1):
            severity_class = f"finding-{finding.severity.lower()}"
            badge_color = severity_colors.get(finding.severity, "#9E9E9E")
            html += f"""
        <div class="finding {severity_class}">
            <h3>{i}. {finding.title}</h3>
            <p><span class="severity-badge" style="background-color: {badge_color};">{finding.severity}</span></p>
            <p><strong>Explanation:</strong> {finding.explanation}</p>
            <div class="recommendation">
                <strong>Recommendation:</strong> {finding.recommendation}
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>"""
        return html

    def _generate_from_template(self, report: AuditReport, template_path: Path) -> str:
        """Generate HTML report from template."""
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_path.name)
        return template.render(report=report)


class ReportService:
    """Service class for generating reports."""

    def __init__(
        self,
        input_dir: Path = Path("data"),
        output_dir: Path = Path("output"),
        template_dir: Optional[Path] = None,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.output_dir.mkdir(exist_ok=True)

    def load_findings(self) -> List[Dict[str, Any]]:
        """Load security findings from explained.json."""
        explained_file = self.input_dir / "explained.json"
        if not explained_file.exists():
            logger.error(f"Input file not found: {explained_file}")
            return []

        with open(explained_file, "r") as f:
            return json.load(f)

    def load_metadata(self) -> Dict[str, Any]:
        """Load project metadata from collected.json."""
        collected_file = self.input_dir / "collected.json"
        if not collected_file.exists():
            logger.warning(f"Metadata file not found: {collected_file}")
            return {"project_id": "unknown-project"}

        with open(collected_file, "r") as f:
            data = json.load(f)
            return data.get("metadata", {"project_id": "unknown-project"})

    def create_report(self, findings_data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> AuditReport:
        """Create AuditReport from raw data."""
        findings = [
            SecurityFinding(
                title=f.get("title", "Unknown Issue"),
                severity=f.get("severity", "INFO"),
                explanation=f.get("explanation", "No explanation provided"),
                recommendation=f.get("recommendation", "No recommendation provided"),
            )
            for f in findings_data
        ]

        severity_counts = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

        return AuditReport(
            findings=findings,
            project_name=metadata.get("project_id", "Unknown Project"),
            audit_date=datetime.now().strftime("%Y-%m-%d"),
            total_findings=len(findings),
            severity_counts=severity_counts,
        )

    def generate_reports(self):
        """Generate both Markdown and HTML reports."""
        findings_data = self.load_findings()
        if not findings_data:
            logger.warning("No findings to report")
            return

        metadata = self.load_metadata()
        report = self.create_report(findings_data, metadata)

        # Generate Markdown report
        md_generator = MarkdownGenerator()
        md_template = None
        if self.template_dir:
            md_template_path = self.template_dir / "report.md.j2"
            if md_template_path.exists():
                md_template = md_template_path

        md_content = md_generator.generate(report, md_template)
        md_output = self.output_dir / "audit.md"
        with open(md_output, "w") as f:
            f.write(md_content)
        logger.info(f"Markdown report generated: {md_output}")

        # Generate HTML report
        html_generator = HTMLGenerator()
        html_template = None
        if self.template_dir:
            html_template_path = self.template_dir / "report.html.j2"
            if html_template_path.exists():
                html_template = html_template_path

        html_content = html_generator.generate(report, html_template)
        html_output = self.output_dir / "audit.html"
        with open(html_output, "w") as f:
            f.write(html_content)
        logger.info(f"HTML report generated: {html_output}")


def main(
    input_dir: str = "data",
    output_dir: str = "output",
    template_dir: Optional[str] = None,
):
    """Generate security audit reports from explained findings.

    Args:
        input_dir: Directory containing explained.json
        output_dir: Directory to save generated reports
        template_dir: Optional directory containing custom templates
    """
    service = ReportService(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        template_dir=Path(template_dir) if template_dir else None,
    )
    service.generate_reports()


if __name__ == "__main__":
    fire.Fire(main)